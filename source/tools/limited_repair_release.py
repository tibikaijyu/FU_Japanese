#!/usr/bin/env python3
"""Create an exact three-helper repair PAK from the pinned installed FU Japanese PAK.

This is intentionally separate from package_release.py: it proves the exact
input PAK and three-helper overlay delta, and makes no claim of whole-MOD rebuild
or validation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path, PurePosixPath

from package_release import canonical_json, sha, tree_inventory, verify_pak_tree, write_zip

ROOT = Path(__file__).resolve().parents[2]
EXPECTED_INPUT_PAK_SHA256 = "7f32db9bccff3b0dd5cf84a1f57b767408109d5b3b01f3064b30c2fe6ac7a889"
HELPER_ASSETS = {
    "fujp/lua_display.lua": "a17f0dcca89fd18c0b72abf5f0405ca2a3cf40612602ab58f255d82824cc3020",
    "fujp/species_display.lua": "37d435f245de42bb682601b0772b0260d80553142b4e8d2de62148576fc54082",
    "fujp/guide_display.lua": "7c83737a833ebf985e99b1cf21a091528589db50abac7a588ab46cae95d2e23a",
}
APPROVED_CHANGE_PATHS = frozenset(HELPER_ASSETS)
RELEASE_ID = "0.2.4-public.3"
PAK_RELEASE_ID = "0.2.4-public.3-pak.1"
AUDIT_REPORT = ROOT.parent / ".local/stability-2026-11-12/fu-audit/report.json"
AUDIT_INVENTORY = ROOT.parent / ".local/stability-2026-11-12/fu-audit/inventory.json"
EVIDENCE_DIR = ROOT.parent / ".local/stability-2026-11-12/fu-fallback"
REPORT_DIR = ROOT.parent / ".local/stability-2026-11-12/fu-fallback/releases"
EXTRA_FALLBACK_REPORT = ROOT.parent / ".local/stability-2026-11-12/fu-extra/fallback-report.json"
EXTRA_FALLBACK_TEST = ROOT / "source/compat/test_extra_display_fallback.py"
EXTRA_FALLBACK_CASE_COUNT = 249
EXTRA_FALLBACK_ASSERTION_COUNT = 639
EXTRA_FALLBACK_DLLS = {
    "Lua 5.3": ROOT.parent / "RPGGrowthJP/source/build/tools/lua53/lua53.dll",
    "Lua 5.4": ROOT.parent / "RPGGrowthJP/source/build/tools/lua54/lua54.dll",
}
DEFAULT_INPUT_PAK = Path(r"E:/SteamLibrary/steamapps/common/Starbound/mods/FU_Japanese.pak")
DEFAULT_TOOLS = Path(r"E:/SteamLibrary/steamapps/common/Starbound/win32")


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


CONFIG_ASSETS = ("fujp/lua_display.config", "fujp/species_display.config", "fujp/guide_display.config")


def validate_test_report(path: Path, runtime: str, expected_lua_hashes: dict[str, str],
                         expected_config_hashes: dict[str, str]):
    report = read_json(path)
    if report.get("status") != "passed" or report.get("runtime") != runtime:
        raise ValueError(f"Lua compatibility evidence did not pass: {path}")
    if report.get("cases") != 28 or report.get("assertions") != 915:
        raise ValueError(f"Lua compatibility evidence has unexpected coverage: {path}")
    if report.get("tested_lua_sha256") != expected_lua_hashes:
        raise ValueError(f"Lua compatibility report target hashes differ from the current 135 Lua assets: {path}")
    if report.get("tested_display_config_sha256") != expected_config_hashes:
        raise ValueError(f"Lua compatibility report config hashes differ from the current display dictionaries: {path}")
    if not report.get("lua_library_sha256"):
        raise ValueError(f"Lua runtime binary hash is missing: {path}")
    return report


def validate_lua_audit(report_path: Path, inventory_path: Path, generated_lua_hashes: dict[str, str]):
    report, inventory = read_json(report_path), read_json(inventory_path)
    if report.get("worktree_lua_count_start") != 135 or report.get("worktree_lua_count_end") != 135:
        raise ValueError("Lua audit must cover the fixed 135-target worktree")
    if inventory.get("worktree_lua_count_start") != 135 or inventory.get("worktree_lua_count_end") != 135:
        raise ValueError("Lua audit inventory must cover the fixed 135-target worktree")
    if report.get("worktree_changes_during_audit") or inventory.get("worktree_changes_during_audit"):
        raise ValueError("Lua audit observed source changes during its run")
    if report.get("inventory") != "inventory.json":
        raise ValueError("Lua audit does not point to the expected inventory")
    if len(inventory.get("files", [])) != 135:
        raise ValueError("Lua audit inventory file count is not 135")
    rows = inventory["files"]
    assets = [item.get("asset") for item in rows]
    if any(not isinstance(asset, str) or not asset for asset in assets) or len(set(assets)) != 135:
        raise ValueError("Lua audit must contain 135 unique nonempty asset paths")
    if set(assets) != set(generated_lua_hashes):
        raise ValueError("Lua audit asset set differs from the generated MOD Lua set")
    audited_hashes = []
    for item in rows:
        worktree = item.get("worktree_jp", {})
        if not item.get("asset") or not worktree.get("sha256"):
            raise ValueError("Lua audit lacks a worktree hash for one target")
        asset = item["asset"]
        if worktree["sha256"] != generated_lua_hashes[asset]:
            raise ValueError("Lua audit worktree hash is stale for " + asset)
        audited_hashes.append({
            "asset": item["asset"],
            "worktree_sha256": worktree["sha256"],
            "installed_fujp_pak_sha256": item.get("installed_fujp_pak", {}).get("sha256"),
            "final_logged_winner": item.get("final_logged_winner"),
            "classification": item.get("classification"),
            "status": item.get("status"),
        })
    return {
        "report_path": str(Path(report_path).resolve()),
        "report_sha256": file_sha256(report_path),
        "inventory_path": str(Path(inventory_path).resolve()),
        "inventory_sha256": file_sha256(inventory_path),
        "target_lua_count": 135,
        "audit_summary": report.get("summary"),
        "external_override_summary": report.get("external_override_summary"),
        "audited_target_hashes": audited_hashes,
    }


def validate_input_tree_against_audit(input_tree: Path, audit_inventory_path: Path):
    tree = tree_inventory(input_tree)
    rows = read_json(audit_inventory_path).get("files", [])
    for row in rows:
        asset = row["asset"]
        installed = row.get("installed_fujp_pak", {})
        if not installed.get("present") or not installed.get("sha256"):
            raise ValueError("Input PAK audit lacks an installed hash for " + asset)
        if asset not in tree or tree[asset]["sha256"] != installed["sha256"]:
            raise ValueError("Input PAK asset differs from audit evidence: " + asset)
    return {"matched_assets": len(rows), "all_installed_target_hashes_match": True}


def validate_stage_lua_hashes(stage_dir: Path, expected_lua_hashes: dict[str, str]):
    stage_dir = Path(stage_dir)
    actual = {
        path.relative_to(stage_dir).as_posix(): sha(path.read_bytes())
        for path in sorted(stage_dir.rglob("*.lua"))
    }
    if actual != expected_lua_hashes:
        missing = sorted(set(expected_lua_hashes) - set(actual))
        extra = sorted(set(actual) - set(expected_lua_hashes))
        stale = sorted(name for name in set(actual) & set(expected_lua_hashes)
                       if actual[name] != expected_lua_hashes[name])
        raise ValueError(f"Staged Lua set/hash differs from tested 135 targets (missing={missing[:3]}, extra={extra[:3]}, stale={stale[:3]})")
    return actual


def validate_stage_config_hashes(stage_dir: Path, expected_config_hashes: dict[str, str]):
    actual = {}
    for asset in CONFIG_ASSETS:
        path = Path(stage_dir) / asset
        if not path.is_file():
            raise ValueError("Staged PAK is missing a tested display config: " + asset)
        actual[asset] = sha(path.read_bytes())
    if actual != expected_config_hashes:
        raise ValueError("Staged PAK config hashes differ from the dictionaries used by Lua tests")
    return actual


def validate_expected_helper_hashes(expected_helpers: dict[str, str]):
    if set(expected_helpers) != APPROVED_CHANGE_PATHS or any(
            not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value)
            for value in expected_helpers.values()):
        raise ValueError("All three repair helper hashes require explicit parent review")
    return expected_helpers


def validate_extra_fallback_report(report_path: Path, test_script: Path, project: Path,
                                   expected_helpers: dict[str, str]):
    report = read_json(report_path)
    if report.get("schemaVersion") != 1 or report.get("status") != "passed":
        raise ValueError("Extra display fallback report is not explicitly passed")
    if not isinstance(report.get("createdAt"), str) or not report["createdAt"].strip():
        raise ValueError("Extra display fallback report lacks a creation timestamp")
    test_script = Path(test_script).resolve()
    test_row = report.get("test", {})
    if test_row.get("path") != str(test_script) or test_row.get("sha256") != file_sha256(test_script):
        raise ValueError("Extra display fallback report is not bound to the current test harness")
    if report.get("caseCount") != EXTRA_FALLBACK_CASE_COUNT:
        raise ValueError("Extra display fallback report has unexpected case coverage")
    cases = report.get("cases")
    if (not isinstance(cases, list) or len(cases) != EXTRA_FALLBACK_CASE_COUNT
            or any(not isinstance(case, str) or not case.strip() for case in cases)
            or len(set(cases)) != EXTRA_FALLBACK_CASE_COUNT):
        raise ValueError("Extra display fallback cases must be unique, named, and complete")
    runtime_rows = report.get("runtimes")
    if not isinstance(runtime_rows, list) or len(runtime_rows) != 2:
        raise ValueError("Extra display fallback report must include both Lua runtime rows")
    expected_runtimes = {}
    for version, dll_path in EXTRA_FALLBACK_DLLS.items():
        expected_runtimes[version] = {
            "path": str(dll_path.resolve()),
            "sha256": file_sha256(dll_path),
        }
    seen_runtimes = set()
    runtime_evidence = []
    for row in runtime_rows:
        version = str(row.get("luaVersion", ""))
        version = "Lua " + version.removeprefix("Lua ")
        if version not in expected_runtimes or version in seen_runtimes:
            raise ValueError("Extra display fallback report has missing or duplicate runtime rows")
        expected = expected_runtimes[version]
        dll = row.get("dll", {})
        if dll.get("path") != expected["path"] or dll.get("sha256") != expected["sha256"]:
            raise ValueError("Extra display fallback report is bound to a different Lua DLL: " + version)
        if (row.get("result") != "passed" or row.get("caseCount") != EXTRA_FALLBACK_CASE_COUNT
                or row.get("assertionCount") != EXTRA_FALLBACK_ASSERTION_COUNT):
            raise ValueError("Extra display fallback runtime did not report complete passing assertions: " + version)
        seen_runtimes.add(version)
        runtime_evidence.append({"lua_version": version, "dll_path": expected["path"],
                                 "dll_sha256": expected["sha256"], "case_count": row["caseCount"],
                                 "assertion_count": row["assertionCount"]})
    if seen_runtimes != set(expected_runtimes):
        raise ValueError("Extra display fallback report does not cover Lua 5.3 and 5.4")
    if report.get("configuredEntryCounts") != {
            "speciesDescriptionsAndNames": 167, "guideFieldsAndPages": 62}:
        raise ValueError("Extra display fallback report does not cover the reviewed dictionary entry counts")

    test_script = Path(test_script).resolve()
    project = Path(project).resolve()
    expected_sources = {
        str((project / "source/compat/followup_022/fujp/species_display.lua").resolve()): expected_helpers["fujp/species_display.lua"],
        str((project / "source/compat/followup_022/fujp/guide_display.lua").resolve()): expected_helpers["fujp/guide_display.lua"],
    }
    expected_configs = {
        str((project / "source/compat/followup_022/fujp/species_display.config").resolve()): file_sha256(project / "source/compat/followup_022/fujp/species_display.config"),
        str((project / "source/compat/followup_022/fujp/guide_display.config").resolve()): file_sha256(project / "source/compat/followup_022/fujp/guide_display.config"),
    }
    for key, expected_map in (("sources", expected_sources), ("configs", expected_configs)):
        rows = report.get(key)
        if not isinstance(rows, list) or len(rows) != len(expected_map):
            raise ValueError("Extra display fallback " + key + " evidence has the wrong asset set")
        actual = {item.get("path"): item.get("sha256") for item in rows if isinstance(item, dict)}
        if actual != expected_map:
            raise ValueError("Extra display fallback " + key + " hashes differ from current reviewed files")
    tested_config_hashes = {
        "fujp/species_display.config": expected_configs[str((project / "source/compat/followup_022/fujp/species_display.config").resolve())],
        "fujp/guide_display.config": expected_configs[str((project / "source/compat/followup_022/fujp/guide_display.config").resolve())],
    }
    for asset, expected_hash in tested_config_hashes.items():
        if file_sha256(project / "mods/FU_Japanese" / asset) != expected_hash:
            raise ValueError("Generated MOD config differs from the extra test config: " + asset)
    return {
        "report_path": str(Path(report_path).resolve()), "report_sha256": file_sha256(report_path),
        "harness_path": test_row["path"], "harness_sha256": test_row["sha256"],
        "case_count": len(cases), "cases": cases, "runtimes": runtime_evidence,
        "sources": expected_sources, "configs": expected_configs,
        "tested_config_hashes": tested_config_hashes,
    }


def validate_evidence(project: Path, evidence_dir: Path, audit_report: Path, audit_inventory: Path,
                      expected_helpers: dict[str, str] = HELPER_ASSETS):
    project = Path(project).resolve()
    source_paths = {
        "fujp/lua_display.lua": "source/compat/fujp/lua_display.lua",
        "fujp/species_display.lua": "source/compat/followup_022/fujp/species_display.lua",
        "fujp/guide_display.lua": "source/compat/followup_022/fujp/guide_display.lua",
    }
    validate_expected_helper_hashes(expected_helpers)
    helper_hashes = {}
    for asset, source_rel in source_paths.items():
        source_bytes = (project / source_rel).read_bytes()
        generated_bytes = (project / "mods/FU_Japanese" / asset).read_bytes()
        if source_bytes != generated_bytes:
            raise ValueError("Generated helper differs from its compatibility source: " + asset)
        helper_hash = sha(source_bytes)
        if helper_hash != expected_helpers[asset]:
            raise ValueError("Helper content differs from the reviewed repair hash: " + asset)
        helper_hashes[asset] = helper_hash

    generated_lua_hashes = {
        path.relative_to(project / "mods/FU_Japanese").as_posix(): sha(path.read_bytes())
        for path in sorted((project / "mods/FU_Japanese").rglob("*.lua"))
    }
    if len(generated_lua_hashes) != 135:
        raise ValueError("Current MOD must contain exactly the audited 135 Lua target files")
    generated_config_hashes = {}
    for asset in CONFIG_ASSETS:
        path = project / "mods/FU_Japanese" / asset
        if not path.is_file():
            raise ValueError("Current MOD is missing a display config tested by the fallback suites: " + asset)
        generated_config_hashes[asset] = sha(path.read_bytes())
    lua53 = validate_test_report(evidence_dir / "lua53-live-upstream-three-helper.json",
                                 "Lua 5.3", generated_lua_hashes, generated_config_hashes)
    lua54 = validate_test_report(evidence_dir / "lua54-live-upstream-three-helper.json",
                                 "Lua 5.4", generated_lua_hashes, generated_config_hashes)
    audit = validate_lua_audit(audit_report, audit_inventory, generated_lua_hashes)
    extra = validate_extra_fallback_report(EXTRA_FALLBACK_REPORT, EXTRA_FALLBACK_TEST, project, expected_helpers)
    return {
        "helper_assets": helper_hashes,
        "generated_lua_file_count": len(generated_lua_hashes),
        "generated_lua_hashes": generated_lua_hashes,
        "tested_display_config_hashes": generated_config_hashes,
        "lua_compatibility": {
            "lua53": {"report_sha256": file_sha256(evidence_dir / "lua53-live-upstream-three-helper.json"),
                      "runtime": lua53["runtime"], "cases": lua53["cases"], "assertions": lua53["assertions"],
                      "lua_library_sha256": lua53["lua_library_sha256"]},
            "lua54": {"report_sha256": file_sha256(evidence_dir / "lua54-live-upstream-three-helper.json"),
                      "runtime": lua54["runtime"], "cases": lua54["cases"], "assertions": lua54["assertions"],
                      "lua_library_sha256": lua54["lua_library_sha256"]},
        },
        "lua_audit": audit,
        "extra_display_fallback": extra,
    }


def compare_repair_trees(before_dir: Path, after_dir: Path, helper_bytes: dict[str, bytes],
                         approved_paths=frozenset(APPROVED_CHANGE_PATHS)):
    """Require the exact reviewed helper delta and type-sensitive metadata equality."""
    if set(approved_paths) != APPROVED_CHANGE_PATHS:
        raise ValueError("Repair change allowlist must be exactly the three helper assets")
    if set(helper_bytes) != APPROVED_CHANGE_PATHS:
        raise ValueError("Replacement bytes must be provided for exactly the three helper assets")
    before = tree_inventory(before_dir)
    after = tree_inventory(after_dir)
    if set(before) != set(after):
        missing = sorted(set(before) - set(after))
        added = sorted(set(after) - set(before))
        raise ValueError(f"Repair changed the PAK path set (missing={missing[:3]}, added={added[:3]})")
    before_meta = (Path(before_dir) / "_metadata").read_bytes()
    after_meta = (Path(after_dir) / "_metadata").read_bytes()
    if canonical_json(before_meta) != canonical_json(after_meta):
        raise ValueError("Repair changed typed _metadata content")
    changed = {name for name in before if before[name] != after[name]}
    if changed != APPROVED_CHANGE_PATHS:
        raise ValueError(f"Repair changed unexpected PAK assets: {sorted(changed)}")
    for asset, raw in helper_bytes.items():
        if (Path(after_dir) / asset).read_bytes() != raw:
            raise ValueError("Repair output helper does not match the generated source: " + asset)
    return {
        "input_asset_count": len(before),
        "output_asset_count": len(after),
        "relative_paths_identical": True,
        "changed_paths": sorted(changed),
        "all_non_helper_raw_sha256_identical": True,
        "approved_change_paths": sorted(APPROVED_CHANGE_PATHS),
        "metadata_typed_json_identical": True,
        "input_helper_hashes": {asset: before[asset]["sha256"] for asset in sorted(APPROVED_CHANGE_PATHS)},
        "output_helper_hashes": {asset: after[asset]["sha256"] for asset in sorted(APPROVED_CHANGE_PATHS)},
        "input_metadata_sha256": sha(before_meta),
        "output_metadata_sha256": sha(after_meta),
        "input_tree_inventory_sha256": sha(json.dumps(before, sort_keys=True, separators=(",", ":")).encode()),
        "output_tree_inventory_sha256": sha(json.dumps(after, sort_keys=True, separators=(",", ":")).encode()),
        "input_tree_inventory": before,
        "output_tree_inventory": after,
    }


def verify_stage_unchanged(before_dir: Path, stage_dir: Path, helper_bytes: dict[str, bytes], expected_delta: dict):
    current = compare_repair_trees(before_dir, stage_dir, helper_bytes)
    if current != expected_delta:
        raise ValueError("Staged repair tree changed after its initial allowlist verification")
    return current


def verify_fixed_evidence(project: Path, input_pak: Path, evidence_dir: Path,
                          audit_report: Path, audit_inventory: Path, initial_evidence: dict,
                          input_pak_sha256: str):
    if file_sha256(input_pak) != input_pak_sha256:
        raise ValueError("Pinned input PAK changed during release preparation")
    current = validate_evidence(project, evidence_dir, audit_report, audit_inventory)
    if current != initial_evidence:
        raise ValueError("Lua helper, tests, or audit evidence changed during release preparation")
    return True


def _run_official(command):
    subprocess.run([str(item) for item in command], check=True, capture_output=True, text=True)


def _payload(project: Path, pak_bytes: bytes):
    note = project / "docs/limited-repair/FU_Japanese_0.2.4-public.3.md"
    install = project / "docs/limited-repair/INSTALL_JA.txt"
    required = [
        note, install, project / "LICENSE.md", project / "THIRD_PARTY_NOTICES.md",
        project / "LICENSES/MIT-tools.txt",
        project / "mods/FU_Japanese/ATTRIBUTION.txt",
        project / "mods/FU_Japanese/LICENSE-FU-CC-BY-4.0.txt",
    ]
    if any(not path.is_file() for path in required):
        raise ValueError("Repair package documentation or license material is missing")
    files = {
        "README_JA.md": note.read_bytes(),
        "INSTALL_JA.txt": install.read_bytes(),
        "LICENSE.md": (project / "LICENSE.md").read_bytes(),
        "THIRD_PARTY_NOTICES.md": (project / "THIRD_PARTY_NOTICES.md").read_bytes(),
        "LICENSES/MIT-tools.txt": (project / "LICENSES/MIT-tools.txt").read_bytes(),
        "LICENSES/FU_Japanese/ATTRIBUTION.txt": (project / "mods/FU_Japanese/ATTRIBUTION.txt").read_bytes(),
        "LICENSES/FU_Japanese/LICENSE-FU-CC-BY-4.0.txt": (project / "mods/FU_Japanese/LICENSE-FU-CC-BY-4.0.txt").read_bytes(),
        "mods/FU_Japanese.pak": pak_bytes,
    }
    return files


def create_repair_release(project: Path, input_pak: Path, tools_dir: Path, output_dir: Path,
                          release_id=RELEASE_ID, pak_release_id=PAK_RELEASE_ID,
                          evidence_dir=EVIDENCE_DIR, audit_report=AUDIT_REPORT,
                          audit_inventory=AUDIT_INVENTORY):
    project = Path(project).resolve()
    input_pak, tools_dir, output_dir = map(Path, (input_pak, tools_dir, output_dir))
    if release_id != RELEASE_ID or pak_release_id != PAK_RELEASE_ID:
        raise ValueError("This limited repair uses only the reviewed .public.3 / .pak.1 IDs")
    if not input_pak.is_file() or file_sha256(input_pak) != EXPECTED_INPUT_PAK_SHA256:
        raise ValueError("Input PAK is missing or differs from the pinned installed PAK")
    input_pak_sha256 = file_sha256(input_pak)
    evidence = validate_evidence(project, evidence_dir, audit_report, audit_inventory)
    packer, unpacker = tools_dir / "asset_packer.exe", tools_dir / "asset_unpacker.exe"
    for tool in (packer, unpacker):
        if not tool.is_file():
            raise ValueError("Official Starbound packer/unpacker is missing: " + str(tool))

    pak_base = f"FU_Japanese_{pak_release_id}"
    zip_name = pak_base + "-install.zip"
    report_name = pak_base + "-generation-report.json"
    manifest_name = f"release-artifacts-{release_id}.json"
    sums_name = f"SHA256SUMS-{release_id}.txt"
    output_dir = output_dir.resolve()
    if not output_dir.is_relative_to(project.resolve() / "dist"):
        raise ValueError("Limited repair outputs must remain under the project dist directory")
    collisions = [name for name in (zip_name, report_name, manifest_name, sums_name)
                  if (output_dir / name).exists()]
    if collisions:
        raise FileExistsError("Repair outputs already exist; never overwrite history: " + ", ".join(collisions))

    output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".fu-limited-repair-", dir=output_dir) as temp:
        temp = Path(temp)
        extracted = temp / "input-tree"
        stage = temp / "stage" / "FU_Japanese"
        repacked = temp / "FU_Japanese.pak"
        roundtrip = temp / "roundtrip"
        extracted.mkdir()
        _run_official([unpacker, input_pak, extracted])
        if not extracted.is_dir() or not (extracted / "_metadata").is_file():
            raise ValueError("Official unpacker did not produce a valid input tree")
        input_audit_check = validate_input_tree_against_audit(extracted, audit_inventory)
        validate_stage_config_hashes(extracted, evidence["tested_display_config_hashes"])
        shutil.copytree(extracted, stage)
        helper_sources = {
            "fujp/lua_display.lua": project / "source/compat/fujp/lua_display.lua",
            "fujp/species_display.lua": project / "source/compat/followup_022/fujp/species_display.lua",
            "fujp/guide_display.lua": project / "source/compat/followup_022/fujp/guide_display.lua",
        }
        helper_bytes = {asset: path.read_bytes() for asset, path in helper_sources.items()}
        if {asset: sha(raw) for asset, raw in helper_bytes.items()} != evidence["helper_assets"]:
            raise ValueError("Helper sources changed after evidence validation")
        for asset, raw in helper_bytes.items():
            helper_path = stage / asset
            if not helper_path.is_file():
                raise ValueError("Pinned input PAK is missing target helper asset: " + asset)
            helper_path.write_bytes(raw)
        delta = compare_repair_trees(extracted, stage, helper_bytes)
        stage_lua_hashes = validate_stage_lua_hashes(stage, evidence["generated_lua_hashes"])
        stage_config_hashes = validate_stage_config_hashes(stage, evidence["tested_display_config_hashes"])

        _run_official([packer, stage, repacked])
        if not repacked.is_file():
            raise ValueError("Official asset_packer did not produce a repair PAK")
        _run_official([unpacker, repacked, roundtrip])
        pak_roundtrip = verify_pak_tree(stage, roundtrip)
        if not pak_roundtrip["relative_paths_match"] or not pak_roundtrip["non_metadata_raw_sha256_match"] or not pak_roundtrip["metadata_json_deep_equal"]:
            raise ValueError("Official PAK round-trip verification failed")
        verify_stage_unchanged(extracted, stage, helper_bytes, delta)
        validate_stage_lua_hashes(stage, evidence["generated_lua_hashes"])
        validate_stage_config_hashes(stage, evidence["tested_display_config_hashes"])

        pak_bytes = repacked.read_bytes()
        payload = _payload(project, pak_bytes)
        verify_fixed_evidence(project, input_pak, evidence_dir, audit_report, audit_inventory,
                              evidence, input_pak_sha256)
        temp_zip_path = temp / zip_name
        artifact = write_zip(temp_zip_path, pak_base, payload)
        artifact["file"] = zip_name
        verify_fixed_evidence(project, input_pak, evidence_dir, audit_report, audit_inventory,
                              evidence, input_pak_sha256)
        report = {
            "schema_version": 1,
            "release_id": release_id,
            "pak_release_id": pak_release_id,
            "distribution_scope": "three-helper repair overlay from pinned installed PAK; no whole-MOD rebuild or validation claimed",
            "input_pak": {"path": str(input_pak.resolve()), "sha256": EXPECTED_INPUT_PAK_SHA256,
                          "bytes": input_pak.stat().st_size},
            "evidence": evidence,
            "input_pak_audit_check": input_audit_check,
            "staged_lua_target_count": len(stage_lua_hashes),
            "staged_lua_hashes": stage_lua_hashes,
            "staged_display_config_hashes": stage_config_hashes,
            "repair_delta": delta,
            "official_tools": {"asset_packer": str(packer.resolve()), "asset_packer_sha256": file_sha256(packer),
                               "asset_unpacker": str(unpacker.resolve()), "asset_unpacker_sha256": file_sha256(unpacker)},
            "pak": {"path_in_zip": "mods/FU_Japanese.pak", "sha256": sha(pak_bytes),
                    "bytes": len(pak_bytes), "roundtrip": pak_roundtrip},
            "zip": artifact,
            "native_game_executed": False,
            "optional_font_pak_included": False,
            "known_scope_note": "This limited helper repair does not address the pre-existing Weapon Stats Workshop item 729726478 overlay on buildweapon.lua and buildunrandweapon.lua, or one pre-existing FU researchTree.lua difference related to descriptions and update timing. Runtime causes and effects are unverified; no follow-up, removal, or stability claim is included.",
            "performance_optimization": False,
        }
        report_path = temp / report_name
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        manifest = {
            "schema_version": 1,
            "release_id": release_id,
            "pak_release_id": pak_release_id,
            "distribution_scope": "three-helper repair PAK only",
            "artifacts": [{"file": zip_name, "sha256": artifact["sha256"], "bytes": artifact["bytes"]}],
            "upload_allowlist": [zip_name],
            "generation_report": {"file": report_name, "sha256": file_sha256(report_path)},
            "whole_mod_validation_claimed": False,
        }
        manifest_path = temp / manifest_name
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
                                 encoding="utf-8", newline="\n")
        sums_path = temp / sums_name
        sums_path.write_text(f"{artifact['sha256']}  {zip_name}\n", encoding="utf-8", newline="\n")
        created = []
        try:
            for name in (zip_name, report_name, manifest_name, sums_name):
                destination = output_dir / name
                source_path = temp / name
                with destination.open("xb") as output_stream, source_path.open("rb") as input_stream:
                    shutil.copyfileobj(input_stream, output_stream)
                created.append(destination)
        except Exception:
            for destination in created:
                destination.unlink(missing_ok=True)
            raise
    return {"zip": str(output_dir / zip_name), "report": str(output_dir / report_name),
            "manifest": str(output_dir / manifest_name), "upload_allowlist": [zip_name]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-pak", type=Path, default=DEFAULT_INPUT_PAK)
    parser.add_argument("--tools-dir", type=Path, default=DEFAULT_TOOLS)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    parser.add_argument("--project", type=Path, default=ROOT)
    parser.add_argument("--evidence-dir", type=Path, default=EVIDENCE_DIR)
    parser.add_argument("--audit-report", type=Path, default=AUDIT_REPORT)
    parser.add_argument("--audit-inventory", type=Path, default=AUDIT_INVENTORY)
    args = parser.parse_args()
    print(json.dumps(create_repair_release(args.project, args.input_pak, args.tools_dir,
                                           args.output_dir, evidence_dir=args.evidence_dir,
                                           audit_report=args.audit_report,
                                           audit_inventory=args.audit_inventory), indent=2))


if __name__ == "__main__":
    main()
