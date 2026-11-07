#!/usr/bin/env python3
"""Package the checked-in layout into verified install/source ZIPs (stdlib only)."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]
RELEASE_ID = "0.2.3-public.1"
ZIP_TIME = (2026, 11, 7, 0, 0, 0)
INSTALL_DOCS = {
    "README_JA.md", "INSTALL_JA.txt", "CHANGELOG.md", "LICENSE.md",
    "THIRD_PARTY_NOTICES.md", "LICENSES/MIT-tools.txt",
    "docs/verification/2026-11-07-user-report.md",
    "source/machine_translation/README.md",
    "source/machine_translation/model_provenance.json",
}
REQUIRED_SOURCE = {
    "source/machine_translation/model_provenance.json",
    "source/machine_translation/pre_review_semantic_candidates.jsonl",
    "source/source/catalog.jsonl", "source/compat/followup_022/fujp/species_display.lua",
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def safe_public_path(name):
    path = PurePosixPath(name)
    if (not name or path.is_absolute() or ".." in path.parts or
            any(c in name for c in "\\:\r\n") or path.as_posix() != name):
        return False
    forbidden = {".git", ".local", ".venv", "venv", "__pycache__", "fugumt-model"}
    if forbidden.intersection(path.parts):
        return False
    return not (name.startswith(("docs/development/", "source/reports/scope/")) or
                name.endswith((".log", ".zip", ".pyc")))

def load_public_files(root):
    """The reviewed checksum manifest is the explicit source-package allowlist."""
    files = {}
    for line in (root / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match or not safe_public_path(match[2]):
            raise ValueError("Unsafe or malformed public checksum entry")
        expected, name = match.groups()
        if name in files or name == "SHA256SUMS.txt":
            raise ValueError("Duplicate or self-referential checksum entry")
        file = root / name
        if file.is_symlink() or not file.resolve().is_relative_to(root.resolve()):
            raise ValueError("Symlinks are not supported: " + name)
        data = file.read_bytes()
        if sha(data) != expected:
            raise ValueError("Public checksum mismatch: " + name)
        files[name] = data
    return files

def validate_release(files):
    for name in REQUIRED_SOURCE | INSTALL_DOCS:
        if name not in files:
            raise ValueError("Required source/notice missing: " + name)
    report = json.loads(files["source/reports/validation.json"])
    metadata = json.loads(files["mods/FU_Japanese/_metadata"])
    if not report["passed"] or metadata["version"] != report["mod_version"]:
        raise ValueError("Release validation does not match the MOD version")
    prefix = "mods/FU_Japanese/"
    actual = {name[len(prefix):]: sha(data) for name, data in files.items() if name.startswith(prefix)}
    if actual != json.loads(files["source/reports/mod_sha256.json"]):
        raise ValueError("Game files differ from the validated MOD")
    coverage = json.loads(files["source/reports/coverage.json"])
    if sha(files["source/source/catalog.jsonl"]) != coverage["catalog_sha256"]:
        raise ValueError("Coverage predates the catalog")
    if (coverage["rejected_entries"] or coverage["append_coverage"]["rejected"] or
            coverage["retained_reasons"].get("not_translated", 0)):
        raise ValueError("Unresolved translation validation failures")
    audit = json.loads(files["source/reports/final_residual_decisions.json"])
    for key in ("missing_translation_fields", "unclassified_whole_fields", "structural_errors",
                "mixed_english_clause_unique_sources"):
        if audit[key]:
            raise ValueError("Completeness audit failed: " + key)
    for name, expected in audit["input_sha256"].items():
        if sha(files["source/source/" + name]) != expected:
            raise ValueError("Completeness audit predates: " + name)
    evidence = json.loads(files["source/reports/test_summary_023.json"])
    if not evidence["passed"]:
        raise ValueError("Stored regression evidence is not passing")
    for row in evidence["reports"]:
        if not row["passed"] or sha(files["source/reports/" + row["file"]]) != row["sha256"]:
            raise ValueError("Regression evidence changed: " + row["file"])
    return metadata["version"]

def install_files(files):
    return {name: data for name, data in files.items()
            if name.startswith(("mods/FU_Japanese/", "optional/FU_Japanese_Font/")) or name in INSTALL_DOCS}

def write_zip(destination, prefix, files):
    if destination.is_symlink():
        raise ValueError("Refusing to replace a symlink")
    payload = dict(files)
    payload["SHA256SUMS.txt"] = "".join(
        f"{sha(data)}  {name}\n" for name, data in sorted(files.items())
    ).encode("utf-8")
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(payload.items()):
            if not safe_public_path(name):
                raise ValueError("Invalid archive path: " + name)
            info = zipfile.ZipInfo(prefix + "/" + name, ZIP_TIME)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(destination) as archive:
        expected_names = {prefix + "/" + name for name in payload}
        if set(archive.namelist()) != expected_names or len(archive.infolist()) != len(expected_names):
            raise ValueError("ZIP file list mismatch")
        # Reading every member verifies CRC; compare the exact archived payload too.
        for name, data in payload.items():
            if archive.read(prefix + "/" + name) != data:
                raise ValueError("ZIP content mismatch: " + name)
    return {"file": destination.name, "files": len(payload), "bytes": destination.stat().st_size,
            "sha256": sha(destination.read_bytes()), "crc_and_content_verified": True}

def package(root, output_dir, release_id=RELEASE_ID):
    root, output_dir = Path(root).resolve(), Path(output_dir).resolve()
    if not re.fullmatch(r"\d+\.\d+\.\d+-public\.\d+", release_id):
        raise ValueError("Use a distinct public repack identifier, e.g. 0.2.3-public.1")
    if output_dir == root or not output_dir.is_relative_to(root):
        raise ValueError("Output must be a separate directory inside the repository")
    files = load_public_files(root)
    version = validate_release(files)
    if version.split("-fu")[0] != release_id.split("-public.")[0]:
        raise ValueError("Repack identifier does not match the MOD version")
    output_dir.mkdir(parents=True, exist_ok=True)
    prefix = "FU_Japanese_" + release_id
    artifacts = []
    for kind, payload in (("install", install_files(files)), ("source", files)):
        artifacts.append(write_zip(output_dir / f"{prefix}-{kind}.zip", prefix, payload))
    checksums = output_dir / f"SHA256SUMS-{release_id}.txt"
    checksums.write_bytes("".join(f"{row['sha256']}  {row['file']}\n" for row in artifacts).encode())
    report = {"release_id": release_id, "mod_version": version, "prerelease": True,
              "native_game_executed": False, "artifacts": artifacts,
              "checksum_file": checksums.name,
              "reproducibility": "Fixed names, order, timestamps, permissions and compression level. ZIP byte identity is tested with the same Python/zlib runtime."}
    (output_dir / "release-artifacts.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2))
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    parser.add_argument("--release-id", default=RELEASE_ID)
    args = parser.parse_args()
    package(args.root, args.output_dir, args.release_id)
