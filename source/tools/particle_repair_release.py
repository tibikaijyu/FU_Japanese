"""Package and validate public.5 without rewriting earlier release evidence."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import posixpath
import re
import sys
import zipfile

import package_release as packaging
from limited_repair_public4 import current_public_files, TOOLS_DEFAULT
from release_evidence import ROOT, filesystem_files, input_state_sha256, sha

RELEASE_ID = '0.2.4-public.5'
PAK_ID = RELEASE_ID + '-pak.2'
ASSET = 'stats/typer_particle.lua'
SOURCE = 'source/compat/' + ASSET
REVIEWED_SHA = 'b4bc888a82af982225076dd48d21e4a44d5d4e69d08f5666ca80b0ad29c6a79f'
BASELINE = 'source/reports/mod_sha256.json'
HISTORY = ('source/reports/limited_repair_024_public3.json',
           'source/reports/limited_repair_024_public4.json')
RECORD = 'source/reports/particle_repair_024_public5_pak2.json'
HELPER_TESTS = 'source/reports/limited_helper_tests_024_public5_pak2.json'
PARTICLE_TESTS = 'source/reports/particle_runtime_024_public5_pak2.json'
FIXTURE = 'source/tests/particle-fixtures/corpus.json'
UPSTREAM = 'source/tests/particle-fixtures/upstream-typer_particle.lua'
GUIDE = 'docs/limited-repair/INSTALL_JA_public5.md'
DOCS = (GUIDE, 'docs/compatibility/COMPATIBILITY.md', 'LICENSE.md',
        'THIRD_PARTY_NOTICES.md', 'CHANGELOG.md',
        'source/machine_translation/README.md', 'source/machine_translation/model_provenance.json',
        'docs/verification/2026-11-07-user-report.md')


def expected_mod(files):
    expected = json.loads(files[BASELINE])
    for path in HISTORY:
        expected.update(json.loads(files[path])['approved_helpers'])
    expected[ASSET] = REVIEWED_SHA
    return expected


def assert_payload(files):
    expected = expected_mod(files)
    actual = {p.removeprefix('mods/FU_Japanese/'): sha(data)
              for p, data in files.items() if p.startswith('mods/FU_Japanese/')}
    if actual != expected or sha(files[SOURCE]) != REVIEWED_SHA:
        raise ValueError('public.5 permits only the reviewed particle writer beyond public.4')
    return expected


def validate(files):
    record = json.loads(files[RECORD])
    helpers, particles = (json.loads(files[p]) for p in (HELPER_TESTS, PARTICLE_TESTS))
    expected = assert_payload(files)
    if record.get('release_id') != RELEASE_ID or record.get('changed_game_assets') != [ASSET]:
        raise ValueError('public.5 release identifier or change scope differs')
    state = input_state_sha256(files)
    if any(v.get('input_state_sha256') != state for v in (record, helpers, particles)):
        raise ValueError('public.5 evidence is stale for current source/MOD inputs')
    if record.get('historical_sha256') != {p: sha(files[p]) for p in (BASELINE, *HISTORY)}:
        raise ValueError('Historical release evidence changed')
    if record.get('test_sha256') != {p: sha(files[p]) for p in (HELPER_TESTS, PARTICLE_TESTS)}:
        raise ValueError('public.5 test report hash differs')
    if (helpers.get('passed') is not True or helpers.get('unit_tests') != 30
            or any(helpers.get(k) != 0 for k in ('failures', 'errors', 'skipped'))):
        raise ValueError('public.5 helper/packaging regression suite did not pass completely')
    if {r.get('runtime') for r in helpers.get('runtimes', [])} != {'Lua 5.3', 'Lua 5.4'}:
        raise ValueError('public.5 requires both helper Lua versions')
    for row in helpers['runtimes']:
        if (row.get('passed') is not True or row.get('core_cases') != 8
                or row.get('core_assertions') != 142 or row.get('extra_cases') != 262
                or row.get('extra_assertions') != 785):
            raise ValueError('public.5 helper coverage differs')
    if (particles.get('candidate_sha256') != REVIEWED_SHA
            or particles.get('corpus_sha256') != sha(files[FIXTURE])
            or particles.get('upstream_sha256') != sha(files[UPSTREAM])
            or particles.get('effect_count') != 8):
        raise ValueError('public.5 particle fixture or source differs')
    rows = particles.get('runs', [])
    if len(rows) != 2 or {r.get('lua_version') for r in rows} != {'5.3', '5.4'}:
        raise ValueError('public.5 requires both particle Lua versions')
    for row in rows:
        if (row.get('passed') is not True or row.get('checked_texts') != 172
                or row.get('checked_particles') != 987 or row.get('invalid_baseline_texts') != 169):
            raise ValueError('public.5 particle regression coverage differs')
    for row in json.loads(files[FIXTURE]):
        if row.get('patch_sha256') != sha(files['mods/FU_Japanese/' + row['asset'] + '.patch']):
            raise ValueError('public.5 effect translation fixture is stale')
    packages = record.get('packages', [])
    if [p.get('path') for p in packages] != ['mods/FU_Japanese.pak', 'optional/FU_Japanese_Font.pak']:
        raise ValueError('public.5 must include exactly the main and optional font PAKs')
    for row, count in zip(packages, (len(expected), len(packaging.FONT_FILE_ALLOWLIST))):
        proof = row.get('verification', {})
        if proof.get('file_count') != count or any(proof.get(k) is not True for k in (
                'relative_paths_match', 'non_metadata_raw_sha256_match', 'metadata_json_deep_equal')):
            raise ValueError('public.5 official PAK roundtrip is incomplete')
    font = {p.removeprefix(packaging.FONT_PREFIX): sha(v) for p, v in files.items()
            if p.startswith(packaging.FONT_PREFIX)}
    old_font = json.loads(files[HISTORY[1]])['font_files']
    if font != old_font or set(font) != packaging.FONT_FILE_ALLOWLIST:
        raise ValueError('public.5 optional font differs from public.4')
    artifact = record.get('artifact', {})
    if (artifact.get('file') != 'FU_Japanese_' + PAK_ID + '-install.zip'
            or artifact.get('crc_and_content_verified') is not True
            or record.get('upload_allowlist') != [artifact['file']]):
        raise ValueError('public.5 install ZIP allowlist differs')
    if record.get('document_sha256') != {p: sha(files[p]) for p in DOCS}:
        raise ValueError('public.5 packaged documents differ')
    if any(record.get(k) is not False for k in ('native_game_executed', 'whole_mod_rebuilt',
                                               'multiplayer_disconnect_cause_verified')):
        raise ValueError('public.5 cannot claim game/full rebuild/multiplayer verification')
    return record


def document_links(payload):
    for name, data in payload.items():
        if not name.endswith('.md'):
            continue
        for target in re.findall(rb'\]\(([^)]+)\)', data):
            link = target.decode('utf-8')
            if link.startswith(('http:', 'https:', 'mailto:', '#')):
                continue
            destination = posixpath.normpath(posixpath.join(posixpath.dirname(name), link.split('#')[0]))
            if destination not in payload:
                raise ValueError('Broken install document link: ' + name + ' -> ' + link)


def reuse_verified_paks(files, previous, tools):
    previous = Path(previous).resolve(strict=True)
    if not previous.is_relative_to(ROOT / 'dist'):
        raise ValueError('Verified PAK proof must be inside this repository dist')
    report = json.loads(previous.read_text(encoding='utf-8'))
    if (report.get('release_id') != RELEASE_ID or report.get('changed_game_assets') != [ASSET]
            or report.get('historical_sha256') != {p: sha(files[p]) for p in (BASELINE, *HISTORY)}):
        raise ValueError('Verified PAK baseline differs')
    if report.get('official_tools') != {p.name: sha(p.read_bytes()) for p in (
            Path(tools) / 'asset_packer.exe', Path(tools) / 'asset_unpacker.exe')}:
        raise ValueError('Official tools differ from verified PAK proof')
    artifact = report['artifact']
    archive = previous.parent / artifact['file']
    if sha(archive.read_bytes()) != artifact['sha256']:
        raise ValueError('Verified input ZIP hash differs')
    results = []
    with zipfile.ZipFile(archive) as zf:
        for package in report['packages']:
            matches = [n for n in zf.namelist() if n.endswith('/' + package['path'])]
            if len(matches) != 1:
                raise ValueError('Verified input PAK path differs')
            data = zf.read(matches[0])
            proof = package['verification']
            meta = ('mods/FU_Japanese/_metadata' if package['path'].startswith('mods/')
                    else 'optional/FU_Japanese_Font/_metadata')
            if (sha(data) != package['pak_sha256']
                    or proof.get('metadata_canonical_sha256') != sha(packaging.canonical_json(files[meta]))
                    or any(proof.get(k) is not True for k in (
                        'relative_paths_match', 'non_metadata_raw_sha256_match', 'metadata_json_deep_equal'))):
                raise ValueError('Verified PAK bytes or roundtrip proof differs')
            results.extend((data, proof))
    if len(results) != 4:
        raise ValueError('Expected the two verified PAKs')
    return results


def create(output, tools, verified_generation=None):
    output = Path(output).resolve()
    if not output.is_relative_to(ROOT) or output == ROOT or output.exists():
        raise ValueError('Use a new output directory inside this repository')
    files = current_public_files(ROOT)
    assert_payload(files)
    before = input_state_sha256(filesystem_files(ROOT))
    from run_limited_helper_tests import run as run_helpers
    output.mkdir(parents=True)
    run_helpers(output / 'helper-tests.json', 'auto')
    sys.path.insert(0, str(ROOT / 'source/compat'))
    from test_typer_particle import verify
    particles = verify(ROOT / SOURCE, ROOT / UPSTREAM, ROOT / FIXTURE)
    after = input_state_sha256(filesystem_files(ROOT))
    if before != after:
        raise ValueError('Source/MOD inputs changed during release tests')
    particles['input_state_sha256'] = after
    particle_bytes = (json.dumps(particles, indent=2) + '\n').encode()
    helper_bytes = (output / 'helper-tests.json').read_bytes()
    if verified_generation:
        main, main_proof, font, font_proof = reuse_verified_paks(files, verified_generation, tools)
    else:
        main, main_proof = packaging.build_verified_pak(files, tools, output)
        font, font_proof = packaging.build_verified_font_pak(files, tools, output)
    selected = packaging.pak_install_files(files, main, font)
    payload = {p: v for p, v in selected.items()
               if p.startswith(('mods/', 'optional/', 'LICENSES/'))
               or p in ('LICENSE.md', 'THIRD_PARTY_NOTICES.md', 'CHANGELOG.md', 'MIT-tools.txt')
               or p.startswith('source/machine_translation/')}
    payload['docs/verification/2026-11-07-user-report.md'] = files['docs/verification/2026-11-07-user-report.md']
    payload['README_JA.md'] = files[GUIDE]
    payload['FU_COMPATIBILITY.md'] = files['docs/compatibility/COMPATIBILITY.md']
    document_links(payload)
    artifact = packaging.write_zip(output / ('FU_Japanese_' + PAK_ID + '-install.zip'), PAK_ID, payload)
    packages = [
        {'path': 'mods/FU_Japanese.pak', 'pak_sha256': sha(main), 'verification': main_proof},
        {'path': 'optional/FU_Japanese_Font.pak', 'pak_sha256': sha(font), 'verification': font_proof}]
    record = {'schema': 1, 'release_id': RELEASE_ID, 'input_state_sha256': after,
              'historical_sha256': {p: sha(files[p]) for p in (BASELINE, *HISTORY)},
              'changed_game_assets': [ASSET], 'packages': packages,
              'test_sha256': {HELPER_TESTS: sha(helper_bytes), PARTICLE_TESTS: sha(particle_bytes)},
              'artifact': artifact, 'upload_allowlist': [artifact['file']],
              'document_sha256': {p: sha(files[p]) for p in DOCS},
              'native_game_executed': False, 'whole_mod_rebuilt': False,
              'multiplayer_disconnect_cause_verified': False}
    if verified_generation:
        record['reused_official_pak_report_sha256'] = sha(Path(verified_generation).read_bytes())
    encoded = (json.dumps(record, indent=2, sort_keys=True) + '\n').encode()
    files.update({HELPER_TESTS: helper_bytes, PARTICLE_TESTS: particle_bytes, RECORD: encoded})
    validate(files)
    if input_state_sha256(filesystem_files(ROOT)) != after:
        raise ValueError('Release inputs changed during official packaging')
    for path, data in ((HELPER_TESTS, helper_bytes), (PARTICLE_TESTS, particle_bytes), (RECORD, encoded)):
        target = ROOT / path
        if target.exists():
            raise FileExistsError('Refusing to overwrite release evidence: ' + path)
        target.write_bytes(data)
    report = {**record, 'official_tools': {p.name: sha(p.read_bytes()) for p in (
        Path(tools) / 'asset_packer.exe', Path(tools) / 'asset_unpacker.exe')}}
    (output / 'generation-report.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    manifest = {'release_id': RELEASE_ID, 'prerelease': True, 'artifacts': [artifact],
                'upload_allowlist': [artifact['file']]}
    (output / ('release-artifacts-' + RELEASE_ID + '.json')).write_text(
        json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    (output / 'SHA256SUMS.txt').write_text(artifact['sha256'] + '  ' + artifact['file'] + '\n', encoding='ascii')
    print(json.dumps({'output': str(output), 'artifact': artifact}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--pak-tools-dir', type=Path, default=TOOLS_DEFAULT)
    parser.add_argument('--verified-generation', type=Path)
    args = parser.parse_args()
    create(args.output_dir, args.pak_tools_dir, args.verified_generation)
