"""Localize FU array additions using exact, hash-pinned installed-asset pointers.

NPC status lines use an exact runtime lookup. Indexed sources are resolved by
append_index_basis.py against the complete installed layer order.
"""
from __future__ import annotations

import collections
import hashlib
import itertools
import json
import re
from pathlib import Path

from common import PROTECTED, dump, ptr, unptr

NPC_SCRIPT = 'scripts/actions/npc.lua'
NPC_MARKER = '\tnpc.setStatusText(storage.statusText)'


def matching_paths(document, parts, source):
    """Find exact source values at a pointer with a JSON-patch append wildcard."""
    def descend(value, offset, prefix):
        if offset == len(parts):
            if value == source:
                yield ptr(prefix)
            return
        key = parts[offset]
        if key == '-':
            if isinstance(value, list):
                for index, child in enumerate(value):
                    yield from descend(child, offset + 1, prefix + (str(index),))
        elif isinstance(value, dict) and key in value:
            yield from descend(value[key], offset + 1, prefix + (key,))
        elif isinstance(value, list) and key.isdigit() and int(key) < len(value):
            yield from descend(value[int(key)], offset + 1, prefix + (key,))
    return list(descend(document, 0, ()))


def catalog_row(asset, pointer, source, category, origin):
    identity = asset + '\0' + pointer + '\0' + source
    strategy = 'npc_status_lookup' if asset == 'npcs/statuses.config' else 'indexed_guards'
    parts = unptr(pointer)
    if strategy == 'indexed_guards' and parts.count('-') != 1:
        raise ValueError('An append with multiple unknown indices needs a dedicated resolver: ' + asset + pointer)
    return {'id': hashlib.sha256(identity.encode()).hexdigest()[:20],
            'asset': asset, 'path': pointer, 'source': source, 'category': category,
            'origin': origin, 'strategy': strategy}


def paths_for(row, upstream):
    from append_index_plans import paths_for as planned_paths
    return planned_paths(row, upstream)


def lua_quote(value):
    # JSON's UTF-8 strings share the escapes used here with Lua. Do not emit
    # JSON's \\uXXXX escape, which is not a valid Lua string escape.
    return json.dumps(value, ensure_ascii=False).replace('\\/', '/')


def npc_override(original, mapping):
    if original.count(NPC_MARKER) != 1:
        raise ValueError('NPC status writer changed; inspect upstream before building')
    header = ('-- FU Japanese: exact display-text lookup for FU-added NPC status lines.\n'
              '-- Original NPC behavior remains below; source and license are in ATTRIBUTION.txt.\n'
              'local fuJapaneseNpcStatuses = {\n')
    header += ''.join('  [' + lua_quote(k) + '] = ' + lua_quote(v) + ',\n'
                      for k, v in sorted(mapping.items()))
    header += '}\n\n'
    insertion = ('\t-- Localize only the displayed status; unknown values remain unchanged.\n'
                 '\tstorage.statusText = fuJapaneseNpcStatuses[storage.statusText] or storage.statusText\n')
    return header + original.replace(NPC_MARKER, insertion + NPC_MARKER)


def build_asset_groups(project, asset, select_translation, check_translation, basis):
    from namegen_safety import assert_safe_namegen_translation
    path = Path(project) / 'source/append_catalog.jsonl'
    rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()] if path.exists() else []
    translated, retained, rejected = [], [], []
    groups = []
    for row in rows:
        if row['asset'] != asset or row['strategy'] != 'indexed_guards':
            continue
        assert_safe_namegen_translation(row['asset'], row['path'])
        target, method = select_translation(row['source'])
        if target is None:
            retained.append({**row, 'reason':'not_translated'})
            continue
        issues = check_translation(row['source'], target)
        if issues:
            rejected.append({**row, 'translation':target, 'reasons':issues})
            continue
        if target == row['source'] or not re.search(r'[\u3040-\u30ff\u3400-\u9fff]', PROTECTED.sub('', target)):
            retained.append({**row, 'reason':'not_japanese_output', 'translation':target})
            continue
        paths = paths_for(row, basis)
        for pointer in paths:
            assert_safe_namegen_translation(row['asset'], pointer)
            groups.append([{'op':'test','path':pointer,'value':row['source']},
                           {'op':'replace','path':pointer,'value':target}])
        translated.append({**row,'translation':target,'method':method,'generated_paths':paths})
    return groups, translated, retained, rejected


def build(project, upstream, out, select_translation, check_translation, basis_path=None):
    from namegen_safety import assert_safe_namegen_translation
    project, upstream, out = map(Path, (project, upstream, out))
    path = project / 'source/append_catalog.jsonl'
    basis_path = Path(basis_path) if basis_path else project / 'source/append_index_basis.json'
    if not basis_path.is_file():
        raise ValueError('Capture installed append assets before building: ' + str(basis_path))
    basis = json.loads(basis_path.read_text(encoding='utf-8'))
    path = project / 'source/append_catalog.jsonl'
    rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()] if path.exists() else []
    translated, retained, rejected = [], [], []
    groups = collections.defaultdict(list)
    statuses = {}
    for row in rows:
        assert_safe_namegen_translation(row['asset'], row['path'])
        target, method = select_translation(row['source'])
        if target is None:
            retained.append({**row, 'reason': 'not_translated'})
            continue
        issues = check_translation(row['source'], target)
        if issues:
            rejected.append({**row, 'translation': target, 'reasons': issues})
            continue
        if target == row['source']:
            retained.append({**row, 'reason': 'deliberately_retained'})
            continue
        if not re.search(r'[\u3040-\u30ff\u3400-\u9fff]',PROTECTED.sub('',target)):
            retained.append({**row, 'reason': 'no_japanese_output', 'translation':target})
            continue
        paths = paths_for(row, basis)
        for pointer in paths:
            assert_safe_namegen_translation(row['asset'], pointer)
            groups[row['asset']].append([
                {'op': 'test', 'path': pointer, 'value': row['source']},
                {'op': 'replace', 'path': pointer, 'value': target}])
        if row['strategy'] == 'npc_status_lookup':
            statuses[row['source']] = target
        translated.append({**row, 'translation': target, 'method': method, 'generated_paths': paths})
    for asset, extra in groups.items():
        destination = out / (asset + '.patch')
        current = json.loads(destination.read_text(encoding='utf-8')) if destination.exists() else []
        dump(destination, current + extra)
    if statuses:
        original = (upstream / NPC_SCRIPT).read_text(encoding='utf-8')
        modified = npc_override(original, statuses)
        destination = out / NPC_SCRIPT
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(modified, encoding='utf-8',newline='\n')
        dump(project / 'reports/npc_status_override.json', {
            'upstream_asset': NPC_SCRIPT,
            'upstream_sha256': hashlib.sha256((upstream / NPC_SCRIPT).read_bytes()).hexdigest(),
            'output_sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
            'translated_status_values': len(statuses),
            'method': 'Exact dictionary lookup immediately before existing status display call.'})
    from append_index_plans import summarize
    index_plan = summarize(rows, basis)
    index_plan['translated_groups'] = sum(len(r.get('generated_paths', [])) for r in translated)
    index_plan['basis_file_sha256'] = hashlib.sha256(basis_path.read_bytes()).hexdigest()
    dump(project / 'reports/append_index_plan.json', index_plan)
    report = {'catalog_entries': len(rows), 'translated_entries': len(translated),
              'translated_unique_sources': len({r['source'] for r in translated}),
              'npc_status_values': len(statuses), 'additional_guarded_groups': sum(map(len, groups.values())),
              'index_plan_report': 'append_index_plan.json', 'retained': retained, 'rejected': rejected,
              'scope': 'FU-added array values. Guard probes are not counted as separate translations.'}
    dump(project / 'reports/append_coverage.json', report)
    (project / 'source/append_translated_catalog.jsonl').write_text(
        ''.join(json.dumps(row, ensure_ascii=False) + '\n' for row in translated), encoding='utf-8',newline='\n')
    return report
