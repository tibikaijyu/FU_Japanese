"""Validate the public.4 approval independently from immutable public.3 history."""
from __future__ import annotations

import json
import re
from pathlib import Path

from release_evidence import ROOT, filesystem_files, input_state_sha256, sha

RECORD = 'source/reports/limited_repair_024_public4.json'
TESTS = 'source/reports/limited_helper_tests_024_public4.json'
BASELINE = 'source/reports/mod_sha256.json'
HISTORICAL = 'source/reports/limited_repair_024_public3.json'
SOURCE_PATHS = {
    'fujp/species_display.lua':'source/compat/followup_022/fujp/species_display.lua',
    'fujp/guide_display.lua':'source/compat/followup_022/fujp/guide_display.lua',
}
HARNESS_PATHS = {
    'source/compat/test_extra_display_fallback.py',
    'source/compat/test_lua_localization.lua',
    'source/tools/run_limited_helper_tests.py',
}
FONT_PREFIX = 'optional/FU_Japanese_Font/'
FONT_ALLOWLIST = {'_metadata','hobo.ttf','ATTRIBUTION.txt','LICENSE-MPLUS-EN.txt','LICENSE-MPLUS-JA.txt'}
DOCS = (
    ('docs/README_JA.md','README_JA.md'),
    ('docs/limited-repair/INSTALL_JA_public4.txt','INSTALL_JA.txt'),
    ('docs/PAK_DISTRIBUTION.md','PAK_DISTRIBUTION.md'),
    ('CHANGELOG.md','CHANGELOG.md'),
    ('LICENSE.md','LICENSE.md'),
    ('THIRD_PARTY_NOTICES.md','THIRD_PARTY_NOTICES.md'),
    ('docs/limited-repair/FU_Japanese_0.2.4-public.4.md','limited-repair/FU_Japanese_0.2.4-public.4.md'),
    ('docs/limited-repair/INSTALL_JA_public4.txt','limited-repair/INSTALL_JA_public4.txt'),
)


def validate(files):
    record = json.loads(files[RECORD])
    tests = json.loads(files[TESTS])
    baseline = json.loads(files[BASELINE])
    historical = json.loads(files[HISTORICAL])
    helpers = record.get('approved_helpers', {})
    expected_names = set(SOURCE_PATHS)
    if record.get('schema') != 1 or record.get('scope') != 'two-helper-display-repair':
        raise ValueError('public.4 evidence has an unexpected schema or scope')
    if record.get('release_id') != '0.2.4-public.4' or set(helpers) != expected_names:
        raise ValueError('public.4 must explicitly approve exactly two display helpers')
    if any(not isinstance(v, str) or not re.fullmatch(r'[0-9a-f]{64}', v) for v in helpers.values()):
        raise ValueError('public.4 helper approval hashes are malformed')
    if record.get('historical_public3_record_sha256') != sha(files[HISTORICAL]):
        raise ValueError('Historical public.3 approval changed')
    expected_state = record.get('input_state_sha256')
    if (not expected_state or tests.get('input_state_sha256') != expected_state
            or input_state_sha256(files) != expected_state):
        raise ValueError('public.4 test report is stale for current source/MOD inputs')
    if record.get('test_report_sha256') != sha(files[TESTS]):
        raise ValueError('public.4 test report hash differs')
    if record.get('baseline_manifest_sha256') != sha(files[BASELINE]):
        raise ValueError('Historical MOD manifest changed')
    if record.get('input_pak_sha256') != historical.get('pak_sha256'):
        raise ValueError('public.4 input PAK is not the approved public.3 payload')
    old_helpers = historical.get('approved_helpers', {})
    if set(record.get('baseline_helpers', {})) != expected_names:
        raise ValueError('public.4 must bind the two public.3 helper hashes')
    for asset, source in SOURCE_PATHS.items():
        if asset not in baseline or record['baseline_helpers'].get(asset) != old_helpers.get(asset):
            raise ValueError('public.3 baseline helper approval differs: ' + asset)
        for path in (source, 'mods/FU_Japanese/' + asset):
            if sha(files[path]) != helpers[asset]:
                raise ValueError('Reviewed public.4 helper differs from source/MOD: ' + path)
    expected_mod = dict(baseline)
    expected_mod.update(old_helpers)
    expected_mod.update(helpers)
    actual_mod = {p.removeprefix('mods/FU_Japanese/'):sha(data) for p,data in files.items()
                  if p.startswith('mods/FU_Japanese/')}
    if actual_mod != expected_mod:
        raise ValueError('public.4 changes game assets outside its two approved helpers')
    if record.get('changed_game_assets') != sorted(expected_names):
        raise ValueError('public.4 change set is not exactly the two helpers')
    if record.get('tested_config_sha256') != {
        name:sha(files['mods/FU_Japanese/' + name])
        for name in ('fujp/lua_display.config','fujp/species_display.config','fujp/guide_display.config')
    }:
        raise ValueError('public.4 tested display config hashes differ')

    artifact = record.get('artifact', {})
    if (artifact.get('file') != 'FU_Japanese_0.2.4-public.4-pak.1-install.zip'
            or artifact.get('files') < 10 or artifact.get('crc_and_content_verified') is not True
            or not re.fullmatch(r'[0-9a-f]{64}', str(artifact.get('sha256', '')))):
        raise ValueError('public.4 install ZIP approval is malformed')
    if record.get('upload_allowlist') != [artifact['file']]:
        raise ValueError('public.4 upload allowlist must contain only the install ZIP')
    roundtrip = record.get('official_roundtrip', {})
    if (roundtrip.get('file_count') != len(baseline)
            or any(roundtrip.get(k) is not True for k in ('relative_paths_match','non_metadata_raw_sha256_match','metadata_json_deep_equal'))):
        raise ValueError('public.4 official main PAK round trip is not complete')
    actual_font = {name.removeprefix(FONT_PREFIX):sha(data) for name,data in files.items()
                   if name.startswith(FONT_PREFIX)}
    if (set(actual_font) != FONT_ALLOWLIST
            or actual_font != {name:sha(files[FONT_PREFIX + name]) for name in FONT_ALLOWLIST}
            or record.get('font_files') != actual_font):
        raise ValueError('Optional font payload differs from its exact file allowlist')
    if record.get('font_roundtrip', {}).get('file_count') != len(FONT_ALLOWLIST):
        raise ValueError('Optional font PAK round trip is incomplete')
    for key in ('relative_paths_match','non_metadata_raw_sha256_match','metadata_json_deep_equal'):
        if record['font_roundtrip'].get(key) is not True:
            raise ValueError('Optional font PAK round trip failed: ' + key)
    for source, packaged in DOCS:
        if record.get('packaged_document_sha256', {}).get(source) != sha(files[source]):
            raise ValueError('Packaged document approval differs: ' + source)
        if packaged not in record.get('packaged_paths', []):
            raise ValueError('Required public.4 document is absent from the package: ' + packaged)

    if (tests.get('passed') is not True or tests.get('unit_tests') != 30
            or any(tests.get(key) != 0 for key in ('failures','errors','skipped'))):
        raise ValueError('public.4 regression tests did not pass completely')
    rows = tests.get('runtimes', [])
    if len(rows) != 2 or {r.get('runtime') for r in rows} != {'Lua 5.3','Lua 5.4'}:
        raise ValueError('public.4 must test both Lua versions')
    for row in rows:
        if (row.get('passed') is not True or row.get('core_cases') != 8 or row.get('core_assertions') != 142
                or row.get('extra_cases') != 262 or row.get('extra_assertions') != 785
                or row.get('backend') not in ('lupa','ctypes')
                or not re.fullmatch(r'[0-9a-f]{64}', str(row.get('binary_sha256','')))):
            raise ValueError('public.4 runtime coverage/backend evidence differs')
    if set(tests.get('harness_sha256', {})) != HARNESS_PATHS:
        raise ValueError('public.4 test harness inventory differs')
    for path, digest in tests['harness_sha256'].items():
        if path not in files or sha(files[path]) != digest:
            raise ValueError('public.4 test harness changed: ' + path)
    if tests.get('helper_sha256') != {
        path:sha(files[path]) for path in (
            'source/compat/followup_022/fujp/species_display.lua',
            'source/compat/followup_022/fujp/guide_display.lua',
            'mods/FU_Japanese/fujp/species_display.lua',
            'mods/FU_Japanese/fujp/guide_display.lua')
    }:
        raise ValueError('public.4 regression report helper hashes differ')
    if (record.get('whole_mod_rebuilt') is not False or record.get('native_game_executed') is not False
            or record.get('multiplayer_disconnect_cause_verified') is not False
            or tests.get('native_game_executed') is not False or tests.get('whole_mod_runtime_tested') is not False):
        raise ValueError('public.4 must not claim full rebuild, game, or multiplayer verification')
    return record


def create(generation_report, test_report):
    generation_path, test_path = Path(generation_report), Path(test_report)
    generation = json.loads(generation_path.read_text(encoding='utf-8'))
    report_bytes = test_path.read_bytes()
    target_tests = ROOT / TESTS
    target_tests.write_bytes(report_bytes)
    files = filesystem_files(ROOT)
    extra = {BASELINE,HISTORICAL}
    extra.update(FONT_PREFIX + name for name in FONT_ALLOWLIST)
    extra.update(source for source,_ in DOCS)
    for path in extra:
        files[path] = (ROOT / path).read_bytes()
    files[TESTS] = report_bytes
    state = input_state_sha256(files)
    if json.loads(report_bytes).get('input_state_sha256') != state:
        raise ValueError('public.4 test report input state differs from current source/MOD')
    archive_path = generation_path.parent / generation['artifact']['file']
    import zipfile
    with zipfile.ZipFile(archive_path) as archive:
        prefix = generation['pak_release_id'] + '/'
        packaged_paths = sorted(name.removeprefix(prefix) for name in archive.namelist())
        if any(not name.startswith(prefix) for name in archive.namelist()):
            raise ValueError('Install ZIP has unexpected outer paths')
    historical = json.loads(files[HISTORICAL])
    approved = generation['current_helper_sha256']
    report = json.loads(report_bytes)
    record = {
        'schema':1, 'scope':'two-helper-display-repair', 'release_id':'0.2.4-public.4',
        'input_state_sha256':state,
        'test_report_sha256':sha(report_bytes),
        'generation_report_sha256':sha(generation_path.read_bytes()),
        'baseline_manifest_sha256':sha(files[BASELINE]),
        'historical_public3_record_sha256':sha(files[HISTORICAL]),
        'input_pak_sha256':generation['input_pak_sha256'],
        'approved_helpers':approved,
        'baseline_helpers':{asset:historical['approved_helpers'][asset] for asset in SOURCE_PATHS},
        'changed_game_assets':generation['changed_game_assets'],
        'tested_config_sha256':{name:sha(files['mods/FU_Japanese/' + name]) for name in (
            'fujp/lua_display.config','fujp/species_display.config','fujp/guide_display.config')},
        'official_roundtrip':generation['pak_distribution']['packages'][0]['verification'],
        'font_roundtrip':generation['pak_distribution']['packages'][1]['verification'],
        'font_pak_sha256':generation['pak_distribution']['packages'][1]['pak_sha256'],
        'font_files':{name:sha(files[FONT_PREFIX + name]) for name in FONT_ALLOWLIST},
        'artifact':generation['artifact'], 'upload_allowlist':generation['upload_allowlist'],
        'packaged_paths':packaged_paths,
        'packaged_document_sha256':{source:sha(files[source]) for source,_ in DOCS},
        'whole_mod_rebuilt':False, 'native_game_executed':False,
        'multiplayer_disconnect_cause_verified':False,
    }
    encoded = (json.dumps(record, indent=2, sort_keys=True) + '\n').encode('utf-8')
    files[RECORD] = encoded
    validate(files)
    (ROOT / RECORD).write_bytes(encoded)
    print(json.dumps({'written':RECORD, 'release_id':record['release_id'],
                      'input_state_sha256':state, 'artifact':record['artifact']}, indent=2))
