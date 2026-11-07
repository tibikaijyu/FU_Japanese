#!/usr/bin/env python3
"""Verify a narrow v0.2.1 repair against the exact distributed v0.2.0 ZIP.

This is a byte-preservation and data-semantics audit, not a Starbound launch.
Run test_namegen_semantics.py first. Full rebuilding still uses validate.py
with the complete pinned FU source checkout.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from namegen_safety import assert_safe_namegen_patch, assert_safe_namegen_translation

BASELINE_SHA256 = '09abec002f7a13e2dd81e74d613c58f1cf5edf53a2239663f42c502d7aea78fb'
PREFIX = 'FU_Japanese_0.2.0/'
REMOVED = {
    'species/elduukharmalenamegen.config.patch',
    'species/elduukharfemalenamegen.config.patch',
}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def verify(project, mod, baseline_zip):
    project, mod, baseline_zip = map(Path, (project, mod, baseline_zip))
    assert sha(baseline_zip.read_bytes()) == BASELINE_SHA256, 'Wrong baseline ZIP'
    regression = json.loads((project/'reports/namegen_regression.json').read_text())
    assert regression['passed'] and not regression['failures'] and not regression['errors']
    assert regression['metrics']['fixed_source_references_resolved'] == 2
    audit = json.loads((project/'reports/final_residual_decisions.json').read_text())
    for key in ('unclassified_whole_fields', 'missing_translation_fields', 'structural_errors'):
        assert audit[key] == 0, key
    actual = {p.relative_to(mod).as_posix(): sha(p.read_bytes())
              for p in mod.rglob('*') if p.is_file()}
    with zipfile.ZipFile(baseline_zip) as z:
        old = json.loads(z.read(PREFIX+'source/reports/mod_sha256.json'))
        archived = {n.removeprefix(PREFIX+'mods/FU_Japanese/'): sha(z.read(n))
                    for n in z.namelist()
                    if n.startswith(PREFIX+'mods/FU_Japanese/') and not n.endswith('/')}
        assert old == archived, 'Baseline archive and validation manifest disagree'
        assert set(old) - set(actual) == REMOVED
        assert not set(actual) - set(old)
        changed = sorted(p for p in actual if actual[p] != old[p])
        assert changed == ['_metadata'], changed
        old_meta = json.loads(z.read(PREFIX+'mods/FU_Japanese/_metadata'))
        meta = json.loads((mod/'_metadata').read_text())
        old_meta['version'] = '0.2.1-fu6.5.8'
        assert meta == old_meta
        assert meta['requires'] == [] and meta['includes'] == ['FrackinUniverse']
        assert meta['priority'] == 1000
        for name in ('catalog.jsonl', 'translated_catalog.jsonl'):
            before = [json.loads(s) for s in z.read(PREFIX+'source/source/'+name).decode().splitlines()]
            after = [json.loads(s) for s in (project/'source'/name).read_text().splitlines()]
            expected = [r for r in before if r['asset']+'.patch' not in REMOVED]
            assert after == expected and len(before) - len(after) == 2
        preserved_font_files = 0
        for p in (project.parent/'optional').rglob('*'):
            if p.is_file():
                relative = p.relative_to(project.parent).as_posix()
                assert p.read_bytes() == z.read(PREFIX+relative)
                preserved_font_files += 1
    patch_count = ordinary = ui_count = authored_count = 0
    ui = json.loads((project/'reports/ui_image_label_manifest.json').read_text())
    ui_keys = {(r['asset'], json.dumps(r['group'], sort_keys=True, ensure_ascii=False)) for r in ui}
    for p in sorted(mod.rglob('*.patch')):
        asset = p.relative_to(mod).as_posix()[:-6]
        groups = json.loads(p.read_text(encoding='utf-8'))
        assert isinstance(groups, list), asset
        assert_safe_namegen_patch(asset, groups)
        patch_count += 1
        for group in groups:
            if (asset, json.dumps(group, sort_keys=True, ensure_ascii=False)) in ui_keys:
                ui_count += 1
                continue
            assert len(group) == 2
            a, b = group
            assert a['op'] == 'test' and b['op'] == 'replace' and a['path'] == b['path']
            if 'value' not in a:
                authored_count += 1
                continue
            assert isinstance(a['value'], str) and isinstance(b['value'], str)
            ordinary += 1
    assert (patch_count, ordinary, ui_count, authored_count) == (14383, 187928, 21, 2)
    for name in ('catalog.jsonl', 'append_catalog.jsonl', 'translated_catalog.jsonl', 'append_translated_catalog.jsonl'):
        for line in (project/'source'/name).read_text().splitlines():
            row = json.loads(line)
            assert_safe_namegen_translation(row['asset'], row['path'])
            for pointer in row.get('generated_paths', []):
                assert_safe_namegen_translation(row['asset'], pointer)
    validation = {
        'passed': True, 'mod_version': meta['version'], 'runtime_tested': False,
        'scope': 'v0.2.1 targeted repair: exact baseline payload comparison, complete patch parse and independent name-control checks, pinned FU reference-resolution regression. Not a full upstream reapplication or game launch.',
        'patch_files_parsed': patch_count, 'guarded_groups_checked': ordinary,
        'guarded_group_check_scope': 'Structure and exact byte identity to v0.2.0; prior generic application tests are historical evidence, not runtime proof.',
        'known_full_assets_verified': 0, 'known_full_asset_strings_changed': 0,
        'patch_only_assets_without_vanilla_or_other_mod_base': 1223,
        'upstream_reapplication_performed': False,
        'prior_full_asset_validation': 'history/v0.2.0/validation.json',
        'prior_validation_limitation': 'v0.2.0 incorrectly approved two source-ID translations. New namegen checks supersede that approval.',
        'errors': [], 'source_guard_mismatches_in_known_assets': [],
        'known_asset_source_patch_errors': [],
        'authored_dialogue_groups_checked': authored_count, 'ui_presentation_groups_checked': ui_count,
        'metadata_hard_dependencies': [], 'metadata_optional_load_after': ['FrackinUniverse'],
        'localized_lua_files_verified': 130, 'lua_verification': 'Byte identity to the distributed v0.2.0; Lua tests not rerun for unchanged scripts.',
        'lua_display_literal_changes': 694, 'supplemental_append_fields': 1203,
        'embedded_json_display_fields': 44,
        'namegen_regression': regression,
        'baseline_archive_sha256': BASELINE_SHA256,
        'preserved_main_mod_files': len(actual)-1,
        'removed_main_mod_files': sorted(REMOVED),
        'changed_main_mod_files': changed,
        'preserved_optional_font_files': preserved_font_files,
    }
    dump(project/'reports/validation.json', validation)
    dump(project/'reports/mod_sha256.json', actual)
    hotfix = json.loads((project/'reports/hotfix_0.2.1.json').read_text())
    hotfix.update({'validation_pending': False, 'passed': True,
                  'preserved_main_mod_files': len(actual)-1,
                  'regression_tests_passed': regression['tests_run'],
                  'patch_files_parsed': patch_count,
                  'validation_report': 'validation.json'})
    dump(project/'reports/hotfix_0.2.1.json', hotfix)
    print(json.dumps({k: validation[k] for k in ('passed', 'patch_files_parsed', 'guarded_groups_checked', 'preserved_main_mod_files', 'removed_main_mod_files', 'runtime_tested')}, ensure_ascii=False))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project', required=True)
    p.add_argument('--mod', required=True)
    p.add_argument('--baseline-zip', required=True)
    args = p.parse_args()
    verify(args.project, args.mod, args.baseline_zip)
