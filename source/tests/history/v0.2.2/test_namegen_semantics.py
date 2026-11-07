#!/usr/bin/env python3
"""Regress the 0.2.0 Elduukhar name-source-ID startup failure.

These tests check data semantics and the build-time safety policy.  They do not
run Starbound or emulate its Markov generator.  The four upstream fixtures are
small, pinned FU assets; their attribution is in fixtures/provenance.json.

Example after integration into a release's source folder::

    python tools/test_namegen_semantics.py --project . \
        --mod ../mods/FU_Japanese --fixtures tests/namegen_fixtures \
        --report reports/namegen_regression.json
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import unittest


EXPECTED_FIXTURE_HASHES = {
    "species/elduukharmalenamegen.config":
        "e2fe9398ba589f4e080d4dfe010cae1bcc497e710299a8638b0c508ff398494d",
    "species/elduukharfemalenamegen.config":
        "0845bbe817eb0ba9303abb83572d81d8cb57e630c819f640657649ee9a178bb7",
    "names/elduukharmale.namesource":
        "bf214789dd44ee5196e32d0adff8851736a1d9f7ecbc6e1965196284d307402c",
    "names/elduukharfemale.namesource":
        "7e273ef47fc9cf748d9c702cf0f33fca0db1e199b521203c54f2a1718090b77e",
}
SOURCE_IDS = ("elduukharmale", "elduukharfemale")
BROKEN_IDS = {
    "elduukharmale": "エル・デュカ・マール",
    "elduukharfemale": "エルドゥカー・メス",
}
JAPANESE = re.compile(r"[\u3040-\u30ff\u3400-\u9fff]")
OPTIONS = None
METRICS = {}


def pointer_parts(pointer):
    if not pointer.startswith("/"):
        raise ValueError("Expected an absolute JSON pointer")
    return tuple(part.replace("~1", "/").replace("~0", "~")
                 for part in pointer[1:].split("/"))


def resolve(document, parts):
    for part in parts:
        document = document[int(part)] if isinstance(document, list) else document[part]
    return document


def apply_simple_guarded_patch(document, patch_file):
    """Apply only the test/replace pairs present in these name-data patches.

    This small fixture helper intentionally refuses other operations.  It is
    not a reimplementation of the game's complete JSON-patch behavior.
    """
    result = copy.deepcopy(document)
    if not patch_file.exists():
        return result, 0
    groups = json.loads(patch_file.read_text(encoding="utf-8"))
    matched = 0
    for group in groups:
        if not isinstance(group, list) or len(group) != 2:
            raise AssertionError(f"Unexpected name-data patch group: {patch_file}")
        test, replacement = group
        if (test.get("op") != "test" or replacement.get("op") != "replace"
                or test.get("path") != replacement.get("path") or "value" not in test):
            raise AssertionError(f"Unexpected name-data operation: {patch_file}")
        parts = pointer_parts(test["path"])
        try:
            actual = resolve(result, parts)
        except (KeyError, IndexError, TypeError, ValueError):
            continue
        if actual != test["value"]:
            continue
        parent = resolve(result, parts[:-1])
        key = int(parts[-1]) if isinstance(parent, list) else parts[-1]
        parent[key] = copy.deepcopy(replacement["value"])
        matched += 1
    return result, matched


def markov_references(value):
    """Find source references by their semantic 'markov' control object."""
    if isinstance(value, dict):
        if value.get("mode") == "markov":
            yield value["source"]
        for child in value.values():
            yield from markov_references(child)
    elif isinstance(value, list):
        for child in value:
            yield from markov_references(child)


def require_resolved_sources(namegen, sources):
    references = list(markov_references(namegen))
    for reference in references:
        if reference not in sources:
            raise LookupError(f"Unknown name source '{reference}'")
    return references


def fixture(asset):
    raw = (OPTIONS.fixtures / asset).read_bytes()
    actual = hashlib.sha256(raw).hexdigest()
    if actual != EXPECTED_FIXTURE_HASHES[asset]:
        raise AssertionError(f"Pinned upstream fixture changed: {asset}")
    # Only these hash-pinned configs contain one ordinary /* ... */ comment.
    # This deliberately is not a general relaxed-JSON parser for arbitrary FU.
    text = re.sub(r"/\*.*?\*/", "", raw.decode("utf-8"), flags=re.S)
    return json.loads(text)


def load_safety_module():
    path = OPTIONS.project / "tools/namegen_safety.py"
    spec = importlib.util.spec_from_file_location("fu_namegen_safety_under_test", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def relevant_root(asset, parts):
    """Independent asset-schema boundary for scanning shipped mutations."""
    if asset.endswith(".namesource"):
        return "sourceNames"
    if asset == "celestial/names.config" and parts[:1] in {
            ("systemNames",), ("systemSuffixNames",)}:
        return parts[0]
    if (asset.endswith(".config") and asset.startswith(("species/", "items/"))
            and parts[:1] in {("names",), ("nameGen",)}):
        return parts[0]
    return None


class NamegenRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.safety = load_safety_module()
        cls.sources = {source_id: fixture(f"names/{source_id}.namesource")
                       for source_id in SOURCE_IDS}
        cls.generators = {source_id: fixture(f"species/{source_id}namegen.config")
                          for source_id in SOURCE_IDS}

    def test_upstream_references_resolve_to_registered_ids(self):
        for source_id in SOURCE_IDS:
            with self.subTest(source_id=source_id):
                self.assertEqual(self.sources[source_id]["name"], source_id)
                self.assertEqual(require_resolved_sources(self.generators[source_id], self.sources),
                                 [source_id])
                self.assertEqual(len(self.sources[source_id]["sourceNames"]), 57)

    def test_old_release_reproduces_both_unknown_source_errors(self):
        baseline = OPTIONS.baseline_mod or OPTIONS.fixtures / "baseline_020"
        for source_id in SOURCE_IDS:
            with self.subTest(source_id=source_id):
                patch_file = baseline / f"species/{source_id}namegen.config.patch"
                self.assertTrue(patch_file.is_file(), "The actual old patch must be present")
                broken, changes = apply_simple_guarded_patch(self.generators[source_id], patch_file)
                self.assertEqual(changes, 1)
                self.assertEqual(list(markov_references(broken)), [BROKEN_IDS[source_id]])
                with self.assertRaisesRegex(LookupError, re.escape(BROKEN_IDS[source_id])):
                    require_resolved_sources(broken, self.sources)
        METRICS["old_release_unknown_source_errors_reproduced"] = 2

    def test_fixed_generators_keep_control_objects_and_resolve(self):
        translated_sources = {}
        for source_id, original in self.sources.items():
            updated, _ = apply_simple_guarded_patch(
                original, OPTIONS.mod / f"names/{source_id}.namesource.patch")
            translated_sources[updated["name"]] = updated
        self.assertEqual(set(translated_sources), set(SOURCE_IDS))
        for source_id in SOURCE_IDS:
            with self.subTest(source_id=source_id):
                updated, changes = apply_simple_guarded_patch(
                    self.generators[source_id],
                    OPTIONS.mod / f"species/{source_id}namegen.config.patch")
                # These two source generators contain controls, not name words.
                self.assertEqual(changes, 0)
                self.assertEqual(updated, self.generators[source_id])
                self.assertEqual(require_resolved_sources(updated, translated_sources), [source_id])
        METRICS["fixed_source_references_resolved"] = 2

    def test_name_material_remains_japanese_and_metadata_unchanged(self):
        total_changes = 0
        for source_id, original in self.sources.items():
            with self.subTest(source_id=source_id):
                updated, changes = apply_simple_guarded_patch(
                    original, OPTIONS.mod / f"names/{source_id}.namesource.patch")
                self.assertEqual(changes, 57)
                self.assertEqual(len(updated["sourceNames"]), len(original["sourceNames"]))
                self.assertEqual({k: v for k, v in updated.items() if k != "sourceNames"},
                                 {k: v for k, v in original.items() if k != "sourceNames"})
                for before, after in zip(original["sourceNames"], updated["sourceNames"]):
                    self.assertIsInstance(after, str)
                    self.assertNotEqual(before, after)
                    self.assertRegex(after, JAPANESE)
                total_changes += changes
        self.assertEqual(total_changes, 114)
        METRICS["japanese_source_name_entries_preserved"] = total_changes

    def test_reference_ids_and_nested_control_fields_are_rejected(self):
        cases = [
            ("species/elduukharmalenamegen.config", "/names/1/1/0/source"),
            ("species/elduukharfemalenamegen.config", "/names/1/1/0/source"),
            ("species/example.config", "/names/0/mode"),
            ("species/example.config", "/names/0/titleCase"),
            ("species/example.config", "/names/0/targetLength/0"),
            ("items/example.config", "/nameGen/0/source"),
            ("items/example.config", "/nameGen/0/futureControl/0"),
            ("celestial/names.config", "/systemNames/0/mode"),
            ("celestial/names.config", "/systemSuffixNames/0/source"),
            ("names/elduukharmale.namesource", "/name"),
            ("names/elduukharmale.namesource", "/prefixSize"),
            ("names/elduukharfemale.namesource", "/endSize"),
            ("names/example.namesource", "/sourceNames/0/control"),
            ("names/example.namesource", "/sourceNames/0/1"),
            ("names/example.namesource", "/sourceNames"),
        ]
        for asset, pointer in cases:
            with self.subTest(asset=asset, path=pointer):
                parts = pointer_parts(pointer)
                self.assertTrue(self.safety.is_namegen_scope(asset, parts))
                self.assertFalse(self.safety.is_namegen_display_path(asset, parts))
                with self.assertRaises(ValueError):
                    self.safety.assert_safe_namegen_translation(asset, pointer)
        METRICS["protected_field_cases"] = len(cases)

    def test_literal_choices_fragments_and_append_positions_remain_allowed(self):
        cases = [
            ("species/catnamegen.config", "/names/1/1/1"),
            ("species/feneroxnamegen.config", "/names/1/-"),
            ("species/feneroxnamegen.config", "/names/-/1"),
            ("items/active/weapons/ranged/pistol/pistolnames.config", "/nameGen/1/1/5"),
            ("items/active/weapons/ranged/pistol/pistolnames.config", "/nameGen/1/1/-"),
            ("celestial/names.config", "/systemNames/587/1"),
            ("celestial/names.config", "/systemSuffixNames/-/1"),
            ("names/elduukharmale.namesource", "/sourceNames/0"),
            ("names/elduukharfemale.namesource", "/sourceNames/-"),
        ]
        for asset, pointer in cases:
            with self.subTest(asset=asset, path=pointer):
                parts = pointer_parts(pointer)
                self.assertTrue(self.safety.is_namegen_scope(asset, parts))
                self.assertTrue(self.safety.is_namegen_display_path(asset, parts))
                self.safety.assert_safe_namegen_translation(asset, pointer)
        METRICS["allowed_display_field_cases"] = len(cases)

    def test_numeric_control_slots_need_a_same_batch_string_guard(self):
        asset = 'species/example_namegen.config'
        write = {'op': 'replace', 'path': '/names/0', 'value': '名前'}
        cases = [
            [write],
            [{'op': 'add', 'path': '/names/0', 'value': '名前'}],
            [{'op': 'test', 'path': '/names/0'}, write],
            [{'op': 'test', 'path': '/names/0', 'value': {'mode': 'alts'}}, write],
            [{'op': 'test', 'path': '/names/0', 'value': 'Name', 'inverse': True}, write],
            [[{'op': 'test', 'path': '/names/0', 'value': 'Name'}], write],
            [{'op': 'test', 'path': '/names/1', 'value': 'Name'}, write],
        ]
        for patch in cases:
            with self.subTest(patch=patch), self.assertRaises(ValueError):
                self.safety.assert_safe_namegen_patch(asset, patch)
        self.safety.assert_safe_namegen_patch(asset, [[
            {'op': 'test', 'path': '/names/0', 'value': 'Name'}, write]])
        METRICS['unguarded_or_wrongly_guarded_slot_cases'] = len(cases)

    def test_patch_guard_allows_reference_checks_but_rejects_control_writes(self):
        asset = "species/example_namegen.config"
        safe = [[
            {"op": "test", "path": "/names/0/source", "value": "source_id"},
            {"op": "test", "path": "/names/1", "value": "Name"},
            {"op": "replace", "path": "/names/1", "value": "名前"},
        ]]
        self.safety.assert_safe_namegen_patch(asset, safe)
        unsafe = [
            {"op": "replace", "path": "/names/0/source", "value": "参照名"},
            {"op": "replace", "path": "/names/0", "value": {"mode": "alts"}},
            {"op": "replace", "path": "/names", "value": ["名前"]},
            {"op": "add", "path": "/names/1", "value": ["名前"]},
            {"op": "remove", "path": "/names/1"},
            {"op": "move", "from": "/names/0/source", "path": "/names/1"},
            {"op": "copy", "from": "/names/0/source", "path": "/names/1"},
        ]
        for operation in unsafe:
            with self.subTest(operation=operation):
                with self.assertRaises(ValueError):
                    self.safety.assert_safe_namegen_patch(asset, [[operation]])
        METRICS["protected_patch_mutation_cases"] = len(unsafe)

    def test_unrelated_display_fields_are_outside_namegen_policy(self):
        for asset, pointer in [
                ("items/example.item", "/description"),
                ("dialog/example.config", "/converse/human/0"),
                ("interface/example.config", "/gui/name/value")]:
            with self.subTest(asset=asset, path=pointer):
                self.assertFalse(self.safety.is_namegen_scope(asset, pointer_parts(pointer)))
                self.safety.assert_safe_namegen_translation(asset, pointer)

    def test_no_shipped_name_patch_mutates_a_control_field(self):
        scanned = 0
        for patch in sorted(OPTIONS.mod.rglob("*.patch")):
            asset = patch.relative_to(OPTIONS.mod).as_posix()[:-6]
            if not (asset.endswith(".namesource") or asset == "celestial/names.config"
                    or asset.startswith(("species/", "items/")) and asset.endswith(".config")):
                continue
            groups = json.loads(patch.read_text(encoding="utf-8"))
            pending = list(groups)
            while pending:
                operation = pending.pop()
                if isinstance(operation, list):
                    pending.extend(operation)
                    continue
                if operation.get("op") == "test":
                    continue
                parts = pointer_parts(operation["path"])
                root = relevant_root(asset, parts)
                if root is None:
                    continue
                scanned += 1
                with self.subTest(asset=asset, path=operation["path"]):
                    self.assertEqual(operation["op"], "replace")
                    self.assertEqual(parts[0], root)
                    self.assertGreater(len(parts), 1)
                    # Every component below a name-list root must select an
                    # array entry; a dictionary field denotes generator logic.
                    self.assertTrue(all(p.isascii() and p.isdigit() for p in parts[1:]))
                    if asset.endswith(".namesource"):
                        self.assertEqual(len(parts), 2)
                    self.assertIsInstance(operation["value"], str)
        self.assertGreater(scanned, 1000, "Scan must cover the shipped name translations")
        METRICS["shipped_name_display_mutations_examined"] = scanned

    def test_catalogs_do_not_reintroduce_source_id_translations(self):
        examined = 0
        for filename in ("catalog.jsonl", "translated_catalog.jsonl",
                         "append_catalog.jsonl", "append_translated_catalog.jsonl"):
            path = OPTIONS.project / "source" / filename
            self.assertTrue(path.is_file(), f"Missing release catalog: {filename}")
            for line in path.read_text(encoding="utf-8").splitlines():
                row = json.loads(line)
                parts = pointer_parts(row["path"])
                if relevant_root(row["asset"], parts) is None:
                    continue
                examined += 1
                with self.subTest(catalog=filename, asset=row["asset"], path=row["path"]):
                    self.safety.assert_safe_namegen_translation(row["asset"], row["path"])
                    self.assertNotIn("source", parts[1:])
                    self.assertNotIn("mode", parts[1:])
                    self.assertNotIn(row["source"], SOURCE_IDS)
        self.assertGreater(examined, 1000)
        METRICS["name_catalog_rows_examined"] = examined


def main():
    global OPTIONS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, required=True,
                        help="Release source directory containing tools and source")
    parser.add_argument("--mod", type=Path, required=True, help="Candidate FU_Japanese directory")
    parser.add_argument("--fixtures", type=Path, default=Path(__file__).parent / "fixtures")
    parser.add_argument("--baseline-mod", type=Path,
                        help="Optional original 0.2.0 MOD; defaults to the two preserved old patches")
    parser.add_argument("--report", type=Path)
    OPTIONS = parser.parse_args()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NamegenRegressionTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        "passed": result.wasSuccessful(),
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "runtime_tested": False,
        "scope": "Pinned FU fixture reference resolution, generator-control preservation, "
                 "Japanese name-material preservation, source catalogs and shipped mutation paths. "
                 "Does not execute Starbound or simulate Markov name output.",
        "metrics": METRICS,
        "upstream_fixture_sha256": EXPECTED_FIXTURE_HASHES,
    }
    if OPTIONS.report:
        OPTIONS.report.parent.mkdir(parents=True, exist_ok=True)
        OPTIONS.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                                  encoding="utf-8")
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
