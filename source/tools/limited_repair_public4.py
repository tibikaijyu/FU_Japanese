#!/usr/bin/env python3
"""Build the public.4 two-helper repair using official Starbound tools."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile

import package_release as packaging

ROOT = Path(__file__).resolve().parents[2]
RELEASE_ID = '0.2.4-public.4'
PAK_RELEASE_ID = RELEASE_ID + '-pak.1'
BASELINE_ZIP = ROOT / 'dist/FU_Japanese_0.2.4-public.3-pak.1-install.zip'
BASELINE_ZIP_SHA256 = '66a48798ba904ae26d4e7dc4e32facbd2105a7530d04a03de3a41d3d8696b3eb'
BASELINE_PAK_SHA256 = 'bfe09fcf968337cf1e19bf95aa45f5260a5a16e4a305cf7558f4d954e7e81430'
HELPERS = {
    'fujp/species_display.lua': 'source/compat/followup_022/fujp/species_display.lua',
    'fujp/guide_display.lua': 'source/compat/followup_022/fujp/guide_display.lua',
}
TOOLS_DEFAULT = Path(r'E:/SteamLibrary/steamapps/common/Starbound/win32')


def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def current_public_files(root):
    raw = subprocess.run(
        ['git','-c','safe.directory='+str(root),'-C',str(root),'ls-files',
         '--cached','--others','--exclude-standard','-z'],
        check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
    ).stdout.decode('utf-8')
    result = {}
    for name in raw.split('\0'):
        if not name or name == 'SHA256SUMS.txt':
            continue
        path = root / name
        if not packaging.safe_public_path(name) or path.is_symlink() or not path.is_file():
            raise ValueError('Unsafe or missing public input: ' + name)
        result[name] = path.read_bytes()
    return result


def create(root=ROOT, output_dir=None, tools_dir=TOOLS_DEFAULT):
    root = Path(root).resolve()
    output_dir = Path(output_dir or root / 'dist').resolve()
    tools_dir = Path(tools_dir).resolve()
    if not output_dir.is_relative_to(root) or output_dir == root:
        raise ValueError('Output must be a unique directory inside the repository')
    archive = output_dir / f'FU_Japanese_{PAK_RELEASE_ID}-install.zip'
    verification_path = output_dir / f'FU_Japanese_{PAK_RELEASE_ID}-verification.json'
    sums_path = output_dir / f'SHA256SUMS-{RELEASE_ID}.txt'
    manifest_path = output_dir / f'release-artifacts-{RELEASE_ID}.json'
    generation_path = output_dir / f'FU_Japanese_{PAK_RELEASE_ID}-generation-report.json'
    collisions = [p.name for p in (archive, verification_path, sums_path, manifest_path, generation_path) if p.exists()]
    if collisions:
        raise FileExistsError('Refusing to overwrite release output: ' + ', '.join(collisions))
    output_dir.mkdir(parents=True, exist_ok=True)

    files = current_public_files(root)
    baseline_record = json.loads((root / 'source/reports/limited_repair_024_public3.json').read_text(encoding='utf-8'))
    if file_sha(BASELINE_ZIP) != BASELINE_ZIP_SHA256 or baseline_record.get('pak_sha256') != BASELINE_PAK_SHA256:
        raise ValueError('Historical public.3 ZIP/PAK does not match its fixed approval')
    with zipfile.ZipFile(BASELINE_ZIP) as zf:
        candidates = [n for n in zf.namelist() if n.endswith('/mods/FU_Japanese.pak')]
        if len(candidates) != 1:
            raise ValueError('Historical public.3 ZIP must contain exactly one main PAK')
        baseline_pak = zf.read(candidates[0])
    if packaging.sha(baseline_pak) != BASELINE_PAK_SHA256:
        raise ValueError('Historical public.3 PAK hash differs from fixed approval')

    baseline_unpacker = tools_dir / 'asset_unpacker.exe'
    if not baseline_unpacker.is_file():
        raise ValueError('Official Starbound asset_unpacker.exe is missing')
    with tempfile.TemporaryDirectory(prefix='.public4-baseline-') as temporary:
        temp = Path(temporary)
        baseline_file = temp / 'FU_Japanese.pak'
        baseline_dir = temp / 'baseline'
        baseline_file.write_bytes(baseline_pak)
        subprocess.run([str(baseline_unpacker), str(baseline_file), str(baseline_dir)], check=True,
                       capture_output=True, text=True)
        baseline = packaging.tree_inventory(baseline_dir)
        prefix = 'mods/FU_Japanese/'
        current = {name[len(prefix):]: data for name, data in files.items() if name.startswith(prefix)}
        current_hashes = {name: packaging.sha(data) for name, data in current.items()}
        if set(baseline) != set(current):
            raise ValueError('Current MOD paths differ from historical public.3 input')
        changed = sorted(name for name in current if name != '_metadata'
                         and baseline[name]['sha256'] != current_hashes[name])
        if set(changed) != set(HELPERS):
            raise ValueError('Current MOD change set must be exactly the two reviewed display helpers: ' + repr(changed))
        for asset, source_rel in HELPERS.items():
            if files[prefix + asset] != files[source_rel]:
                raise ValueError('Generated helper differs from compatibility source: ' + asset)
        before_meta = (baseline_dir / '_metadata').read_bytes()
        current_meta = current['_metadata']
        if packaging.canonical_json(before_meta) != packaging.canonical_json(current_meta):
            raise ValueError('Current _metadata differs from historical public.3')
        baseline_delta = {asset: baseline[asset]['sha256'] for asset in HELPERS}

    main_pak, main_roundtrip = packaging.build_verified_pak(files, tools_dir, output_dir)
    font_pak, font_roundtrip = packaging.build_verified_font_pak(files, tools_dir, output_dir)
    if font_pak is None:
        raise ValueError('Optional font is present by policy but did not produce a PAK')
    # The current install guide is version-specific; package it under the familiar root name.
    files['docs/INSTALL_JA.txt'] = files['docs/limited-repair/INSTALL_JA_public4.txt']
    install_files = packaging.pak_install_files(files, main_pak, font_pak)
    # Keep the package focused on install materials; all raw MOD trees were removed above.
    payload = {name: data for name, data in install_files.items()
               if name.startswith(('mods/', 'optional/', 'LICENSES/')) or name in {
                   'README_JA.md', 'INSTALL_JA.txt', 'PAK_DISTRIBUTION.md', 'CHANGELOG.md',
                   'LICENSE.md', 'THIRD_PARTY_NOTICES.md', 'MIT-tools.txt',
                   '2026-11-07-user-report.md', 'machine_translation/README.md',
                   'machine_translation/model_provenance.json'}
               or name.startswith('limited-repair/')}
    for source, destination in (
        ('docs/limited-repair/FU_Japanese_0.2.4-public.4.md','limited-repair/FU_Japanese_0.2.4-public.4.md'),
        ('docs/limited-repair/INSTALL_JA_public4.txt','limited-repair/INSTALL_JA_public4.txt'),
    ):
        payload[destination] = files[source]
    artifact = packaging.write_zip(archive, PAK_RELEASE_ID, payload)
    pak_record = {
        'release_id': PAK_RELEASE_ID, 'mod_version': json.loads(files['mods/FU_Japanese/_metadata'])['version'],
        'official_tools': {str(p): file_sha(p) for p in (tools_dir/'asset_packer.exe', tools_dir/'asset_unpacker.exe')},
        'packages': [
            {'path':'mods/FU_Japanese.pak', 'pak_sha256':packaging.sha(main_pak), 'pak_bytes':len(main_pak), 'verification':main_roundtrip},
            {'path':'optional/FU_Japanese_Font.pak', 'pak_sha256':packaging.sha(font_pak), 'pak_bytes':len(font_pak), 'verification':font_roundtrip},
        ],
    }
    verification_path.write_text(json.dumps(pak_record, indent=2) + '\n', encoding='utf-8', newline='\n')
    report = {
        'schema':1, 'release_id':RELEASE_ID, 'pak_release_id':PAK_RELEASE_ID, 'prerelease':True,
        'baseline_zip_sha256':BASELINE_ZIP_SHA256, 'input_pak_sha256':BASELINE_PAK_SHA256,
        'changed_game_assets':changed, 'baseline_helper_sha256':baseline_delta,
        'current_helper_sha256':{asset:current_hashes[asset] for asset in HELPERS},
        'all_other_game_assets_unchanged':True, 'metadata_type_sensitive_equal':True,
        'pak_distribution':pak_record, 'artifact':artifact,
        'upload_allowlist':[archive.name], 'native_game_executed':False,
        'whole_mod_rebuilt':False, 'multiplayer_disconnect_cause_verified':False,
    }
    generation_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    sums_path.write_text(f"{artifact['sha256']}  {archive.name}\n", encoding='ascii', newline='\n')
    manifest = {'release_id':RELEASE_ID, 'prerelease':True, 'artifacts':[artifact],
                'upload_allowlist':[archive.name], 'checksum_file':sums_path.name,
                'verification_report':verification_path.name, 'generation_report':generation_path.name}
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({'generation_report':str(generation_path), **report}, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--output-dir', type=Path, default=ROOT/'dist/public4-local')
    parser.add_argument('--pak-tools-dir', type=Path, default=TOOLS_DEFAULT)
    args = parser.parse_args()
    create(args.root, args.output_dir, args.pak_tools_dir)
