"""Negative and positive gates for the isolated three-helper repair release."""
from pathlib import Path
import hashlib
import json
import tempfile
import unittest
from unittest.mock import patch
import limited_repair_release as repair

from limited_repair_release import (
    APPROVED_CHANGE_PATHS, HELPER_ASSETS, compare_repair_trees,
    create_repair_release, validate_lua_audit, validate_input_tree_against_audit,
    validate_stage_lua_hashes, validate_stage_config_hashes, verify_fixed_evidence, validate_test_report,
    validate_expected_helper_hashes,
    validate_extra_fallback_report,
)


class LimitedRepairGateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.before, self.after = self.root / "before", self.root / "after"
        self.before.mkdir(); self.after.mkdir()
        entries = {"_metadata": b'{"priority":1000,"version":"0.2.4-fu6.5.8"}\n',
                   "objects/untouched.object": b'{"name":"stable"}\n',
                   "scripts/untouched.lua": b"return 9\n"}
        entries.update({asset: b"return 'old helper'\n" for asset in APPROVED_CHANGE_PATHS})
        self.write(self.before, entries); self.write(self.after, entries)
        self.new_helpers = {asset: ("return 'reviewed %s'\n" % asset).encode()
                            for asset in APPROVED_CHANGE_PATHS}
        for asset, raw in self.new_helpers.items():
            (self.after / asset).write_bytes(raw)

    @staticmethod
    def write(root, entries):
        for name, data in entries.items():
            path = root / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)

    def test_accepts_exact_three_helper_replacement(self):
        report = compare_repair_trees(self.before, self.after, self.new_helpers)
        self.assertEqual(set(report["changed_paths"]), APPROVED_CHANGE_PATHS)
        self.assertEqual(set(report["approved_change_paths"]), APPROVED_CHANGE_PATHS)
        self.assertEqual(report["input_asset_count"], report["output_asset_count"])
        self.assertTrue(report["all_non_helper_raw_sha256_identical"])
        self.assertTrue(report["metadata_typed_json_identical"])
        self.assertEqual(set(report["input_tree_inventory"]), set(report["output_tree_inventory"]))

    def test_rejects_unrelated_file_change(self):
        (self.after / "scripts/untouched.lua").write_bytes(b"return 10\n")
        with self.assertRaisesRegex(ValueError, "unexpected PAK assets"):
            compare_repair_trees(self.before, self.after, self.new_helpers)

    def test_rejects_added_or_missing_asset_paths(self):
        (self.after / "extra.txt").write_bytes(b"extra")
        with self.assertRaisesRegex(ValueError, "path set"):
            compare_repair_trees(self.before, self.after, self.new_helpers)
        (self.after / "extra.txt").unlink(); (self.after / "objects/untouched.object").unlink()
        with self.assertRaisesRegex(ValueError, "path set"):
            compare_repair_trees(self.before, self.after, self.new_helpers)

    def test_rejects_metadata_type_change(self):
        (self.after / "_metadata").write_bytes(b'{"priority":true,"version":"0.2.4-fu6.5.8"}\n')
        with self.assertRaisesRegex(ValueError, "typed _metadata"):
            compare_repair_trees(self.before, self.after, self.new_helpers)

    def test_rejects_widened_allowlist_or_missing_helper(self):
        with self.assertRaisesRegex(ValueError, "exactly the three helper"):
            compare_repair_trees(self.before, self.after, self.new_helpers,
                                 approved_paths=APPROVED_CHANGE_PATHS | {"scripts/untouched.lua"})
        one = next(iter(APPROVED_CHANGE_PATHS))
        with self.assertRaisesRegex(ValueError, "exactly the three helper"):
            compare_repair_trees(self.before, self.after, {one: self.new_helpers[one]})

    def test_rejects_unreviewed_or_old_helper_hash_map(self):
        self.assertEqual(set(HELPER_ASSETS), APPROVED_CHANGE_PATHS)
        self.assertEqual(validate_expected_helper_hashes(HELPER_ASSETS), HELPER_ASSETS)
        with self.assertRaisesRegex(ValueError, "explicit parent review"):
            validate_expected_helper_hashes({**HELPER_ASSETS, "fujp/species_display.lua": "PENDING_REVIEW"})
        with self.assertRaisesRegex(ValueError, "explicit parent review"):
            validate_expected_helper_hashes({asset: HELPER_ASSETS[asset]
                                              for asset in APPROVED_CHANGE_PATHS
                                              if asset != "fujp/guide_display.lua"})

    def test_rejects_report_predating_current_target_hashes(self):
        hashes = {"fujp/lua_display.lua": "c" * 64, "other.lua": "d" * 64}
        path = self.root / "lua53.json"
        path.write_text(json.dumps({"status": "passed", "runtime": "Lua 5.3", "cases": 28,
            "assertions": 915, "lua_library_sha256": "a" * 64,
            "tested_lua_sha256": {"fujp/lua_display.lua": "b" * 64, "other.lua": "d" * 64}}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "target hashes differ"):
            validate_test_report(path, "Lua 5.3", hashes, {"fujp/lua_display.config": "e" * 64})

    def test_rejects_unpassed_or_incomplete_test_report(self):
        hashes = {"fujp/lua_display.lua": "c" * 64}
        path = self.root / "lua54.json"
        path.write_text(json.dumps({"status": "failed", "runtime": "Lua 5.4", "cases": 27,
            "assertions": 900, "lua_library_sha256": "a" * 64,
            "tested_lua_sha256": hashes}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "did not pass"):
            validate_test_report(path, "Lua 5.4", hashes, {"fujp/lua_display.config": "e" * 64})

    def test_rejects_duplicate_or_empty_audit_asset_rows(self):
        report, inventory = self.root / "audit.json", self.root / "inventory.json"
        report.write_text(json.dumps({"worktree_lua_count_start": 135, "worktree_lua_count_end": 135,
            "worktree_changes_during_audit": [], "inventory": "inventory.json", "summary": {}}), encoding="utf-8")
        rows = [{"asset": f"asset/{i}.lua", "worktree_jp": {"sha256": "a" * 64}} for i in range(135)]
        rows[-1]["asset"] = ""
        inventory.write_text(json.dumps({"worktree_lua_count_start": 135, "worktree_lua_count_end": 135,
            "worktree_changes_during_audit": [], "files": rows}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unique nonempty"):
            validate_lua_audit(report, inventory, {f"asset/{i}.lua": "a" * 64 for i in range(135)})

    def test_rejects_stale_audit_hash_and_duplicate_asset_rows(self):
        report, inventory = self.root / "audit.json", self.root / "inventory.json"
        report.write_text(json.dumps({"worktree_lua_count_start": 135, "worktree_lua_count_end": 135,
            "worktree_changes_during_audit": [], "inventory": "inventory.json", "summary": {}}), encoding="utf-8")
        paths = sorted(APPROVED_CHANGE_PATHS)
        generated = {paths[0]: "a" * 64, **{f"other/{i}.lua": "a" * 64 for i in range(134)}}
        rows = [{"asset": paths[0], "worktree_jp": {"sha256": "b" * 64}}]
        rows += [{"asset": f"other/{i}.lua", "worktree_jp": {"sha256": "a" * 64}} for i in range(134)]
        inventory.write_text(json.dumps({"worktree_lua_count_start": 135, "worktree_lua_count_end": 135,
            "worktree_changes_during_audit": [], "files": rows}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "worktree hash is stale"):
            validate_lua_audit(report, inventory, generated)
        rows[1]["asset"] = paths[0]
        inventory.write_text(json.dumps({"worktree_lua_count_start": 135, "worktree_lua_count_end": 135,
            "worktree_changes_during_audit": [], "files": rows}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unique nonempty"):
            validate_lua_audit(report, inventory, generated)

    def test_rejects_test_hash_map_with_missing_or_extra_assets(self):
        path = self.root / "lua53.json"; expected = {"one.lua": "c" * 64, "two.lua": "d" * 64}
        for actual in ({"one.lua": "c" * 64}, {**expected, "extra.lua": "e" * 64}):
            path.write_text(json.dumps({"status": "passed", "runtime": "Lua 5.3", "cases": 28,
                "assertions": 915, "lua_library_sha256": "f" * 64,
                "tested_lua_sha256": actual}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "target hashes differ"):
                validate_test_report(path, "Lua 5.3", expected, {})

    def test_checks_each_input_tree_target_hash_against_audit(self):
        audit, tree = self.root / "input-audit.json", self.root / "input-tree"; tree.mkdir()
        paths = list(sorted(APPROVED_CHANGE_PATHS))
        entries = {asset: f"helper-{asset}".encode() for asset in paths}
        entries.update({f"other/{i}.lua": f"lua-{i}".encode() for i in range(135-len(entries))})
        rows = []
        for asset, data in entries.items():
            path = tree / asset; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
            rows.append({"asset": asset, "installed_fujp_pak": {"present": True,
                "sha256": hashlib.sha256(data).hexdigest()}})
        audit.write_text(json.dumps({"files": rows}), encoding="utf-8")
        self.assertEqual(validate_input_tree_against_audit(tree, audit)["matched_assets"], 135)
        rows[0]["installed_fujp_pak"]["sha256"] = "0" * 64
        audit.write_text(json.dumps({"files": rows}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "differs from audit evidence"):
            validate_input_tree_against_audit(tree, audit)

    def test_rejects_stage_mutation_after_allowlist_check(self):
        from limited_repair_release import verify_stage_unchanged
        initial = compare_repair_trees(self.before, self.after, self.new_helpers)
        (self.after / "scripts/untouched.lua").write_bytes(b"changed while packing")
        with self.assertRaisesRegex(ValueError, "unexpected PAK assets"):
            verify_stage_unchanged(self.before, self.after, self.new_helpers, initial)

    def test_rejects_stage_lua_hash_drift(self):
        contents = {**self.new_helpers, "scripts/untouched.lua": b"other"}
        expected = {name: hashlib.sha256(data).hexdigest() for name, data in contents.items()}
        for name, data in contents.items():
            path = self.after/name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
        self.assertEqual(validate_stage_lua_hashes(self.after, expected), expected)
        (self.after/"scripts/untouched.lua").write_bytes(b"stale")
        with self.assertRaisesRegex(ValueError, "Staged Lua set/hash differs"):
            validate_stage_lua_hashes(self.after, expected)

    def test_requires_input_and_staged_configs_to_match_tested_dictionary_bytes(self):
        hashes = {}
        for asset in ("fujp/lua_display.config", "fujp/species_display.config", "fujp/guide_display.config"):
            data = ("{} " + asset).encode(); path = self.after / asset
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(data)
            hashes[asset] = hashlib.sha256(data).hexdigest()
        self.assertEqual(validate_stage_config_hashes(self.after, hashes), hashes)
        (self.after / "fujp/species_display.config").write_bytes(b"different tested dictionary")
        with self.assertRaisesRegex(ValueError, "config hashes differ"):
            validate_stage_config_hashes(self.after, hashes)

    def test_rejects_input_or_evidence_changed_before_zip_write(self):
        pak = self.root / "input.pak"; pak.write_bytes(b"pinned bytes")
        from limited_repair_release import file_sha256
        pinned = file_sha256(pak)
        with patch("limited_repair_release.validate_evidence", return_value={"snapshot": "changed"}):
            with self.assertRaisesRegex(ValueError, "evidence changed"):
                verify_fixed_evidence(self.root, pak, self.root, self.root, self.root, {"snapshot": "initial"}, pinned)
        pak.write_bytes(b"drifted bytes")
        with self.assertRaisesRegex(ValueError, "input PAK changed"):
            verify_fixed_evidence(self.root, pak, self.root, self.root, self.root, {"snapshot": "initial"}, pinned)

    def test_rejects_input_pak_drift_before_tools_or_outputs(self):
        pak, output = self.root / "installed.pak", self.root / "dist"; pak.write_bytes(b"not pinned")
        with self.assertRaisesRegex(ValueError, "differs from the pinned installed PAK"):
            create_repair_release(self.root, pak, self.root / "tools", output)
        self.assertFalse(output.exists())

    def _extra_report_fixture(self):
        project = self.root / "fixture-project"
        report_path = self.root / "extra-report.json"
        test_script = project / "source/compat/test_extra_display_fallback.py"
        test_script.parent.mkdir(parents=True, exist_ok=True); test_script.write_bytes(b"# reviewed harness\n")
        source_paths = {
            "fujp/species_display.lua": project / "source/compat/followup_022/fujp/species_display.lua",
            "fujp/guide_display.lua": project / "source/compat/followup_022/fujp/guide_display.lua",
        }
        config_paths = {
            "fujp/species_display.config": project / "source/compat/followup_022/fujp/species_display.config",
            "fujp/guide_display.config": project / "source/compat/followup_022/fujp/guide_display.config",
        }
        expected_helpers = {}
        source_rows = []
        for asset, path in source_paths.items():
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes((asset + "\n").encode())
            digest = hashlib.sha256(path.read_bytes()).hexdigest(); expected_helpers[asset] = digest
            source_rows.append({"path": str(path.resolve()), "sha256": digest})
        config_rows = []
        mod = project / "mods/FU_Japanese"
        for asset, path in config_paths.items():
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes((asset + "-config\n").encode())
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            generated = mod / asset; generated.parent.mkdir(parents=True, exist_ok=True); generated.write_bytes(path.read_bytes())
            config_rows.append({"path": str(path.resolve()), "sha256": digest})
        dlls = {}
        runtime_rows = []
        for version in ("Lua 5.3", "Lua 5.4"):
            dll = self.root / (version.replace(" ", "") + ".dll"); dll.write_bytes(version.encode())
            dlls[version] = dll
            runtime_rows.append({"luaVersion": version.removeprefix("Lua "),
                "dll": {"path": str(dll.resolve()), "sha256": hashlib.sha256(dll.read_bytes()).hexdigest()},
                "result": "passed", "caseCount": 249, "assertionCount": 639})
        cases = [f"case {i}" for i in range(249)]
        report = {"schemaVersion": 1, "status": "passed", "createdAt": "2026-11-12T00:00:00Z",
            "test": {"path": str(test_script.resolve()), "sha256": hashlib.sha256(test_script.read_bytes()).hexdigest()},
            "caseCount": len(cases), "cases": cases, "runtimes": runtime_rows,
            "sources": source_rows, "configs": config_rows,
            "configuredEntryCounts": {"speciesDescriptionsAndNames": 167, "guideFieldsAndPages": 62}}
        report_path.write_text(json.dumps(report), encoding="utf-8")
        return project, report_path, test_script, expected_helpers, dlls

    def test_accepts_report_bound_to_current_helpers_configs_harness_and_dlls(self):
        project, report, script, helpers, dlls = self._extra_report_fixture()
        with patch("limited_repair_release.EXTRA_FALLBACK_DLLS", dlls):
            evidence = validate_extra_fallback_report(report, script, project, helpers)
        self.assertEqual(evidence["case_count"], 249)
        self.assertEqual(len(evidence["runtimes"]), 2)
        self.assertEqual(len(evidence["sources"]), 2)
        self.assertEqual(len(evidence["configs"]), 2)

    def test_rejects_extra_report_status_harness_source_config_dll_runtime_or_coverage_drift(self):
        project, report_path, script, helpers, dlls = self._extra_report_fixture()
        with patch("limited_repair_release.EXTRA_FALLBACK_DLLS", dlls):
            base = json.loads(report_path.read_text(encoding="utf-8"))
            mutations = [
                (lambda r: r.update(status="failed"), "not explicitly passed"),
                (lambda r: r["test"].update(sha256="0" * 64), "current test harness"),
                (lambda r: r["sources"][0].update(sha256="0" * 64), "sources hashes differ"),
                (lambda r: r["configs"][0].update(sha256="0" * 64), "configs hashes differ"),
                (lambda r: r["runtimes"][0]["dll"].update(sha256="0" * 64), "different Lua DLL"),
                (lambda r: r["runtimes"].__setitem__(1, dict(r["runtimes"][0])), "duplicate runtime"),
                (lambda r: r.update(caseCount=248), "unexpected case coverage"),
            ]
            for mutate, message in mutations:
                candidate = json.loads(json.dumps(base)); mutate(candidate)
                report_path.write_text(json.dumps(candidate), encoding="utf-8")
                with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                    validate_extra_fallback_report(report_path, script, project, helpers)


if __name__ == "__main__":
    unittest.main(verbosity=2)
