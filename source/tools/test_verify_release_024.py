"""Unit tests for the targeted 0.2.4 release verifier."""
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

import verify_release_024 as verifier


class Release024VerifierTests(unittest.TestCase):
    def test_head_baselines_are_fixed_hash_only_inputs(self):
        baseline = verifier.json.loads(verifier.BASELINE_FIXTURE.read_text(encoding="utf-8"))
        outputs = verifier.json.loads(verifier.APPEND_FIXTURE.read_text(encoding="utf-8"))
        radio = verifier.json.loads(verifier.RADIO_FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(baseline["expected_file_count"], 14526)
        self.assertEqual(len(baseline["files"]), 14526)
        self.assertRegex(baseline["source_git_head"], r"^[0-9a-f]{40}$")
        self.assertRegex(baseline["source_manifest_sha256"], r"^[0-9a-f]{64}$")
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{64}", value)
                            for value in baseline["files"].values()))
        self.assertEqual(outputs["expected_asset_count"], 20)
        self.assertEqual(len(outputs["assets"]), 20)
        self.assertTrue(all(re.fullmatch(r"[0-9a-f]{64}", row["output_sha256"])
                            for row in outputs["assets"]))
        self.assertEqual(radio["successful_message_count"], 16)
        self.assertEqual(len(radio["successful_text_sha256"]), 16)
        self.assertTrue(all(len(value) == 64 for value in radio["successful_text_sha256"].values()))
        self.assertNotIn("source_text", radio)
        self.assertNotIn("translation_text", radio)

    def test_inventory_allows_only_declared_changes_and_no_file_set_drift(self):
        baseline = {"a.patch": "a" * 64, "b.txt": "b" * 64}
        changed = {"a.patch": "c" * 64, "b.txt": "b" * 64}
        result = verifier.compare_inventory(baseline, baseline, changed, {"a.patch"})
        self.assertTrue(result["baseline_matches_fixture"])
        self.assertTrue(result["same_file_set"])
        self.assertTrue(result["changed_paths_within_allowlist"])
        outside = {"a.patch": "c" * 64, "b.txt": "d" * 64}
        result = verifier.compare_inventory(baseline, baseline, outside, {"a.patch"})
        self.assertFalse(result["changed_paths_within_allowlist"])
        added = {**changed, "new.txt": "e" * 64}
        result = verifier.compare_inventory(baseline, baseline, added, {"a.patch"})
        self.assertFalse(result["same_file_set"])

    def test_metadata_comparison_is_type_sensitive(self):
        self.assertFalse(verifier.type_sensitive_equal({"priority": True}, {"priority": 1}))
        self.assertTrue(verifier.type_sensitive_equal({"includes": ["FU"]}, {"includes": ["FU"]}))

    def test_radio_number_tokens_handle_japanese_and_english_prefixes(self):
        self.assertEqual(verifier.NUMBER_RE.findall("確率17.3%ともおさらば"), ["17.3%"])
        self.assertEqual(verifier.NUMBER_RE.findall("chance is 17.3% now"), ["17.3%"])
        self.assertEqual(verifier.NUMBER_RE.findall("[Mouse 1] then [Shift]"), ["1"])

    def test_pinned_radio_hash_normalizes_crlf_and_rejects_text_mutation(self):
        pinned_lf = b'{"key":"value"}\n'
        installed_crlf = pinned_lf.replace(b"\n", b"\r\n")
        expected = verifier.sha256(pinned_lf)
        self.assertNotEqual(verifier.sha256(installed_crlf), expected)
        self.assertEqual(verifier.lf_normalized_sha256(installed_crlf), expected)
        mutated = installed_crlf.replace(b"value", b"valuE")
        self.assertNotEqual(verifier.lf_normalized_sha256(mutated), expected)

    def test_strict_patch_application_reports_failed_test_groups(self):
        source = {"message": {"text": "English"}}
        operations = [
            [{"op": "test", "path": "/message/text", "value": "English"},
             {"op": "replace", "path": "/message/text", "value": "日本語"}],
            [{"op": "test", "path": "/message/text", "value": "English"},
             {"op": "replace", "path": "/message/text", "value": "違う"}],
        ]
        actual, report = verifier.strict_apply(source, operations)
        self.assertEqual(actual["message"]["text"], "日本語")
        self.assertEqual(report["group_count"], 2)
        self.assertEqual(report["applied_group_count"], 1)
        self.assertEqual(report["failed_group_count"], 1)

    def test_only_exact_duplicate_guard_group_that_is_a_noop_is_tolerated(self):
        first = [
            {"op": "test", "path": "/message/text", "value": "English"},
            {"op": "replace", "path": "/message/text", "value": "日本語"},
        ]
        duplicate = [dict(operation) for operation in first]
        source = {"message": {"text": "English"}}
        actual, report = verifier.strict_apply(source, [first, duplicate], {1: 0})
        self.assertEqual(actual["message"]["text"], "日本語")
        self.assertEqual(report["failed_group_count"], 0)
        self.assertEqual(report["applied_group_count"], 1)
        self.assertEqual(report["group_count"], 2)
        self.assertEqual(report["tolerated_duplicate_group_count"], 1)
        self.assertEqual(report["tolerated_duplicate_groups"], [{"group_index": 1, "duplicate_of": 0}])

        different_translation = [dict(operation) for operation in first]
        different_translation[1]["value"] = "別訳"
        _, report = verifier.strict_apply(source, [first, different_translation], {1: 0})
        self.assertEqual(report["failed_group_count"], 1)
        self.assertEqual(report["tolerated_duplicate_group_count"], 0)

        _, report = verifier.strict_apply(source, [first, duplicate])
        self.assertEqual(report["failed_group_count"], 1)
        self.assertEqual(report["tolerated_duplicate_group_count"], 0)

    def test_one_character_source_change_fails_radio_patch_test_guard(self):
        original = {"radio": {"text": "Original"}}
        operations = [[
            {"op": "test", "path": "/radio/text", "value": "Original"},
            {"op": "replace", "path": "/radio/text", "value": "日本語"},
        ]]
        _, report = verifier.strict_apply(original, operations)
        self.assertEqual(report["failed_group_count"], 0)
        altered = {"radio": {"text": "OriginaL"}}
        _, report = verifier.strict_apply(altered, operations)
        self.assertEqual(report["failed_group_count"], 1)

    def test_tree_hash_uses_relative_names_and_rejects_symlinks(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "nested").mkdir()
            (root / "nested" / "asset.txt").write_bytes(b"asset")
            self.assertEqual(set(verifier.hash_tree(root)), {"nested/asset.txt"})
            with patch.object(Path, "is_symlink", return_value=True):
                with self.assertRaisesRegex(ValueError, "symlink"):
                    verifier.hash_tree(root)


if __name__ == "__main__":
    unittest.main(verbosity=2)
