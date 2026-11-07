#!/usr/bin/env python3
"""Check the public working tree using Git and Python's standard library only."""
import argparse
import ast
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

from namegen_safety import assert_safe_namegen_patch, assert_safe_namegen_translation


ROOT = Path(__file__).resolve().parents[2]
MANIFEST = "SHA256SUMS.txt"
MAX_FILE_BYTES = 50 * 1024 * 1024  # Project policy; large inventories stay local.
SECRET_PATTERNS = {
    "private key": rb"-----BEGIN (?:[A-Z]+ )*PRIVATE KEY-----",
    "GitHub token": rb"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})",
    "AWS access key": rb"(?:AKIA|ASIA)[A-Z0-9]{16}",
    "API token": rb"\bsk-[A-Za-z0-9_-]{32,}",
    "credential URL": rb"https?://[^/\s:@]+:[^/\s@]+@",
    "private workspace path": rb"/(?:workspace/scratch|mnt/data)/[A-Za-z0-9_-]+/",
    "Windows user path": rb"[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s\"]+[\\/]+",
}


def git(*args, input_data=None):
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], input=input_data,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
    ).stdout


def public_files():
    paths = git("ls-files", "--cached", "--others", "--exclude-standard", "-z")
    return sorted(set(paths.decode("utf-8").rstrip("\0").split("\0")) - {""})


def digest(data):
    return hashlib.sha256(data).hexdigest()


def check(write_checksums=False):
    names = public_files()
    errors = []
    hashes = {}
    parsed = 0
    python_files = 0
    total_bytes = 0
    largest = (0, "")
    folded = {}
    # --no-index also catches ignored paths accidentally added with git add -f.
    ignored = subprocess.run(
        ["git", "-C", str(ROOT), "check-ignore", "--no-index", "--stdin", "-z"],
        input=("\0".join(names) + "\0").encode("utf-8"),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )
    if ignored.returncode not in (0, 1):
        raise RuntimeError(ignored.stderr.decode("utf-8", errors="replace"))
    for name in ignored.stdout.decode("utf-8").split("\0"):
        if name:
            errors.append(f"Ignored local file is tracked: {name}")

    for name in names:
        parts = PurePosixPath(name).parts
        if name.startswith("/") or ".." in parts or any(c in name for c in "\r\n\\:"):
            errors.append(f"Unsafe repository path: {name!r}")
            continue
        if name.casefold() in folded:
            errors.append(f"Case collision: {folded[name.casefold()]} / {name}")
        folded[name.casefold()] = name
        path = ROOT / name
        if path.is_symlink() or not path.is_file():
            errors.append(f"Missing file or unsupported symlink: {name}")
            continue
        data = path.read_bytes()
        size = len(data)
        total_bytes += size
        largest = max(largest, (size, name))
        if size >= MAX_FILE_BYTES:
            errors.append(f"File exceeds the 50 MiB project limit: {name}")
        if name != MANIFEST:
            hashes[name] = digest(data)
        for label, pattern in SECRET_PATTERNS.items():
            if re.search(pattern, data):
                # Do not echo the matched secret into logs.
                errors.append(f"Possible {label}: {name}")
        try:
            if path.suffix in (".json", ".jsonl") or path.name == "_metadata":
                text = data.decode("utf-8-sig")
                if path.suffix == ".jsonl":
                    for line in text.splitlines():
                        if line.strip():
                            row = json.loads(line)
                            if name in {
                                "source/source/catalog.jsonl", "source/source/translated_catalog.jsonl",
                                "source/source/append_catalog.jsonl", "source/source/append_translated_catalog.jsonl",
                            }:
                                assert_safe_namegen_translation(row["asset"], row["path"])
                                for pointer in row.get("generated_paths", []):
                                    assert_safe_namegen_translation(row["asset"], pointer)
                else:
                    json.loads(text)
                parsed += 1
            elif name.startswith("mods/") and path.suffix == ".patch":
                patch = json.loads(data.decode("utf-8-sig"))
                if not isinstance(patch, list):
                    raise ValueError("Patch root must be an array")
                assert_safe_namegen_patch(name.removeprefix("mods/FU_Japanese/")[:-6], patch)
                parsed += 1
            elif path.suffix == ".py":
                ast.parse(data, filename=name)
                python_files += 1
        except (ValueError, SyntaxError) as exc:
            errors.append(f"Invalid syntax: {name} ({type(exc).__name__})")

    def read_json(name):
        if name not in hashes:
            raise ValueError(f"Required file is not public: {name}")
        return json.loads((ROOT / name).read_text(encoding="utf-8-sig"))

    expected_mod = read_json("source/reports/mod_sha256.json")
    prefix = "mods/FU_Japanese/"
    actual_mod = {name[len(prefix):]: sha for name, sha in hashes.items() if name.startswith(prefix)}
    for name in sorted(actual_mod.keys() | expected_mod.keys()):
        if actual_mod.get(name) != expected_mod.get(name):
            errors.append(f"MOD differs from validated release: {name}")
    retired = read_json("source/source/retired_character_name_assets.json")
    for asset in retired:
        if hashes.get(prefix + asset + ".patch") != digest(b"[]\n"):
            errors.append(f"Character-name patch must remain empty: {asset}")
    evidence = read_json("source/reports/test_summary_023.json")
    if not evidence.get("passed"):
        errors.append("Stored release checks are not passing")
    for row in evidence["reports"]:
        name = "source/reports/" + row["file"]
        if hashes.get(name) != row["sha256"] or not row["passed"]:
            errors.append(f"Release evidence changed: {name}")

    manifest_text = "".join(f"{sha}  {name}\n" for name, sha in sorted(hashes.items()))
    if write_checksums:
        if not errors:
            with (ROOT / MANIFEST).open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(manifest_text)
    else:
        recorded = {}
        for line in (ROOT / MANIFEST).read_text(encoding="utf-8").splitlines():
            match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
            if not match or match[2] in recorded:
                errors.append("Malformed or duplicate checksum entry")
                continue
            recorded[match[2]] = match[1]
        for name in sorted(recorded.keys() | hashes.keys()):
            if recorded.get(name) != hashes.get(name):
                errors.append(f"Checksum mismatch or file-set change: {name}")

    summary = {
        "passed": not errors,
        "public_files": len(names),
        "checksummed_files": len(hashes),
        "total_bytes": total_bytes,
        "largest_file": {"path": largest[1], "bytes": largest[0]},
        "json_files_parsed": parsed,
        "python_files_parsed": python_files,
        "release_mod_files_verified": len(actual_mod),
        "empty_character_name_patches": len(retired),
        "runtime_tested": False,
        "errors": errors,
    }
    print(json.dumps(summary, ensure_ascii=True, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write-checksums", action="store_true",
        help="Explicitly refresh SHA256SUMS.txt after reviewing intended changes.",
    )
    args = parser.parse_args()
    try:
        sys.exit(check(args.write_checksums))
    except (OSError, ValueError, KeyError, RuntimeError, subprocess.CalledProcessError) as exc:
        print(f"Public repository check failed: {exc}", file=sys.stderr)
        sys.exit(1)
