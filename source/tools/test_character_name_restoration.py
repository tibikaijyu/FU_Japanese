#!/usr/bin/env python3
"""Verify restoration of native character-name rules and Markov training data.

This checks fixed data and a necessary input condition in Kawa's independent
SBCharCreator: a sample's UTF-16 length minus prefixSize must not be negative.
It neither executes nor emulates Starbound's native name generator, and passing
does not establish the cause or resolution of an in-game freeze.

Requires the release build requirements (pyjson5) for FU's commented JSON.
All upstream fixtures are from the official pinned FU repository; their URLs
and SHA-256 hashes are in upstream_sources.json. No independent-generator code
is required or copied into this test.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest


OPTIONS = None
METRICS = {}
SOURCES = ('elduukharfemale', 'elduukharmale')
EXPECTED_SHORT = {
    ('elduukharfemale', 'KYRA', '京'),
    ('elduukharfemale', 'KYURU', '菊'),
    ('elduukharfemale', 'KYRU', '京'),
    ('elduukharfemale', 'ORI', '織'),
    ('elduukharmale', 'KYURU', '菊'),
    ('elduukharmale', 'KYRU', '京'),
    ('elduukharmale', 'VERNIN', '春'),
    ('elduukharmale', 'ORI', '織'),
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def utf16_units(value):
    return len(value.encode('utf-16-le')) // 2


def references(value):
    if isinstance(value, dict):
        if value.get('mode') == 'markov':
            yield value['source']
        for child in value.values():
            yield from references(child)
    elif isinstance(value, list):
        for child in value:
            yield from references(child)


def apply_display_pairs(document, path):
    """Apply only these known test/replace-pair patches or a no-op array."""
    result = copy.deepcopy(document)
    groups = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(groups, list):
        raise AssertionError('Patch must be an array')
    for group in groups:
        if not isinstance(group, list) or len(group) != 2:
            raise AssertionError('Unexpected operation shape in fixed fixture patch')
        test, change = group
        if test['op'] != 'test' or change['op'] != 'replace' or test['path'] != change['path']:
            raise AssertionError('Unexpected operation in fixed fixture patch')
        parts = [p.replace('~1', '/').replace('~0', '~') for p in test['path'].split('/')[1:]]
        parent = result
        for part in parts[:-1]:
            parent = parent[int(part)] if isinstance(parent, list) else parent[part]
        key = int(parts[-1]) if isinstance(parent, list) else parts[-1]
        if parent[key] == test['value']:
            parent[key] = copy.deepcopy(change['value'])
    return result


class CharacterNameRestorationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(OPTIONS.project/'tools'))
        from common import read_asset
        cls.read_asset = staticmethod(read_asset)
        cls.retired = json.loads((OPTIONS.project/'source/retired_character_name_assets.json').read_text())
        cls.provenance = {r['asset']: r for r in json.loads(OPTIONS.provenance.read_text())
                          if r.get('sha256')}
        cls.docs = {}
        for asset in cls.retired:
            source = OPTIONS.upstream/asset
            if source.is_file():
                if sha(source.read_bytes()) != cls.provenance[asset]['sha256']:
                    raise AssertionError('Upstream fixture bytes changed: '+asset)
                cls.docs[asset] = cls.read_asset(source)
        cls.old_sources = {}
        for source_id in SOURCES:
            asset = f'names/{source_id}.namesource'
            cls.old_sources[source_id] = apply_display_pairs(
                cls.docs[asset], OPTIONS.old_mod/(asset+'.patch'))

    def test_shortened_old_training_words_are_detected_exactly(self):
        bad = []
        under_target_min = 0
        for source_id in SOURCES:
            original = self.docs[f'names/{source_id}.namesource']
            localized = self.old_sources[source_id]
            self.assertEqual(original['prefixSize'], 2)
            self.assertEqual(original['endSize'], 2)
            self.assertEqual(len(original['sourceNames']), 57)
            for index, (before, after) in enumerate(zip(original['sourceNames'], localized['sourceNames'])):
                upper = utf16_units(after) - original['prefixSize']
                under_target_min += utf16_units(after) < 3
                if upper < 0:
                    bad.append({'source_id':source_id, 'index':index,
                                'original':before, 'translated':after,
                                'unicode_characters':len(after),
                                'utf16_units':utf16_units(after),
                                'utf8_bytes':len(after.encode('utf-8')),
                                'prefix_size':original['prefixSize'],
                                'independent_seed_upper_bound':upper})
        self.assertEqual({(r['source_id'],r['original'],r['translated']) for r in bad}, EXPECTED_SHORT)
        self.assertEqual(len(bad), 8)
        self.assertEqual(under_target_min, 20)
        METRICS['old_negative_seed_upper_bounds'] = bad
        METRICS['old_training_words_below_target_min_3'] = under_target_min

    def test_restored_training_bytes_and_parameters_match_official_data(self):
        preserved = 0
        bad = []
        for source_id in SOURCES:
            asset = f'names/{source_id}.namesource'
            original = self.docs[asset]
            result = apply_display_pairs(original, OPTIONS.mod/(asset+'.patch'))
            self.assertEqual(result, original)
            self.assertEqual(json.loads((OPTIONS.mod/(asset+'.patch')).read_text()), [])
            for index, (first, last) in enumerate(zip(original['sourceNames'], result['sourceNames'])):
                self.assertEqual(first.encode('utf-8'), last.encode('utf-8'))
                self.assertTrue(last.isascii())
                if utf16_units(last) < result['prefixSize']:
                    bad.append((source_id,index,last))
                self.assertGreaterEqual(len(last), 3)
                self.assertLessEqual(len(last), 10)
                preserved += 1
        self.assertEqual(preserved, 114)
        self.assertEqual(bad, [])
        METRICS['original_training_words_byte_identical'] = preserved
        METRICS['restored_negative_seed_upper_bounds'] = len(bad)

    def test_all_character_generators_are_no_ops_on_upstream_data(self):
        expected = {p.relative_to(OPTIONS.old_mod).as_posix()[:-6]
                    for p in OPTIONS.old_mod.rglob('*.patch')
                    if p.name.endswith('.namesource.patch') or
                    p.parent == OPTIONS.old_mod/'species' and p.name.endswith('namegen.config.patch')}
        self.assertEqual(set(self.retired), expected)
        self.assertEqual(len(self.retired), 32)
        self.assertEqual(set(self.retired)-set(self.docs), {'species/feneroxnamegen.config'})
        for asset, original in self.docs.items():
            with self.subTest(asset=asset):
                patch = OPTIONS.mod/(asset+'.patch')
                self.assertEqual(json.loads(patch.read_text()), [])
                result = apply_display_pairs(original, patch)
                self.assertEqual(result, original)
                self.assertEqual(json.dumps(result,ensure_ascii=False,separators=(',',':')).encode('utf-8'),
                                 json.dumps(original,ensure_ascii=False,separators=(',',':')).encode('utf-8'))
        # FU supplies only an append patch for Fenerox. Its vanilla base is not
        # included here. An empty later patch cannot modify any assembled base.
        fenerox = OPTIONS.upstream/'species/feneroxnamegen.config.patch'
        self.assertEqual(sha(fenerox.read_bytes()),self.provenance['species/feneroxnamegen.config.patch']['sha256'])
        patch = OPTIONS.mod/'species/feneroxnamegen.config.patch'
        self.assertEqual(json.loads(patch.read_text()), [])
        sentinel = {'names':[{'mode':'serie'},['Original assembled prefix'],['Original assembled suffix']],
                    'untouched':{'number':17,'reference':'original_reference'}}
        self.assertEqual(apply_display_pairs(sentinel,patch),sentinel)
        METRICS['real_full_upstream_assets_unchanged'] = len(self.docs)
        METRICS['fenerox_no_op_on_arbitrary_assembled_base'] = True
        METRICS['retired_patch_files_checked'] = len(self.retired)

    def test_male_and_female_markov_references_still_resolve(self):
        registry = {self.docs[f'names/{name}.namesource']['name'] for name in SOURCES}
        for name in SOURCES:
            asset = f'species/{name}namegen.config'
            original = self.docs[asset]
            result = apply_display_pairs(original, OPTIONS.mod/(asset+'.patch'))
            self.assertEqual(result, original)
            self.assertEqual(list(references(result)), [name])
            self.assertIn(name, registry)
        METRICS['resolved_original_markov_references'] = 2


def main():
    global OPTIONS
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',required=True,type=Path)
    parser.add_argument('--mod',required=True,type=Path)
    parser.add_argument('--old-mod',required=True,type=Path)
    parser.add_argument('--upstream',required=True,type=Path)
    parser.add_argument('--provenance',required=True,type=Path)
    parser.add_argument('--report',required=True,type=Path)
    OPTIONS = parser.parse_args()
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CharacterNameRestorationTests))
    report = {
        'passed':result.wasSuccessful(), 'tests_run':result.testsRun,
        'failures':len(result.failures), 'errors':len(result.errors),
        'runtime_tested':False,
        'scope':'Original character generator data restoration, exact training-word UTF-8 bytes, registered source IDs, and a necessary seed-length input condition of an independent C# implementation. No native game or Markov generation simulation.',
        'metrics':METRICS,
        'independent_reference':'https://github.com/Kawa-oneechan/SBCharCreator/blob/master/NameGen.cs',
        'reference_limit':'The independent code ignores targetLength and is not established as equivalent to Starbound 1.4.4. It demonstrates a negative input bound, not the cause of the reported native freeze.',
        'limits':['Fenerox has only an upstream append patch; its combined vanilla+FU asset was not available for a real-base application test.','A no-op patch is tested to leave the assembled document unchanged regardless of its content.','No game save or installed game directory is read or changed.'],
    }
    OPTIONS.report.parent.mkdir(parents=True,exist_ok=True)
    OPTIONS.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(main())
