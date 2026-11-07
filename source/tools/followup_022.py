"""Apply reviewed guide/race display additions after the pinned base build.

Every replacement is pinned to its baseline and result hashes. This avoids
silently overwriting later edits to a generated file during a rebuild.
"""
import hashlib
import json
from pathlib import Path
import re


def digest(data):
    return hashlib.sha256(data).hexdigest()


def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def read_manifest(project):
    file = Path(project)/'source/followup_022_manifest.json'
    return json.loads(file.read_text(encoding='utf-8')) if file.exists() else None


def context_overrides(project):
    manifest = read_manifest(project) or {}
    return {(r['asset'], r['path'], r['source']): r['translation']
            for r in manifest.get('field_overrides', [])}


def normalized_text(value):
    return re.sub(r'[ \t\r\n\v\f]+', ' ', value).strip(' ')


def patch_allowances(project):
    manifest = read_manifest(project) or {}
    allowed = set()
    for r in manifest.get('patch_translations', []):
        # Only whitespace variants of an explicitly reviewed display string.
        assert normalized_text(r['source']) == normalized_text(r['canonical_source'])
        allowed.add((r['asset'], r['path'], r['source'], r['translation']))
    return allowed


def apply(project, mod, retained_rows=None):
    project, mod = Path(project), Path(mod)
    manifest = read_manifest(project)
    if not manifest:
        return None
    payload = project/'compat/followup_022'
    plan = []
    for row in manifest['files']:
        rel = Path(row['asset'])
        if rel.is_absolute() or '..' in rel.parts:
            raise ValueError('Unsafe display asset path')
        data = (payload/rel).read_bytes()
        if digest(data) != row['output_sha256']:
            raise ValueError('Reviewed display payload changed: '+str(rel))
        dest = mod/rel
        current = digest(dest.read_bytes()) if dest.exists() else None
        if current not in {row.get('baseline_sha256'), row['output_sha256']}:
            raise ValueError('Base display asset changed; review before overriding: '+str(rel))
        plan.append((dest, data, row))
    overrides = context_overrides(project)
    translated_file = project/'source/translated_catalog.jsonl'
    translated = [json.loads(line) for line in translated_file.read_text().splitlines()]
    catalog = [json.loads(line) for line in (project/'source/catalog.jsonl').read_text().splitlines()]
    originals = {(r['asset'], r['path'], r['source']): r for r in catalog}
    selected = {(r['asset'], r['path'], r['source']): r for r in translated}
    if not set(overrides) <= set(originals):
        raise ValueError('Display overrides must refer to existing catalog fields: '+str(set(overrides)-set(originals)))
    if retained_rows is None:
        retained_rows = json.loads((project/'reports/retained.json').read_text())
    retained = {r['id']: r for r in retained_rows}
    for key, target in overrides.items():
        row = originals[key]
        if target == row['source']:
            selected.pop(key, None)
            retained[row['id']] = {**row, 'reason':'unchanged_name_or_retained_source', 'method':'manual',
                                   'decision':'chemical_or_species_formula' if target == 'Ne' else 'retained_source_not_prose'}
        else:
            selected[key] = {**row, 'translation':target, 'method':'manual'}
            retained.pop(row['id'], None)
    translated = [selected[key] for key in originals if key in selected]
    for dest, data, row in plan:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    translated_file.write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in translated), encoding='utf-8')
    dump(project/'reports/retained.json', sorted(retained.values(), key=lambda r:(r['asset'],r['path'],r['source'])))
    lua_path = project/'reports/lua_validation.json'
    lua = json.loads(lua_path.read_text())
    existing = {r['asset']: r for r in lua['files']}
    support = {r['asset']: r for r in lua['support_assets']}
    for row in manifest['files']:
        asset = row['asset']
        if asset in existing:
            existing[asset]['localized_sha256'] = row['output_sha256']
            existing[asset]['display_followup'] = '0.2.2'
        elif not asset.endswith('.patch'):
            support[asset] = {'asset':asset, 'sha256':row['output_sha256'], 'display_followup':'0.2.2'}
    lua['support_assets'] = sorted(support.values(), key=lambda r:r['asset'])
    lua['file_count'] = len({r['asset'] for r in lua['files']+lua['support_assets'] if r['asset'].endswith('.lua')})
    lua['followup_022'] = {
        'manifest':'source/followup_022_manifest.json',
        'scope':'Known guide/species text at display boundaries only; unknown text and gameplay data are preserved.',
        'runtime_tested':False,
    }
    dump(lua_path, lua)
    report = {'version':'0.2.2', 'files':len(plan), 'contextual_translation_updates':len(overrides),
              'approved_patch_translation_groups':len(manifest.get('patch_translations', [])), 'runtime_tested':False}
    dump(project/'reports/followup_022_build.json', report)
    return report
