"""Validate current limited-repair evidence without relabeling old full reports."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from limited_repair_release import HELPER_ASSETS, EXPECTED_INPUT_PAK_SHA256, CONFIG_ASSETS
from release_evidence import ROOT, filesystem_files, input_state_sha256, sha

RECORD = 'source/reports/limited_repair_024_public3.json'
TESTS = 'source/reports/limited_helper_tests_024_public3.json'
BASELINE = 'source/reports/mod_sha256.json'
SOURCE_PATHS = {
    'fujp/lua_display.lua':'source/compat/fujp/lua_display.lua',
    'fujp/species_display.lua':'source/compat/followup_022/fujp/species_display.lua',
    'fujp/guide_display.lua':'source/compat/followup_022/fujp/guide_display.lua',
}
ARTIFACT = {'file':'FU_Japanese_0.2.4-public.3-pak.1-install.zip',
            'sha256':'66a48798ba904ae26d4e7dc4e32facbd2105a7530d04a03de3a41d3d8696b3eb',
            'bytes':3403701, 'files':9, 'crc_and_content_verified':True}
GENERATION_SHA256 = '06661a1feec724d2e3ab7d3fb3e4b8b82aab7405d08c29ac54b53d12ca159759'
HARNESSES = {'source/compat/test_extra_display_fallback.py',
             'source/compat/test_lua_localization.lua', 'source/tools/run_limited_helper_tests.py'}


def validate(files):
    record = json.loads(files[RECORD])
    tests = json.loads(files[TESTS])
    baseline = json.loads(files[BASELINE])
    state = input_state_sha256(files)
    if record.get('schema') != 1 or record.get('scope') != 'three-helper-repair':
        raise ValueError('Limited repair evidence has an unexpected schema or scope')
    if (record.get('release_id') != '0.2.4-public.3' or record.get('artifact') != ARTIFACT
            or record.get('generation_report_sha256') != GENERATION_SHA256):
        raise ValueError('Limited repair artifact differs from the independently reviewed release')
    if record.get('input_state_sha256') != state or tests.get('input_state_sha256') != state:
        raise ValueError('Limited repair evidence is stale for the current source/MOD inputs')
    if record.get('test_report_sha256') != sha(files[TESTS]):
        raise ValueError('Limited repair test report hash differs')
    if record.get('baseline_manifest_sha256') != sha(files[BASELINE]):
        raise ValueError('Historical MOD manifest changed')
    if record.get('input_pak_sha256') != EXPECTED_INPUT_PAK_SHA256:
        raise ValueError('Limited repair input PAK is not the reviewed input')
    if record.get('approved_helpers') != HELPER_ASSETS or set(record.get('baseline_helpers', {})) != set(HELPER_ASSETS):
        raise ValueError('Limited repair must replace exactly the three reviewed helpers')
    for asset, digest in HELPER_ASSETS.items():
        if record['baseline_helpers'][asset] != baseline[asset]:
            raise ValueError('Historical helper hash differs: ' + asset)
        for path in (SOURCE_PATHS[asset], 'mods/FU_Japanese/' + asset):
            if sha(files[path]) != digest:
                raise ValueError('Reviewed helper differs from current source/MOD: ' + path)
    configs = record.get('tested_config_sha256', {})
    if set(configs) != set(CONFIG_ASSETS):
        raise ValueError('Limited repair must bind all three display dictionaries')
    for asset, digest in configs.items():
        if sha(files['mods/FU_Japanese/' + asset]) != digest:
            raise ValueError('Tested display dictionary changed: ' + asset)
    trip = record.get('official_roundtrip', {})
    if (trip.get('file_count') != len(baseline) or trip.get('relative_paths_match') is not True
            or trip.get('non_metadata_raw_sha256_match') is not True
            or trip.get('metadata_json_deep_equal') is not True):
        raise ValueError('Limited repair official PAK round trip did not pass')
    if (record.get('whole_mod_rebuilt') is not False or record.get('native_game_executed') is not False
            or tests.get('native_game_executed') is not False):
        raise ValueError('Limited repair must not claim whole-MOD rebuild or game execution')
    if (tests.get('passed') is not True or tests.get('unit_tests') != 25
            or any(tests.get(key) != 0 for key in ('failures', 'errors', 'skipped'))):
        raise ValueError('Limited repair regression tests did not pass completely')
    rows = tests.get('runtimes', [])
    if len(rows) != 2 or {r.get('runtime') for r in rows} != {'Lua 5.3', 'Lua 5.4'}:
        raise ValueError('Limited repair must test both Lua versions')
    for row in rows:
        if (row.get('passed') is not True or row.get('core_cases') != 8 or row.get('core_assertions') != 142
                or row.get('extra_cases') != 249 or row.get('extra_assertions') != 639):
            raise ValueError('Limited helper regression coverage differs')
    if set(tests.get('harness_sha256', {})) != HARNESSES:
        raise ValueError('Limited helper test harness inventory differs')
    for path, digest in tests['harness_sha256'].items():
        if path not in files or sha(files[path]) != digest:
            raise ValueError('Limited helper test harness changed')
    return record


def create(generation_report):
    package = json.loads(Path(generation_report).read_text(encoding='utf-8'))
    files = filesystem_files(ROOT)
    # Reports lie outside release_evidence's input roots; read them explicitly.
    tests_raw = (ROOT / TESTS).read_bytes()
    baseline_raw = (ROOT / BASELINE).read_bytes()
    record = {'schema':1, 'scope':'three-helper-repair', 'release_id':package['release_id'],
              'input_state_sha256':input_state_sha256(files),
              'generation_report_sha256':sha(Path(generation_report).read_bytes()),
              'baseline_manifest_sha256':sha(baseline_raw), 'test_report_sha256':sha(tests_raw),
              'input_pak_sha256':package['input_pak']['sha256'],
              'approved_helpers':package['evidence']['helper_assets'],
              'baseline_helpers':package['repair_delta']['input_helper_hashes'],
              'tested_config_sha256':package['staged_display_config_hashes'],
              'official_roundtrip':package['pak']['roundtrip'],
              'artifact':package['zip'], 'pak_sha256':package['pak']['sha256'],
              'whole_mod_rebuilt':False, 'native_game_executed':False,
              'known_findings':{'research_tree_code_mismatches':1, 'external_builder_conflicts':2,
                                'runtime_causation_verified':False}}
    encoded = (json.dumps(record, indent=2, sort_keys=True) + '\n').encode('utf-8')
    files.update({RECORD:encoded, TESTS:tests_raw, BASELINE:baseline_raw})
    validate(files)
    (ROOT / RECORD).write_bytes(encoded)
    print(json.dumps({'written':RECORD, 'scope':record['scope'], 'artifact':record['artifact']}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generation-report', type=Path, required=True)
    create(parser.parse_args().generation_report)
