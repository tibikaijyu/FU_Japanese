#!/usr/bin/env python3
"""Create and verify MOD-bound release test evidence (stdlib only).

After real tests, each report must include passed, failures, errors, skipped, and input_state_sha256.
Capture input_state_sha256(filesystem_files(ROOT)) before and after tests, reject a changed
state, and write the unchanged hash into each report before creating the summary. For example:
  before = input_state_sha256(filesystem_files(ROOT)); result = run_real_tests()
  after = input_state_sha256(filesystem_files(ROOT))
  if before != after or not result.passed: raise SystemExit("input changed or tests failed")
  write_report({"passed": True, "failures": 0, "errors": 0, "skipped": 0, "input_state_sha256": after})
Then run: python source/tools/release_evidence.py create --report runtime.json --report build.json
Reports are read from source/reports. Input inventory uses Git public files, matching package inputs;
ignored model weights, caches, dist, summary, and checksum files are not read.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SUMMARY = "source/reports/test_summary_024.json"
VERSION = "0.2.4"
INPUT_ROOTS = (
    "mods/FU_Japanese", "source/tools", "source/source", "source/compat",
    "source/upstream-overrides", "source/machine_translation", "source/tests",
)
INPUT_FILES = ("source/requirements-build.txt", "source/requirements-test.txt")
REQUIRED_INPUT_ROOTS = (
    "mods/FU_Japanese/", "source/tools/", "source/source/",
    "source/compat/", "source/machine_translation/",
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def is_input(name):
    if name in INPUT_FILES:
        return True
    if "__pycache__" in PurePosixPath(name).parts or name.endswith((".pyc", ".pyo")):
        return False
    return any(name.startswith(root + "/") for root in INPUT_ROOTS)


def filesystem_files(root):
    """Read only Git-public files in input scope, never ignored model/cache files."""
    root = Path(root).resolve()
    try:
        probe = subprocess.run(
            ["git", "-c", "safe.directory=" + str(root), "-C", str(root), "rev-parse", "--show-toplevel"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        ).stdout.decode("utf-8").strip()
        if Path(probe).resolve() != root:
            raise ValueError("Release evidence root must be a Git repository root")
        raw = subprocess.run(
            ["git", "-c", "safe.directory=" + str(root), "-C", str(root),
             "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True,
        ).stdout.decode("utf-8")
        listed = raw.split(chr(0))
    except (FileNotFoundError, subprocess.CalledProcessError):
        # Isolated unit-test fixtures have no Git repository; apply public-path
        # exclusions while walking those small temporary trees.
        listed = []
        for directory in INPUT_ROOTS:
            path = root / directory
            if path.exists():
                for item in path.rglob("*"):
                    if item.is_dir() and not item.is_symlink():
                        continue
                    listed.append(item.relative_to(root).as_posix())
        listed.extend(name for name in INPUT_FILES if (root / name).exists())
    result = {}
    for name in sorted(set(listed)):
        if not name or not is_public_input_path(name) or not is_input(name):
            continue
        item = root / name
        if item.is_symlink() or not item.is_file():
            raise ValueError("Missing file or unsupported symlink in release input: " + name)
        result[name] = item.read_bytes()
    return result


def is_public_input_path(name):
    path = PurePosixPath(name)
    forbidden = {".git", ".local", ".venv", "venv", "__pycache__", "fugumt-model"}
    return (not path.is_absolute() and ".." not in path.parts and
            not forbidden.intersection(path.parts) and
            not name.endswith((".pyc", ".pyo", ".log", ".zip")))


def current_input_hashes(files):
    result = {name: sha(data) for name, data in files.items()
              if is_input(name) and is_public_input_path(name)}
    for prefix in REQUIRED_INPUT_ROOTS:
        if not any(name.startswith(prefix) for name in result):
            raise ValueError("Required release input tree is empty or absent: " + prefix.rstrip("/"))
    return dict(sorted(result.items()))


def input_state_sha256(files):
    """Hash the canonical SHA-256 inventory that binds one test run to its inputs."""
    canonical = json.dumps(current_input_hashes(files), sort_keys=True,
                           separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return sha(canonical)


def validate_release_evidence(files, expected_version=VERSION):
    """Validate 0.2.4 test reports and their binding to current release inputs."""
    if SUMMARY not in files:
        raise ValueError("Required release evidence is missing: " + SUMMARY)
    try:
        evidence = json.loads(files[SUMMARY].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("Release evidence is not valid UTF-8 JSON") from exc
    if not isinstance(evidence, dict) or evidence.get("version") != expected_version:
        raise ValueError("Release evidence version does not match " + expected_version)
    if evidence.get("passed") is not True:
        raise ValueError("Stored release checks are not passing")
    current = current_input_hashes(files)
    state_hash = input_state_sha256(files)
    if evidence.get("inputs") != current or evidence.get("input_state_sha256") != state_hash:
        raise ValueError("Release evidence input hashes do not match current MOD/source inputs")
    reports = evidence.get("reports")
    if not isinstance(reports, list) or not reports:
        raise ValueError("Release evidence has no report references")
    seen = set()
    for row in reports:
        if not isinstance(row, dict):
            raise ValueError("Malformed release test report reference")
        name = row.get("file")
        if (not isinstance(name, str) or PurePosixPath(name).name != name or
                name in ("", "SHA256SUMS.txt", Path(SUMMARY).name) or
                not re.fullmatch(r"[A-Za-z0-9_.-]+\.json", name)):
            raise ValueError("Unsafe release test report name")
        if name in seen:
            raise ValueError("Duplicate release test report: " + name)
        seen.add(name)
        path = "source/reports/" + name
        data = files.get(path)
        if data is None or row.get("sha256") != sha(data):
            raise ValueError("Release evidence report hash mismatch or missing report: " + path)
        try:
            report = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("Referenced test report is not valid JSON: " + path) from exc
        if not isinstance(report, dict) or report.get("passed") is not True or row.get("passed") is not True:
            raise ValueError("Release test report failed: " + path)
        if report.get("input_state_sha256") != state_hash:
            raise ValueError("Release test report was produced for a different input state: " + path)
        for key in ("failures", "errors", "skipped"):
            value = row.get(key)
            reported = report.get(key)
            if (isinstance(value, bool) or not isinstance(value, int) or value < 0 or
                    isinstance(reported, bool) or not isinstance(reported, int) or reported < 0):
                raise ValueError("Release report requires a nonnegative integer " + key + ": " + path)
            if value or reported:
                raise ValueError("Release report has " + key + " tests: " + path)
            if reported != value:
                raise ValueError("Release evidence count differs from test report: " + path)
    return evidence


def report_row(root, name, expected_state_hash):
    if (not isinstance(name, str) or PurePosixPath(name).name != name or
            not re.fullmatch(r"[A-Za-z0-9_.-]+.json", name) or
            name in (Path(SUMMARY).name, "SHA256SUMS.txt")):
        raise ValueError("Report must be a simple JSON filename under source/reports")
    path = Path(root) / "source/reports" / name
    data = path.read_bytes()
    report = json.loads(data.decode("utf-8"))
    if not isinstance(report, dict) or report.get("passed") is not True:
        raise ValueError("Refusing to summarize a failed test report: " + name)
    if report.get("input_state_sha256") != expected_state_hash:
        raise ValueError("Test report input state is stale or missing: " + name)
    row = {"file": name, "sha256": sha(data), "passed": True}
    for key in ("failures", "errors", "skipped"):
        value = report.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value != 0:
            raise ValueError("Report must show " + key + "=0: " + name)
        row[key] = value
    if "tests_run" in report:
        row["tests_run"] = report["tests_run"]
    return row


def create_summary(root, report_names, destination=None):
    """Write the summary only from existing passing test-result JSON files."""
    root = Path(root).resolve()
    current_files = filesystem_files(root)
    inputs = current_input_hashes(current_files)
    state_hash = input_state_sha256(current_files)
    rows = [report_row(root, name, state_hash) for name in report_names]
    if not rows or len({row["file"] for row in rows}) != len(rows):
        raise ValueError("Provide one or more unique report filenames")
    evidence = {"version": VERSION, "passed": True, "reports": rows,
                "inputs": inputs, "input_state_sha256": state_hash}
    target = Path(destination) if destination else root / SUMMARY
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                      encoding="utf-8", newline="\n")
    return evidence


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("create", nargs="?", choices=("create",), default="create")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--report", action="append", required=True,
                        help="Passing JSON test report filename under source/reports (repeatable)")
    args = parser.parse_args(argv)
    try:
        evidence = create_summary(args.root, args.report)
        print(json.dumps({"written": str((args.root / SUMMARY).resolve()),
                          "version": evidence["version"], "reports": len(evidence["reports"]),
                          "bound_inputs": len(evidence["inputs"])}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print("Release evidence creation failed: " + str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
