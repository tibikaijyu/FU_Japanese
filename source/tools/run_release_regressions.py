#!/usr/bin/env python3
"""Run the public 0.2.4 regression suite and write evidence only on a clean run.

Run from the repository root after installing source/requirements-test.txt:
  python source/tools/run_release_regressions.py --baseline-mod <0.2.3-MOD> \
      --mod mods/FU_Japanese --append-basis-inputs <append-basis-inputs.json>
The generated source/reports/regression_024.json can then be bound into
source/reports/test_summary_024.json with release_evidence.py.
"""
from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
import subprocess
import sys
import types
import unittest

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "source" / "tools"
SOURCE_TESTS = ROOT / "source" / "tests"
REPORT = ROOT / "source" / "reports" / "regression_024.json"
FIXTURES = SOURCE_TESTS / "namegen_fixtures"
REQUIRED_TOOL_TESTS = (
    "test_pak_release", "test_public_release", "test_release_evidence",
    "test_verify_release_024",
)

sys.path[:0] = [str(TOOLS), str(SOURCE_TESTS)]
from release_evidence import filesystem_files, input_state_sha256  # noqa: E402


class RecordingResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.records = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.records.append({"name": test.id(), "status": "passed"})

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.records.append({"name": test.id(), "status": "failed"})

    def addError(self, test, err):
        super().addError(test, err)
        self.records.append({"name": test.id(), "status": "error"})

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self.records.append({"name": test.id(), "status": "skipped", "reason": reason})


def load_suite(mod: Path) -> tuple[unittest.TestSuite, object]:
    suite = unittest.TestSuite()
    loader = unittest.defaultTestLoader
    loaded_modules = set()
    for name in REQUIRED_TOOL_TESTS:
        module = importlib.import_module(name)
        loaded_modules.add(name)
        suite.addTests(loader.loadTestsFromModule(module))

    # Include every repository source-level regression module exactly once.
    for path in sorted(SOURCE_TESTS.glob("test_*.py")):
        name = path.stem
        if name in loaded_modules:
            raise RuntimeError("Duplicate regression test module: " + name)
        module = importlib.import_module(name)
        loaded_modules.add(name)
        suite.addTests(loader.loadTestsFromModule(module))

    namegen = importlib.import_module("test_namegen_semantics")
    namegen.OPTIONS = types.SimpleNamespace(
        project=ROOT / "source", mod=mod, fixtures=FIXTURES,
        baseline_mod=None, report=None,
    )
    namegen_suite = loader.loadTestsFromTestCase(namegen.NamegenRegressionTests)
    if namegen_suite.countTestCases() != 11:
        raise RuntimeError("Expected 11 name-generation regression cases")
    suite.addTests(namegen_suite)
    return suite, namegen


def write_report(data: dict) -> None:
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8", newline="\n")


def run(args) -> dict:
    baseline_mod = args.baseline_mod.resolve()
    mod = args.mod.resolve()
    append_inputs = args.append_basis_inputs.resolve()
    # Invalidate any previous success before beginning, so a failed rerun cannot
    # leave stale passing evidence for summary creation.
    if REPORT.exists():
        REPORT.unlink()
    for label, path in (("baseline MOD", baseline_mod), ("candidate MOD", mod),
                        ("append-basis inputs", append_inputs)):
        if not path.exists():
            raise ValueError(f"{label} does not exist: {path}")

    from release_evidence import sha
    before_files = filesystem_files(ROOT)
    before_state = input_state_sha256(before_files)

    verifier = TOOLS / "verify_release_024.py"
    verify = subprocess.run(
        [sys.executable, "-X", "utf8", str(verifier),
         "--baseline-mod", str(baseline_mod), "--mod", str(mod),
         "--append-basis-inputs", str(append_inputs)],
        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
    )
    if verify.stdout:
        print(verify.stdout, end="" if verify.stdout.endswith("\n") else "\n")
    if verify.returncode != 0:
        raise RuntimeError("verify_release_024.py did not pass")
    validation_path = ROOT / "source" / "reports" / "validation.json"
    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    if (validation.get("schema") != "fu-japanese-release-024-validation-v1" or
            validation.get("passed") is not True or
            validation.get("mod_version") != "0.2.4-fu6.5.8"):
        raise RuntimeError("0.2.4 targeted verification report is not passing for the expected MOD version")

    suite, namegen = load_suite(mod)
    result = unittest.TextTestRunner(verbosity=2, resultclass=RecordingResult).run(suite)

    after_state = input_state_sha256(filesystem_files(ROOT))
    state_unchanged = before_state == after_state
    checks = validation.get("checks", {})
    append = validation.get("append_expectations", {}).get("assets", [])
    radio = validation.get("radio_verification", {})
    if (len(append) != 20 or sum(row.get("actual_group_count", 0) for row in append) != 1090 or
            radio.get("message_count") != 26 or radio.get("old_successful_count") != 16 or
            validation.get("baseline_inventory", {}).get("baseline_file_count") != 14526):
        raise RuntimeError("Verification report lacks the expected 20/26/14526 scope evidence")
    if any(value is False for value in checks.values() if isinstance(value, bool)):
        raise RuntimeError("Targeted 0.2.4 verification contains a failed check")
    append_translated_path = ROOT / "source" / "source" / "append_translated_catalog.jsonl"
    append_rows = [json.loads(line) for line in append_translated_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    additional_groups = sum(len(row.get("generated_paths", [])) for row in append_rows)
    total_groups = sum(row.get("actual_group_count", 0) for row in append)
    if additional_groups != 1030 or total_groups - additional_groups != 60:
        raise RuntimeError("Generated catalogs do not confirm 60 direct and 1030 additional groups")
    if not result.wasSuccessful() or result.testsRun == 0 or result.skipped:
        raise RuntimeError("Regression tests must finish with zero failures, errors, and skips")
    if not state_unchanged:
        raise RuntimeError("Public release inputs changed while regression tests were running")

    report = {
        "version": "0.2.4",
        "passed": True,
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "input_state_sha256": after_state,
        "input_state_unchanged_during_run": state_unchanged,
        "tests": result.records,
        "namegen_metrics": namegen.METRICS,
        "verification_summary": {
            "schema": validation["schema"],
            "passed": validation["passed"],
            "mod_version": validation["mod_version"],
            "baseline_file_count": validation["baseline_inventory"]["baseline_file_count"],
            "candidate_file_count": validation["baseline_inventory"]["candidate_file_count"],
            "same_file_set": validation["baseline_inventory"]["same_file_set"],
            "changed_paths": validation["baseline_inventory"]["changed_paths"],
            "changed_paths_within_allowlist": validation["baseline_inventory"]["changed_paths_within_allowlist"],
            "append_assets": append,
            "append_group_count": total_groups,
            "direct_group_count": total_groups - additional_groups,
            "additional_array_group_count": additional_groups,
            "append_translated_catalog_sha256": sha(append_translated_path.read_bytes()),
            "radio_verification": radio,
            "full_fu_source_reapplied": validation["full_fu_source_reapplied"],
            "native_game_executed": validation["native_game_executed"],
            "validation_report_sha256": sha(validation_path.read_bytes()),
            "mod_sha256_report_sha256": sha((ROOT / "source/reports/mod_sha256.json").read_bytes()),
        },
        "limits": [
            "Only the pinned 20 assets and whole-MOD change boundary were statically checked.",
            "The complete Frackin' Universe source checkout was not rebuilt or revalidated.",
            "Starbound in-game display and runtime performance were not tested; game verification is deferred.",
        ],
    }
    write_report(report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-mod", type=Path, required=True,
                        help="Unmodified 0.2.3 MOD directory matching the fixed verification fixture")
    parser.add_argument("--mod", type=Path, required=True, help="Generated 0.2.4 MOD directory")
    parser.add_argument("--append-basis-inputs", type=Path, required=True,
                        help="JSON describing the real base PAK and ordered installed asset layers")
    args = parser.parse_args(argv)
    try:
        report = run(args)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError, subprocess.SubprocessError) as error:
        print("0.2.4 release regressions failed: " + str(error), file=sys.stderr)
        return 1
    print(json.dumps({key: report[key] for key in
                      ("version", "passed", "tests_run", "failures", "errors", "skipped",
                       "input_state_sha256")}, ensure_ascii=False, indent=2))
    print("Wrote " + str(REPORT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
