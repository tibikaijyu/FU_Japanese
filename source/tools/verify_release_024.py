#!/usr/bin/env python3
"""Verify the targeted 0.2.4 regeneration against fixed byte and asset baselines."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "source" / "tools"
FIXTURES = ROOT / "source" / "tests" / "regression_024"
sys.path.insert(0, str(TOOLS))

import append_index_basis as index_basis  # noqa: E402
from validate import TestFailed, apply_batches  # noqa: E402


BASELINE_FIXTURE = FIXTURES / "baseline_mod_sha256.json"
APPEND_FIXTURE = FIXTURES / "append_output_expectations.json"
RADIO_FIXTURE = FIXTURES / "radio_baseline_text_sha256.json"
EXPECTED_VERSION = "0.2.4-fu6.5.8"
RADIO_ASSET = "radiomessages/fu_quests.radiomessages"
TARGETED_RADIO_KEYS = [
    "fu_start_greetings2", "fu_start_makeFurnace", "fu_start_makeForaging",
    "fu_start_Complete1a", "fu_start_Complete2", "fu_start_Complete2a",
    "fu_start_Complete2b", "fu_start_Complete3", "fu_start_Complete3a",
    "fu_start_Complete3b",
]
RADIO_MESSAGE_KEYS = [
    "fu_start_greetings0", "fu_start_greetings1", "fu_start_greetings1b",
    "fu_start_greetings2", "fu_start_greetingspickaxe", "fu_start_makeFurnace",
    "fu_start_makeForaging", "fu_start_makeTable", "fu_start_makeWire",
    "fu_start_makeElectromagnet", "fu_start_Complete1a", "fu_start_Complete1b",
    "fu_start_Complete1c", "fu_start_Complete2", "fu_start_Complete2a",
    "fu_start_Complete2b", "fu_start_Complete3", "fu_start_Complete3a",
    "fu_start_Complete3b", "fu_outpost1", "fu_outpost2",
    "fu_byosftldrive-makeSTL", "fu_byosftldrive-getErchius1",
    "fu_byosftldrive-getErchius2", "fu_byosftldrive-getErchius3",
    "fu_byosftldrive-makeFTL",
]
COLOR_TAG_RE = re.compile(r"\^([A-Za-z][A-Za-z0-9_-]*|reset);")
# ASCII-only word boundaries still match numbers immediately following Japanese.
NUMBER_RE = re.compile(r"(?<![A-Za-z0-9_])[-+]?\d+(?:[.,]\d+)*(?:%|s)?")
KEY_RE = re.compile(r"\[(?:Shift|Mouse\s+\d+|[A-Za-z0-9])\]", re.IGNORECASE)
PLACEHOLDER_RE = re.compile(r"\{[^{}\r\n]+\}|%[sdif]")
JAPANESE_RE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def lf_normalized_sha256(data: bytes) -> str:
    """Hash a text source after normalizing CRLF to the pinned LF representation."""
    return sha256(data.replace(b"\r\n", b"\n"))


def hash_tree(directory: Path) -> dict[str, str]:
    """Hash regular files using MOD-relative paths; refuse symlinks and special files."""
    directory = Path(directory).resolve()
    if not directory.is_dir():
        raise ValueError(f"MOD directory does not exist: {directory}")
    result = {}
    for path in directory.rglob("*"):
        if path.is_symlink():
            raise ValueError("MOD tree contains a symlink: " + path.relative_to(directory).as_posix())
        if path.is_file():
            relative = path.relative_to(directory).as_posix()
            result[relative] = sha256(path.read_bytes())
        elif not path.is_dir():
            raise ValueError("MOD tree contains a non-file entry: " + path.relative_to(directory).as_posix())
    return dict(sorted(result.items()))


def compare_inventory(expected: dict[str, str], baseline: dict[str, str],
                      candidate: dict[str, str], allowed_changes: set[str]) -> dict[str, Any]:
    baseline_matches_fixture = baseline == expected
    same_file_set = set(baseline) == set(candidate)
    changed = sorted(name for name in set(baseline) & set(candidate)
                     if baseline[name] != candidate[name])
    added = sorted(set(candidate) - set(baseline))
    removed = sorted(set(baseline) - set(candidate))
    unexpected = sorted(set(changed) - allowed_changes)
    return {
        "baseline_matches_fixture": baseline_matches_fixture,
        "same_file_set": same_file_set,
        "baseline_file_count": len(baseline),
        "candidate_file_count": len(candidate),
        "changed_paths": changed,
        "added_paths": added,
        "removed_paths": removed,
        "unexpected_changed_paths": unexpected,
        "changed_paths_within_allowlist": not unexpected and not added and not removed,
    }


def type_sensitive_equal(left: Any, right: Any) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            type_sensitive_equal(left[key], right[key]) for key in left)
    if isinstance(left, list):
        return len(left) == len(right) and all(
            type_sensitive_equal(a, b) for a, b in zip(left, right))
    return left == right


def strict_apply(document: Any, operations: list[Any],
                 allowed_duplicate_pairs: dict[int, int] | None = None) -> tuple[Any, dict[str, Any]]:
    """Apply test groups; tolerate only configured exact duplicates that are no-ops."""
    result = copy.deepcopy(document)
    failed = []
    tolerated_duplicates = []
    applied = 0
    allowed_duplicate_pairs = allowed_duplicate_pairs or {}
    for index, item in enumerate(operations):
        group = item if isinstance(item, list) else [item]
        try:
            result = apply_batches(result, group)
            applied += 1
        except (TestFailed, KeyError, IndexError, TypeError, ValueError) as error:
            duplicate_of = allowed_duplicate_pairs.get(index)
            prior = operations[duplicate_of] if duplicate_of is not None and duplicate_of < index else None
            prior_group = prior if isinstance(prior, list) else ([prior] if prior is not None else None)
            if prior_group is not None and type_sensitive_equal(group, prior_group):
                writes = [operation for operation in group
                          if isinstance(operation, dict) and operation.get("op") != "test"]
                try:
                    reapplied = apply_batches(copy.deepcopy(result), writes)
                except (TestFailed, KeyError, IndexError, TypeError, ValueError):
                    reapplied = None
                if reapplied is not None and type_sensitive_equal(reapplied, result):
                    tolerated_duplicates.append({"group_index": index, "duplicate_of": duplicate_of})
                    continue
            paths = [op.get("path") for op in group if isinstance(op, dict) and op.get("op") == "test"]
            failed.append({"group_index": index, "test_paths": paths,
                           "error_type": type(error).__name__})
    return result, {"group_count": len(operations), "applied_group_count": applied,
                    "failed_group_count": len(failed), "failed_groups": failed,
                    "tolerated_duplicate_groups": tolerated_duplicates,
                    "tolerated_duplicate_group_count": len(tolerated_duplicates)}


def compose_asset(base_pak: str, layers: list[tuple[str, Path]], asset: str) -> Any:
    sources = [index_basis.AssetLayer("base", base_pak)]
    sources.extend(index_basis.AssetLayer(name, path) for name, path in layers)
    try:
        document = None
        for source in sources:
            raw = source.read(asset)
            patch_raw = source.read(asset + ".patch")
            if raw is not None:
                document = index_basis.parse_asset(raw)
            if patch_raw is not None:
                if document is None:
                    raise ValueError(f"Layer patch has no lower-priority base for {asset}")
                document = apply_batches(document, index_basis.parse_asset(patch_raw))
        if document is None:
            raise ValueError("No effective source asset found: " + asset)
        return document
    finally:
        for source in sources:
            source.close()


def strict_json_equal(left: Any, right: Any) -> bool:
    return type_sensitive_equal(left, right)


def verify_indexed_assets(mod: Path, inputs_path: Path, expected_fixture: dict[str, Any]):
    base_pak, layers = index_basis.load_inputs(inputs_path)
    checks = {}
    details = []
    for expected in expected_fixture["assets"]:
        asset = expected["asset"]
        patch_path = expected["patch_path"]
        patch_file = mod / Path(*Path(patch_path).parts)
        if not patch_file.is_file():
            checks[asset] = False
            details.append({"asset": asset, "passed": False, "reason": "patch_missing"})
            continue
        operations = index_basis.parse_asset(patch_file.read_bytes())
        group_count_ok = len(operations) == expected["groups"]
        original = compose_asset(base_pak, layers, asset)
        allowed_duplicates = ({3: 0, 4: 1}
                              if asset in {
                                  "npcs/crew/crewmemberengineer.npctype",
                                  "npcs/crew/crewmembermechanic.npctype",
                              } else {})
        final, application = strict_apply(original, operations, allowed_duplicates)
        final_hash = index_basis.asset_hash(final)
        passed = (group_count_ok and application["failed_group_count"] == 0 and
                  final_hash == expected["output_sha256"])
        checks[asset] = passed
        details.append({
            "asset": asset,
            "patch_path": patch_path,
            "expected_group_count": expected["groups"],
            "actual_group_count": len(operations),
            "applied_group_count": application["applied_group_count"],
            "failed_group_count": application["failed_group_count"],
            "failed_groups": application["failed_groups"],
            "tolerated_duplicate_groups": application["tolerated_duplicate_groups"],
            "expected_final_json_sha256": expected["output_sha256"],
            "actual_final_json_sha256": final_hash,
            "passed": passed,
        })
    return checks, details


def token_sequences(text: str) -> dict[str, list[str]]:
    return {
        "color_tags": COLOR_TAG_RE.findall(text),
        "numbers": NUMBER_RE.findall(text),
        "keyboard_keys": KEY_RE.findall(text),
        "placeholders": PLACEHOLDER_RE.findall(text),
    }


def verify_radio(original: dict[str, Any], operations: list[Any], baseline_fixture: dict[str, Any]):
    translated, application = strict_apply(original, operations)
    expected_keys = set(RADIO_MESSAGE_KEYS)
    key_set_matches = set(original) == expected_keys and set(translated) == expected_keys
    target_keys = set(baseline_fixture["targeted_untranslated_keys"])
    successful_hashes = baseline_fixture["successful_text_sha256"]
    japanese = {key: bool(JAPANESE_RE.search(translated.get(key, {}).get("text", "")))
                for key in RADIO_MESSAGE_KEYS}
    targeted = {key: key in translated and translated[key].get("text") != original[key].get("text")
                and japanese[key] for key in sorted(target_keys)}
    prior_success = {
        key: sha256(translated[key]["text"].encode("utf-8")) == expected_hash
        for key, expected_hash in successful_hashes.items()
        if key in translated and isinstance(translated[key].get("text"), str)
    }
    controls = {}
    token_checks = {}
    for key in RADIO_MESSAGE_KEYS:
        before_fields = {k: v for k, v in original[key].items() if k not in {"text", "senderName"}}
        after_fields = {k: v for k, v in translated[key].items() if k not in {"text", "senderName"}}
        controls[key] = strict_json_equal(before_fields, after_fields)
        before_tokens = token_sequences(original[key]["text"])
        after_tokens = token_sequences(translated[key]["text"])
        token_checks[key] = {name: before_tokens[name] == after_tokens[name]
                             for name in before_tokens}
    checks = {
        "radio_source_has_26_expected_bodies": len(original) == 26 and key_set_matches,
        "radio_baseline_lists_expected_10_target_keys": target_keys == set(TARGETED_RADIO_KEYS),
        "all_radio_patch_groups_pass_tests": application["failed_group_count"] == 0,
        "all_26_bodies_have_japanese_text": all(japanese.values()),
        "all_10_targeted_bodies_improved": len(targeted) == 10 and all(targeted.values()),
        "old_16_successful_translations_unchanged": len(prior_success) == 16 and all(prior_success.values()),
        "radio_control_fields_unchanged": all(controls.values()),
        "radio_color_tags_numbers_keys_placeholders_unchanged": all(
            ok for per_message in token_checks.values() for ok in per_message.values()),
    }
    return translated, application, checks, {
        "message_count": len(original),
        "targeted_keys": sorted(target_keys),
        "targeted_status": targeted,
        "old_successful_count": len(successful_hashes),
        "old_successful_translation_status": prior_success,
        "failed_patch_groups": application["failed_groups"],
        "controls_unchanged": controls,
        "token_checks": token_checks,
        "checks": checks,
    }


def check_metadata(baseline_mod: Path, mod: Path):
    baseline_metadata = json.loads((baseline_mod / "_metadata").read_text(encoding="utf-8-sig"))
    current_metadata = json.loads((mod / "_metadata").read_text(encoding="utf-8-sig"))
    stable_fields = ("name", "includes", "requires", "priority")
    stable = {field: type_sensitive_equal(baseline_metadata.get(field), current_metadata.get(field))
              for field in stable_fields}
    attribution = (mod / "ATTRIBUTION.txt").read_text(encoding="utf-8")
    return {
        "baseline_version": baseline_metadata.get("version"),
        "candidate_version": current_metadata.get("version"),
        "version_is_0_2_4_fu6_5_8": current_metadata.get("version") == EXPECTED_VERSION,
        "stable_metadata_fields": stable,
        "stable_metadata_fields_unchanged": all(stable.values()),
        "attribution_has_17868_commit": "17868d86c9bb7bc00f92038fb78b48cebd1b41b8" in attribution,
        "attribution_has_1c80_commit": "1c80b714c8b7da9ce3d35f237850ffdb236b9a2e" in attribution,
    }


def verify_release(baseline_mod: Path, mod: Path, inputs_path: Path):
    baseline_fixture = json.loads(BASELINE_FIXTURE.read_text(encoding="utf-8"))
    append_fixture = json.loads(APPEND_FIXTURE.read_text(encoding="utf-8"))
    radio_fixture = json.loads(RADIO_FIXTURE.read_text(encoding="utf-8"))
    expected_inventory = baseline_fixture["files"]
    baseline_inventory = hash_tree(baseline_mod)
    candidate_inventory = hash_tree(mod)

    indexed_paths = {item["patch_path"] for item in append_fixture["assets"]}
    allowed = indexed_paths | {RADIO_ASSET + ".patch", "_metadata", "ATTRIBUTION.txt"}
    inventory = compare_inventory(expected_inventory, baseline_inventory, candidate_inventory, allowed)

    append_checks, append_details = verify_indexed_assets(mod, inputs_path, append_fixture)
    radio_raw = None
    base_pak, layers = index_basis.load_inputs(inputs_path)
    for name, layer_path in layers:
        if name == "fu":
            layer = index_basis.AssetLayer(name, layer_path)
            try:
                radio_raw = layer.read(RADIO_ASSET)
            finally:
                layer.close()
            break
    if radio_raw is None:
        raise ValueError("append-basis input has no readable official FU radio asset layer")
    radio_original = index_basis.parse_asset(radio_raw)
    radio_patch_path = mod / Path(*Path(RADIO_ASSET + ".patch").parts)
    radio_operations = index_basis.parse_asset(radio_patch_path.read_bytes())
    _radio_final, radio_application, radio_checks, radio_detail = verify_radio(
        radio_original, radio_operations, radio_fixture)
    radio_normalized_sha = lf_normalized_sha256(radio_raw)
    radio_checks["official_radio_layer_matches_fixed_sha256"] = (
        radio_normalized_sha == radio_fixture["official_sha256"])
    radio_detail.update({
        "official_commit": radio_fixture["official_commit"],
        "official_radio_layer_raw_sha256": sha256(radio_raw),
        "official_radio_layer_lf_normalized_sha256": radio_normalized_sha,
        "official_sha256_representation": radio_fixture["official_sha256_representation"],
        "line_ending_note": "Installed source raw SHA and pinned commit LF SHA may differ; CRLF is normalized to LF for the commit-blob check.",
        "baseline_patch_sha256": radio_fixture["baseline_patch_sha256"],
        "baseline_success_text_sha256": radio_fixture["successful_text_sha256"],
    })

    metadata = check_metadata(baseline_mod, mod)
    checks = {
        "baseline_file_count_is_14526": baseline_fixture["expected_file_count"] == 14526 and
        len(expected_inventory) == 14526,
        "baseline_inventory_matches_git_head_fixture": inventory["baseline_matches_fixture"],
        "file_set_unchanged": inventory["same_file_set"],
        "only_20_indexed_patches_radio_metadata_attribution_changed": inventory["changed_paths_within_allowlist"],
        "all_20_indexed_assets_match_expected_output": len(append_checks) == 20 and all(append_checks.values()),
        **{f"append_asset:{key}": value for key, value in append_checks.items()},
        **metadata,
        **radio_checks,
    }
    return {
        "schema": "fu-japanese-release-024-validation-v1",
        "passed": all(value for value in checks.values() if isinstance(value, bool)),
        "mod_version": metadata["candidate_version"],
        "scope": "targeted regeneration + whole MOD byte preservation",
        "baseline_git_head": baseline_fixture["source_git_head"],
        "baseline_source_manifest_sha256": baseline_fixture["source_manifest_sha256"],
        "full_fu_source_reapplied": False,
        "native_game_executed": False,
        "commercial_source_bytes_saved": False,
        "checks": checks,
        "baseline_inventory": inventory,
        "changed_path_allowlist": sorted(allowed),
        "append_basis_inputs_sha256": sha256(inputs_path.read_bytes()),
        "append_expectations": {
            "fixture": str(APPEND_FIXTURE.relative_to(ROOT)),
            "source_comparison_sha256": append_fixture["source_comparison_sha256"],
            "assets": append_details,
        },
        "radio_verification": radio_detail,
        "metadata": metadata,
        "limitations": [
            "Only 20 selected assets were composed from the configured real asset layers.",
            "The complete Frackin' Universe source checkout was unavailable and was not reapplied.",
            "The game was not launched; runtime rendering and behavior remain unverified.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-mod", type=Path, required=True,
                        help="Unmodified 0.2.3 MOD snapshot matching the fixed git-HEAD SHA fixture")
    parser.add_argument("--mod", type=Path, required=True, help="Generated 0.2.4 MOD directory")
    parser.add_argument("--append-basis-inputs", type=Path, required=True,
                        help="JSON describing the actual base PAK and ordered installed asset layers")
    args = parser.parse_args()
    reports = ROOT / "source" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    try:
        actual_hashes = hash_tree(args.mod)
        (reports / "mod_sha256.json").write_text(
            json.dumps(actual_hashes, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    except Exception as error:
        actual_hashes = None
        (reports / "mod_sha256.json").write_text("{}\n", encoding="utf-8", newline="\n")
        hash_error = f"{type(error).__name__}: {error}"
    else:
        hash_error = None
    try:
        report = verify_release(args.baseline_mod, args.mod, args.append_basis_inputs)
    except Exception as error:
        report = {
            "schema": "fu-japanese-release-024-validation-v1",
            "passed": False,
            "mod_version": EXPECTED_VERSION,
            "scope": "targeted regeneration + whole MOD byte preservation",
            "full_fu_source_reapplied": False,
            "native_game_executed": False,
            "commercial_source_bytes_saved": False,
            "fatal_error": f"{type(error).__name__}: {error}",
            "mod_sha256_generated": actual_hashes is not None,
            "mod_sha256_error": hash_error,
        }
    (reports / "validation.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"passed": report.get("passed", False),
                      "validation": str(reports / "validation.json"),
                      "mod_sha256": str(reports / "mod_sha256.json"),
                      "checks": report.get("checks", {}),
                      "fatal_error": report.get("fatal_error")}, ensure_ascii=False, indent=2))
    return 0 if report.get("passed") else 1


if __name__ == "__main__":
    raise SystemExit(main())
