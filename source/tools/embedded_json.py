#!/usr/bin/env python3
"""Localize display leaves inside Tiled's JSON-encoded parameters strings.

Tiled map properties often encode a second JSON object in a string. Ordinary
JSON Patch cannot address those inner leaves. The complete outer string is
therefore guarded, parsed, changed at approved string paths, then serialized.
Asset identifiers, numeric values, booleans and object structure stay intact.
"""
from __future__ import annotations

import argparse
import collections
import copy
import hashlib
import json
from pathlib import Path

import pyjson5

from common import dump, has_words, ptr, read_asset, sanitize, unptr, walk


def parse_parameters(source):
    try:
        return json.loads(source)
    except json.JSONDecodeError:
        return pyjson5.loads(sanitize(source))


def display_leaf(parts, source):
    if not parts or not has_words(source):
        return False
    key = parts[-1]
    if key.lower().endswith('description') or key in {'npcname', 'shortdescription', 'displayName', 'senderName', 'bookmarkName'}:
        return True
    if any(p in {'dialog', 'Dialog', 'chatOptions', 'chatStrings'} for p in parts[:-1]):
        return not source.startswith('dialog.')
    if key == 'text' and any(p in {'radioMessages', 'gui', 'paneLayout', 'paneLayoutOverride'} for p in parts):
        return True
    if any(p in {'gui', 'paneLayout', 'paneLayoutOverride'} for p in parts) and key in {'title', 'subtitle', 'caption', 'hint', 'tooltip'}:
        return True
    return False


def extract(upstream, destination):
    upstream, destination = Path(upstream), Path(destination)
    records = []
    report = {'map_files': 0, 'encoded_parameters_scanned': 0, 'encoded_parse_errors': [],
              'containers_with_display_text': 0, 'display_fields': 0}
    for source_path in sorted((upstream / 'dungeons').rglob('*.json')):
        data = read_asset(source_path)
        report['map_files'] += 1
        asset = source_path.relative_to(upstream).as_posix()
        for outer_parts, encoded, parent in walk(data):
            property_name = None
            if outer_parts and outer_parts[-1] == 'value' and isinstance(parent, dict):
                property_name = parent.get('name')
            elif len(outer_parts) >= 2 and outer_parts[-2] == 'properties':
                property_name = outer_parts[-1]
            if property_name != 'parameters' or not encoded.lstrip().startswith(('{', '[')):
                continue
            report['encoded_parameters_scanned'] += 1
            try:
                nested = parse_parameters(encoded)
            except Exception as error:
                report['encoded_parse_errors'].append({'asset': asset, 'path': ptr(outer_parts), 'error': str(error)[:160]})
                continue
            count = 0
            for inner_parts, source, _ in walk(nested):
                if not display_leaf(inner_parts, source):
                    continue
                identity = asset + '\0' + ptr(outer_parts) + '\0' + ptr(inner_parts) + '\0' + source
                records.append({
                    'id': hashlib.sha256(identity.encode()).hexdigest()[:20],
                    'asset': asset, 'path': ptr(outer_parts),
                    'inner_path': ptr(inner_parts), 'source': source,
                    'container_source': encoded, 'category': 'dungeon_text',
                    'origin': asset, 'kind': 'embedded_json',
                })
                count += 1
            if count:
                report['containers_with_display_text'] += 1
                report['display_fields'] += count
    report['unique_source_strings'] = len({r['source'] for r in records})
    destination.mkdir(parents=True, exist_ok=True)
    (destination / 'embedded_catalog.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in records), encoding='utf-8')
    dump(destination / 'embedded_extraction_report.json', report)
    return records, report


def _get(tree, path):
    for part in unptr(path):
        tree = tree[int(part)] if isinstance(tree, list) else tree[part]
    return tree


def _set(tree, path, value):
    parts = unptr(path)
    for part in parts[:-1]:
        tree = tree[int(part)] if isinstance(tree, list) else tree[part]
    last = int(parts[-1]) if isinstance(tree, list) else parts[-1]
    tree[last] = value


def _differences(before, after, parts=()):
    if type(before) is not type(after):
        yield ptr(parts), before, after
    elif isinstance(before, dict):
        if before.keys() != after.keys():
            yield ptr(parts), before, after
        else:
            for key in before:
                yield from _differences(before[key], after[key], parts + (key,))
    elif isinstance(before, list):
        if len(before) != len(after):
            yield ptr(parts), before, after
        else:
            for i, (left, right) in enumerate(zip(before, after)):
                yield from _differences(left, right, parts + (str(i),))
    elif before != after:
        yield ptr(parts), before, after


def build_patches(records, translations):
    """Return (patches_by_asset, manifest, report).

    ``translations`` maps original display strings to already-validated Japanese.
    Missing/unchanged entries are retained. Call the common translation validator
    before passing the map here, just as for ordinary JSON display fields.
    ``manifest`` records both original and replacement outer strings, so an
    independent validator can verify each complete test/replace group.
    """
    groups = collections.defaultdict(list)
    for record in records:
        groups[(record['asset'], record['path'], record['container_source'])].append(record)
    patches = collections.defaultdict(list)
    manifest = []
    translated_fields = 0
    for (asset, outer_path, source), fields in sorted(groups.items()):
        original = parse_parameters(source)
        result = copy.deepcopy(original)
        expected = {}
        for record in fields:
            target = translations.get(record['source'])
            if target is None or target == record['source']:
                continue
            if not isinstance(target, str):
                raise TypeError(f'Non-string translation for {record["id"]}')
            if _get(original, record['inner_path']) != record['source']:
                raise ValueError(f'Original nested source mismatch: {record["id"]}')
            _set(result, record['inner_path'], target)
            expected[record['inner_path']] = (record['source'], target)
        if not expected:
            continue
        actual = {path: (left, right) for path, left, right in _differences(original, result)}
        if actual != expected:
            raise ValueError(f'Non-display nested change in {asset}: {outer_path}')
        encoded = json.dumps(result, ensure_ascii=False, separators=(',', ':'))
        # Re-parse serialized output and check the complete tree, including types.
        reparsed = json.loads(encoded)
        if list(_differences(result, reparsed)):
            raise ValueError(f'Nested JSON serialization changed a value in {asset}')
        patches[asset].append([
            {'op': 'test', 'path': outer_path, 'value': source},
            {'op': 'replace', 'path': outer_path, 'value': encoded},
        ])
        manifest.append({'asset': asset, 'path': outer_path, 'source': source,
                         'target': encoded, 'display_changes': [
                             {'path': path, 'source': pair[0], 'target': pair[1]}
                             for path, pair in sorted(expected.items())]})
        translated_fields += len(expected)
    report = {'catalog_entries': len(records), 'translated_fields': translated_fields,
              'retained_fields': len(records) - translated_fields,
              'patched_containers': len(manifest), 'patch_assets': len(patches),
              'non_display_changes': 0}
    return dict(patches), manifest, report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('upstream')
    parser.add_argument('destination')
    args = parser.parse_args()
    _, report = extract(args.upstream, args.destination)
    print(json.dumps(report, ensure_ascii=False, indent=2))
