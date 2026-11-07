#!/usr/bin/env python3
"""Verify the targeted 0.2.3 name-generation repair against the distributed 0.2.2 archive."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

from build import check_translation
from followup_022 import read_manifest, patch_allowances
from namegen_safety import assert_safe_namegen_patch, assert_safe_namegen_translation, retired_character_name_assets

BASELINE_SHA256 = 'ae519e8b48b099981e448e87744bdb02a5b26b6b944809dbae175ec227ee37b9'
PREFIX = 'FU_Japanese_0.2.2/'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def dump(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def verify(project, mod, baseline_zip):
    project, mod, baseline_zip = map(Path, (project, mod, baseline_zip))
    assert sha(baseline_zip.read_bytes()) == BASELINE_SHA256, 'Unexpected baseline archive'
    retired = set(retired_character_name_assets(project))
    empty_files = {asset+'.patch' for asset in retired}
    desired = {asset: sha(b'[]\n') for asset in empty_files}
    actual = {p.relative_to(mod).as_posix(): sha(p.read_bytes()) for p in mod.rglob('*') if p.is_file()}
    with zipfile.ZipFile(baseline_zip) as z:
        previous = json.loads(z.read(PREFIX+'source/reports/mod_sha256.json'))
        expected = dict(previous)
        expected.update(desired)
        old_meta = json.loads(z.read(PREFIX+'mods/FU_Japanese/_metadata'))
        old_meta['version'] = '0.2.3-fu6.5.8'
        metadata = read_json(mod/'_metadata')
        assert metadata == old_meta
        expected['_metadata'] = actual['_metadata']
        assert actual == expected, 'Unexpected game-file modification or missing reviewed output'
        for name in ('catalog.jsonl', 'translated_catalog.jsonl',
                     'append_catalog.jsonl', 'append_translated_catalog.jsonl'):
            old_rows = [json.loads(s) for s in z.read(PREFIX+'source/source/'+name).decode().splitlines()]
            new_rows = [json.loads(s) for s in (project/'source'/name).read_text().splitlines()]
            assert new_rows == [r for r in old_rows if r['asset'] not in retired], name
            for row in new_rows:
                assert_safe_namegen_translation(row['asset'], row['path'])
                for pointer in row.get('generated_paths', []):
                    assert_safe_namegen_translation(row['asset'], pointer)
        for file in (project.parent/'optional').rglob('*'):
            if file.is_file():
                relative = file.relative_to(project.parent).as_posix()
                assert file.read_bytes() == z.read(PREFIX+relative)
    assert metadata['requires'] == [] and metadata['includes'] == ['FrackinUniverse'] and metadata['priority'] == 1000
    assert len(actual) == len({p.casefold() for p in actual}), 'Windows path case collision'
    allowed = set(patch_allowances(project))
    for line in (project/'source/translated_catalog.jsonl').read_text().splitlines():
        r = json.loads(line)
        assert r['source'] != r['translation'], 'Retained symbols must not be counted as translations'
        allowed.add((r['asset'],r['path'],r['source'],r['translation']))
    for line in (project/'source/append_translated_catalog.jsonl').read_text().splitlines():
        r = json.loads(line)
        allowed.update((r['asset'],p,r['source'],r['translation']) for p in r['generated_paths'])
    embedded = read_json(project/'reports/embedded_manifest.json')
    allowed.update((r['asset'],r['path'],r['source'],r['target']) for r in embedded)
    ui = read_json(project/'reports/ui_image_label_manifest.json')
    ui_set = {(r['asset'], json.dumps(r['group'], sort_keys=True)) for r in ui}
    adaptations = {(r['asset'],r['path']):r['translation'] for r in read_json(project/'source/authored_adaptations.json')}
    patches = normal_groups = ui_groups = authored_groups = empty_patches = 0
    for file in sorted(mod.rglob('*.patch')):
        rel = file.relative_to(mod).as_posix()
        asset = rel[:-6]
        groups = read_json(file)
        assert isinstance(groups, list), asset
        assert_safe_namegen_patch(asset, groups)
        patches += 1
        if not groups:
            assert rel in empty_files
            empty_patches += 1
        for group in groups:
            if (asset,json.dumps(group,sort_keys=True)) in ui_set:
                ui_groups += 1
                continue
            assert isinstance(group,list) and len(group)==2, asset
            a,b=group
            assert a['op']=='test' and b['op']=='replace' and a['path']==b['path'],asset
            if 'value' not in a:
                assert adaptations.get((asset,a['path']))==b['value'],asset
                authored_groups += 1
                continue
            key=(asset,a['path'],a['value'],b['value'])
            assert key in allowed, (asset,a['path'],'unapproved text change')
            if rel in desired:
                issues=check_translation(a['value'],b['value'])
                assert not issues,(asset,a['path'],issues)
            normal_groups += 1
    assert empty_patches==len(empty_files)==32 and ui_groups==21 and authored_groups==2
    lua=read_json(project/'reports/lua_validation.json')
    for r in lua['files']:
        assert actual[r['asset']]==r['localized_sha256']
    for r in lua['support_assets']:
        assert actual[r['asset']]==r['sha256']
    audit=read_json(project/'reports/final_residual_decisions.json')
    for key in ('missing_translation_fields','structural_errors','unclassified_whole_fields'):
        assert audit[key]==0,key
    for name in ('catalog.jsonl','append_catalog.jsonl','lua_catalog.jsonl'):
        assert audit['input_sha256'][name]==sha((project/'source'/name).read_bytes())
    evidence=read_json(project/'reports/test_summary_023.json')
    assert evidence['passed'] and all(r['passed'] for r in evidence['reports'])
    for row in evidence['reports']:
        file = project/'reports'/row['file']
        assert sha(file.read_bytes()) == row['sha256'], row['file']
        assert read_json(file)['passed'], row['file']

    unchanged=sum(name in previous and value==previous[name] for name,value in actual.items())
    validation={
        'passed':True, 'mod_version':metadata['version'], 'runtime_tested':False,
        'scope':'Exact 0.2.2 baseline comparison, complete patch allowlist and character-name protections, pinned generation-input preservation and actual folder overlays. Unchanged Lua/display tests are reused from 0.2.2; the native game and Markov generator are not executed.',
        'patch_files_parsed':patches,'guarded_groups_checked':normal_groups,
        'ui_presentation_groups_checked':ui_groups,'authored_dialogue_groups_checked':authored_groups,
        'empty_legacy_compatibility_patches':empty_patches,
        'known_full_assets_verified':0,'known_full_asset_strings_changed':0,
        'patch_only_assets_without_vanilla_or_other_mod_base':1223,
        'upstream_reapplication_performed':False,
        'prior_full_asset_validation':'history/v0.2.0/validation.json',
        'source_guard_mismatches_in_known_assets':[],'known_asset_source_patch_errors':[],'errors':[],
        'metadata_hard_dependencies':[],'metadata_optional_load_after':['FrackinUniverse'],
        'localized_lua_files_verified':lua['file_count'],'lua_display_literal_changes':lua['translated_literals'],
        'supplemental_append_fields':read_json(project/'reports/append_coverage.json')['translated_entries'],'embedded_json_display_fields':44,
        'game_files':len(actual),'unchanged_game_files_from_022':unchanged,
        'changed_game_files_from_022':sorted(p for p in actual if p in previous and actual[p]!=previous[p]),
        'new_game_files_from_022':sorted(set(actual)-set(previous)),
        'baseline_archive_sha256':BASELINE_SHA256,'targeted_test_evidence':evidence,
        'direct_hang_causation_confirmed':False,
        'removed_character_name_guarded_groups':188070-normal_groups,
        'preserved_guides_and_species_descriptions':True,
    }
    dump(project/'reports/validation.json',validation)
    dump(project/'reports/mod_sha256.json',actual)
    print(json.dumps({k:validation[k] for k in ('passed','patch_files_parsed','guarded_groups_checked','game_files','unchanged_game_files_from_022','runtime_tested')},ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',required=True)
    p.add_argument('--mod',required=True)
    p.add_argument('--baseline-zip',required=True)
    a=p.parse_args()
    verify(a.project,a.mod,a.baseline_zip)
