"""Tests for 0.2.4 release evidence binding and fail-closed checks."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from release_evidence import (SUMMARY, create_summary, filesystem_files,
                               input_state_sha256, validate_release_evidence)


class ReleaseEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for name in (
            "mods/FU_Japanese/_metadata", "mods/FU_Japanese/items/example.patch",
            "source/tools/build.py", "source/source/catalog.jsonl",
            "source/compat/runtime.lua", "source/machine_translation/machine_translations.json",
        ):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(("fixture:" + name).encode())
        report = self.root / "source/reports/runtime_tests.json"
        report.parent.mkdir(parents=True, exist_ok=True)
        state = input_state_sha256(filesystem_files(self.root))
        report.write_text(json.dumps({"passed": True, "tests_run": 4, "failures": 0,
                                      "errors": 0, "skipped": 0,
                                      "input_state_sha256": state}), encoding="utf-8")
        create_summary(self.root, ["runtime_tests.json"])

    def tearDown(self):
        self.temp.cleanup()

    def files(self):
        result = {}
        for path in self.root.rglob("*"):
            if path.is_file():
                result[path.relative_to(self.root).as_posix()] = path.read_bytes()
        return result

    def update_summary(self, edit):
        path = self.root / SUMMARY
        evidence = json.loads(path.read_text(encoding="utf-8"))
        edit(evidence)
        path.write_text(json.dumps(evidence), encoding="utf-8")

    def test_accepts_current_024_summary_and_report_hashes(self):
        evidence = validate_release_evidence(self.files())
        self.assertEqual(evidence["version"], "0.2.4")
        self.assertEqual(evidence["reports"][0]["tests_run"], 4)

    def test_input_inventory_excludes_private_model_cache_and_dist(self):
        private = (
            "source/machine_translation/fugumt-model/weights.bin",
            "source/tools/__pycache__/local.pyc",
            "source/tools/private.log",
        )
        for name in private:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"must not enter public evidence")
        files = filesystem_files(self.root)
        self.assertTrue(all(name not in files for name in private))
        self.assertFalse(any(name.startswith("dist/") for name in files))

    def test_rejects_old_release_version(self):
        self.update_summary(lambda data: data.update(version="0.2.3"))
        with self.assertRaisesRegex(ValueError, "version"):
            validate_release_evidence(self.files())

    def test_rejects_missing_report(self):
        self.update_summary(lambda data: data["reports"][0].update(file="absent.json"))
        with self.assertRaisesRegex(ValueError, "missing report"):
            validate_release_evidence(self.files())

    def test_rejects_failed_report(self):
        self.update_summary(lambda data: data["reports"][0].update(passed=False))
        with self.assertRaisesRegex(ValueError, "report failed"):
            validate_release_evidence(self.files())

    def test_rejects_skipped_tests(self):
        self.update_summary(lambda data: data["reports"][0].update(skipped=1))
        with self.assertRaisesRegex(ValueError, "skipped tests"):
            validate_release_evidence(self.files())

    def test_rejects_changed_source_or_mod(self):
        for name in ("source/tools/build.py", "mods/FU_Japanese/_metadata"):
            with self.subTest(name=name):
                files = self.files()
                files[name] = b"changed after tests"
                with self.assertRaisesRegex(ValueError, "input hashes"):
                    validate_release_evidence(files)

    def test_rejects_failure_or_skip_in_report_payload(self):
        for key in ("failures", "skipped"):
            with self.subTest(key=key):
                report_path = self.root / "source/reports/runtime_tests.json"
                report = json.loads(report_path.read_text(encoding="utf-8"))
                report[key] = 1
                report_path.write_text(json.dumps(report), encoding="utf-8")
                import hashlib
                digest = hashlib.sha256(report_path.read_bytes()).hexdigest()
                self.update_summary(lambda data: data["reports"][0].update(sha256=digest, **{key: 0}))
                with self.assertRaisesRegex(ValueError, "has " + key):
                    validate_release_evidence(self.files())
                self.tearDown()
                self.setUp()

    def test_create_rejects_old_report_after_input_changes(self):
        source = self.root / "source/tools/build.py"
        source.write_bytes(b"changed after test execution")
        with self.assertRaisesRegex(ValueError, "input state is stale"):
            create_summary(self.root, ["runtime_tests.json"])

    def test_rejects_report_hash_mismatch(self):
        files = self.files()
        files["source/reports/runtime_tests.json"] = b'{"passed":true,"tests_run":4,"failures":0,"errors":0,"skipped":0}'
        with self.assertRaisesRegex(ValueError, "report hash mismatch"):
            validate_release_evidence(files)

    def test_rejects_missing_failure_counter(self):
        report = self.root / "source/reports/runtime_tests.json"
        state = input_state_sha256(filesystem_files(self.root))
        report.write_text(json.dumps({"passed": True, "tests_run": 4, "errors": 0, "skipped": 0,
                                      "input_state_sha256": state}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "failures=0"):
            create_summary(self.root, ["runtime_tests.json"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
