#!/usr/bin/env python3
"""Check safe folder-copy upgrades that restore native character name data.

The tests copy actual release MOD folders into temporary directories, overlay
the proposed new folder, and resolve the two Markov source references against
four fixed official FU data files. They do not run Starbound or its Markov
algorithm. No installed game or save data is read or modified.

Example from the release's source directory:
  python tools/test_namegen_upgrade.py --mod ../mods/FU_Japanese \
    --baseline-mod /path/to/FU_Japanese_0.2.0/mods/FU_Japanese \
    --previous-mod /path/to/FU_Japanese_0.2.1/mods/FU_Japanese \
    --recent-mod /path/to/FU_Japanese_0.2.2/mods/FU_Japanese \
    --fixtures tests/namegen_fixtures --report reports/namegen_upgrade.json
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest


SOURCES = ('elduukharmale', 'elduukharfemale')
BAD_IDS = {
    'elduukharmale': 'エル・デュカ・マール',
    'elduukharfemale': 'エルドゥカー・メス',
}
FIXTURE_HASHES = {
    'species/elduukharmalenamegen.config':
        'e2fe9398ba589f4e080d4dfe010cae1bcc497e710299a8638b0c508ff398494d',
    'species/elduukharfemalenamegen.config':
        '0845bbe817eb0ba9303abb83572d81d8cb57e630c819f640657649ee9a178bb7',
    'names/elduukharmale.namesource':
        'bf214789dd44ee5196e32d0adff8851736a1d9f7ecbc6e1965196284d307402c',
    'names/elduukharfemale.namesource':
        '7e273ef47fc9cf748d9c702cf0f33fca0db1e199b521203c54f2a1718090b77e',
}
ARGS = None
METRICS = {}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def manifest(directory):
    return {p.relative_to(directory).as_posix(): digest(p.read_bytes())
            for p in sorted(directory.rglob('*')) if p.is_file()}


def fixture(relative):
    raw = (ARGS.fixtures / relative).read_bytes()
    if digest(raw) != FIXTURE_HASHES[relative]:
        raise AssertionError('Official fixture changed: ' + relative)
    # These exact hash-pinned FU files have at most one block comment.
    # This is deliberately not a general relaxed-JSON parser.
    return json.loads(re.sub(r'/\*.*?\*/', '', raw.decode(), flags=re.S))


def resolve(document, parts):
    for part in parts:
        document = document[int(part)] if isinstance(document, list) else document[part]
    return document


def patched(document, patch_file):
    result = copy.deepcopy(document)
    if not patch_file.exists():
        return result
    groups = json.loads(patch_file.read_text(encoding='utf-8'))
    if not isinstance(groups, list):
        raise AssertionError('Name-data patch must be a JSON array')
    for group in groups:
        if not isinstance(group, list) or len(group) != 2:
            raise AssertionError('Only these fixture test/replace pairs are supported')
        test, replacement = group
        if (test.get('op') != 'test' or replacement.get('op') != 'replace'
                or test.get('path') != replacement.get('path') or 'value' not in test):
            raise AssertionError('Unexpected fixture mutation')
        parts = [part.replace('~1', '/').replace('~0', '~')
                 for part in test['path'].split('/')[1:]]
        if resolve(result, parts) != test['value']:
            continue
        parent = resolve(result, parts[:-1])
        key = int(parts[-1]) if isinstance(parent, list) else parts[-1]
        parent[key] = copy.deepcopy(replacement['value'])
    return result


def references(value):
    if isinstance(value, dict):
        if value.get('mode') == 'markov':
            yield value['source']
        for child in value.values():
            yield from references(child)
    elif isinstance(value, list):
        for child in value:
            yield from references(child)


def source_registry(mod):
    result = {}
    for name in SOURCES:
        value = patched(fixture(f'names/{name}.namesource'),
                        mod / f'names/{name}.namesource.patch')
        result[value['name']] = value
    return result


def generator(mod, name):
    return patched(fixture(f'species/{name}namegen.config'),
                   mod / f'species/{name}namegen.config.patch')


class OverlayUpgradeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for folder in (ARGS.baseline_mod, ARGS.mod):
            if not folder.is_dir():
                raise AssertionError('Missing MOD directory: ' + str(folder))
        cls.candidate_manifest = manifest(ARGS.mod)
        retired_file = ARGS.mod.parent.parent / 'source/source/retired_character_name_assets.json'
        cls.retired_assets = json.loads(retired_file.read_text(encoding='utf-8'))
        old_name_assets = {p.relative_to(ARGS.baseline_mod).as_posix()[:-6]
                           for p in ARGS.baseline_mod.rglob('*.patch')
                           if p.name.endswith('.namesource.patch') or
                           p.parent == ARGS.baseline_mod / 'species' and p.name.endswith('namegen.config.patch')}
        if set(cls.retired_assets) != old_name_assets or len(cls.retired_assets) != 32:
            raise AssertionError('Retired assets must cover all 32 original character name patches')

    def assert_resolved_controls(self, mod):
        registry = source_registry(mod)
        self.assertEqual(set(registry), set(SOURCES))
        for name in SOURCES:
            with self.subTest(source=name):
                value = generator(mod, name)
                self.assertEqual(value, fixture(f'species/{name}namegen.config'))
                self.assertEqual(list(references(value)), [name])
                self.assertIn(name, registry)
                self.assertEqual(registry[name], fixture(f'names/{name}.namesource'))

    def test_compatibility_files_are_present_and_empty(self):
        for asset in self.retired_assets:
            path = ARGS.mod / (asset + '.patch')
            with self.subTest(path=path.name):
                self.assertTrue(path.is_file(), 'The legacy filename must be overwritten')
                self.assertEqual(json.loads(path.read_text(encoding='utf-8')), [])
        METRICS['empty_compatibility_patches'] = len(self.retired_assets)

    def test_old_payload_contains_both_confirmed_bad_references(self):
        registry = source_registry(ARGS.baseline_mod)
        for name in SOURCES:
            with self.subTest(source=name):
                actual = list(references(generator(ARGS.baseline_mod, name)))
                self.assertEqual(actual, [BAD_IDS[name]])
                self.assertNotIn(actual[0], registry)
        METRICS['old_invalid_references_reproduced'] = 2

    def overlay_and_check(self, baseline, label):
        with tempfile.TemporaryDirectory(prefix='fu_namegen_upgrade_') as temporary:
            destination = Path(temporary) / 'FU_Japanese'
            shutil.copytree(baseline, destination)
            shutil.copytree(ARGS.mod, destination, dirs_exist_ok=True)
            observed = manifest(destination)
            self.assertEqual(observed, self.candidate_manifest,
                             'Overlay left stale release files or changed copied content')
            self.assertEqual(len(observed), len({p.casefold() for p in observed}),
                             'Windows paths must not collide after case folding')
            self.assertEqual([p.relative_to(destination).as_posix()
                              for p in destination.rglob('_metadata')], ['_metadata'])
            self.assert_resolved_controls(destination)
            for asset in self.retired_assets:
                self.assertEqual(json.loads((destination / (asset + '.patch')).read_text()), [])
            METRICS[f'overlay_{label}_files_verified'] = len(observed)
            METRICS[f'overlay_{label}_source_references_resolved'] = 2

    def test_overlay_actual_020_folder(self):
        self.overlay_and_check(ARGS.baseline_mod, '020')

    def test_overlay_actual_021_folder(self):
        if ARGS.previous_mod is None:
            self.skipTest('--previous-mod not supplied')
        self.overlay_and_check(ARGS.previous_mod, '021')

    def test_overlay_actual_022_folder(self):
        if ARGS.recent_mod is None:
            self.skipTest('--recent-mod not supplied')
        self.overlay_and_check(ARGS.recent_mod, '022')

    def test_removal_only_previous_upgrade_leaves_old_references(self):
        if ARGS.previous_mod is None:
            self.skipTest('--previous-mod not supplied')
        # A minimal copy models exactly the omitted-file behavior that the new
        # two explicit empty files address; it does not infer user actions.
        relatives = [f'species/{name}namegen.config.patch' for name in SOURCES]
        with tempfile.TemporaryDirectory(prefix='fu_removed_file_upgrade_') as temporary:
            destination = Path(temporary) / 'FU_Japanese'
            for folder in (ARGS.baseline_mod, ARGS.previous_mod):
                for relative in relatives:
                    source = folder / relative
                    if source.exists():
                        target = destination / relative
                        target.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source, target)
            for name in SOURCES:
                self.assertEqual(list(references(generator(destination, name))), [BAD_IDS[name]])
        METRICS['removal_only_overlay_stale_references'] = 2

    def test_name_material_and_generator_settings_are_preserved(self):
        registry = source_registry(ARGS.mod)
        total = 0
        for name in SOURCES:
            before = fixture(f'names/{name}.namesource')
            after = registry[name]
            self.assertEqual({k: v for k, v in before.items() if k != 'sourceNames'},
                             {k: v for k, v in after.items() if k != 'sourceNames'})
            self.assertEqual(len(before['sourceNames']), len(after['sourceNames']))
            for first, last in zip(before['sourceNames'], after['sourceNames']):
                self.assertEqual(first.encode('utf-8'), last.encode('utf-8'))
                total += 1
        self.assertEqual(total, 114)
        self.assert_resolved_controls(ARGS.mod)
        METRICS['original_training_words_preserved'] = total

    def test_startup_metadata_keeps_optional_fu_ordering(self):
        meta = json.loads((ARGS.mod / '_metadata').read_text())
        self.assertEqual(meta['name'], 'FUJapaneseTranslation2026')
        self.assertEqual(meta['requires'], [])
        self.assertEqual(meta['includes'], ['FrackinUniverse'])
        self.assertEqual(meta['priority'], 1000)
        self.assertEqual(meta['version'], '0.2.3-fu6.5.8')


def main():
    global ARGS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mod', required=True, type=Path)
    parser.add_argument('--baseline-mod', required=True, type=Path)
    parser.add_argument('--previous-mod', type=Path)
    parser.add_argument('--recent-mod', type=Path)
    parser.add_argument('--fixtures', required=True, type=Path)
    parser.add_argument('--report', type=Path)
    ARGS = parser.parse_args()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(OverlayUpgradeTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {
        'passed': result.wasSuccessful(), 'tests_run': result.testsRun,
        'failures': len(result.failures), 'errors': len(result.errors),
        'skipped': len(result.skipped), 'runtime_tested': False,
        'scope': 'Actual release folder overlays, 32 obsolete translations replaced by no-op patches, file identities, pinned FU source-reference resolution and original training-word preservation. Does not execute Starbound or its Markov generation algorithm.',
        'metrics': METRICS, 'upstream_fixture_sha256': FIXTURE_HASHES,
        'candidate_mod_manifest_sha256': digest(json.dumps(
            manifest(ARGS.mod), sort_keys=True, separators=(',', ':')).encode()),
        'limits': [
            'An overlay into one existing FU_Japanese folder is tested; a separate older copy in another mods folder is not removed by this package.',
            'The uploaded log confirms an invalid female source reference but does not identify the installed translation version or how old data remained active.',
        ],
    }
    if ARGS.report:
        ARGS.report.parent.mkdir(parents=True, exist_ok=True)
        ARGS.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
