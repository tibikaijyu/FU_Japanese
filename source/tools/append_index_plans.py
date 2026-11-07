"""Bounded, original-text-guarded index plans for FU's appended display fields.

The vanilla-owned arrays are absent from the FU repository. Celestial names use
published vanilla lengths and the exact pinned FU operations to derive expected
indices, with a small guarded neighborhood for base/version/mod differences.
Other small display arrays have explicit bounded searches. A failed original
value test must skip its individual replacement; it must never rename another
value merely because it occupies a candidate index.
"""
from __future__ import annotations

import collections
import functools
import hashlib
import json
from pathlib import Path

import jsonpatch

from common import ptr, read_asset, unptr


CELESTIAL_BASE = {'systemNames': 587, 'systemSuffixNames': 42}
CELESTIAL_PATCH_SHA256 = '6c3d617e9c5ac6f3ac0aee8c09dfcd50a1f6031d4c565cc48864ded4bd1e4d3d'
CELESTIAL_NEIGHBORHOOD = 8
REFERENCE = {
    'game': 'Starbound vanilla 1.4.x reference array layout',
    'fu_version': '6.5.8',
    'fu_commit': '17868d86c9bb7bc00f92038fb78b48cebd1b41b8',
    'source_url': 'https://www.reddit.com/r/frackinuniverse/comments/1iaat5f',
    'source_date': '2025-01-26 / 2025-01-27',
    'reference_lengths': CELESTIAL_BASE,
    'note': 'Firsthand modding explanation: 587 vanilla system names, FU removes 3; 42 separate suffixes. Exact original text guards are still mandatory.',
}


def _find(document, parts, source, prefix=()):
    if not parts:
        if document == source:
            yield ptr(prefix)
        return
    key, rest = parts[0], parts[1:]
    if key == '-':
        if isinstance(document, list):
            for i, value in enumerate(document):
                yield from _find(value, rest, source, prefix + (str(i),))
    elif isinstance(document, dict) and key in document:
        yield from _find(document[key], rest, source, prefix + (key,))
    elif isinstance(document, list) and key.isdigit() and int(key) < len(document):
        yield from _find(document[int(key)], rest, source, prefix + (key,))


def _ops(value):
    if isinstance(value, list):
        for item in value:
            yield from _ops(item)
    elif isinstance(value, dict) and 'op' in value:
        yield value


@functools.lru_cache(maxsize=4)
def _celestial_document(upstream):
    source = Path(upstream) / 'celestial/names.config.patch'
    if hashlib.sha256(source.read_bytes()).hexdigest() != CELESTIAL_PATCH_SHA256:
        raise ValueError('The pinned FU celestial-name patch changed; re-audit the append index plan.')
    # None placeholders represent unknown vanilla values. Only positions matter;
    # no commercial vanilla asset content is copied or distributed here.
    document = {key: [None] * size for key, size in CELESTIAL_BASE.items()}
    for operation in _ops(read_asset(source)):
        # The pinned patch only uses deterministic add/remove operations.
        if operation['op'] not in {'add', 'remove', 'replace', 'copy', 'move'}:
            raise ValueError('Conditional celestial source patch needs a new explicit index plan.')
        document = jsonpatch.apply_patch(document, [operation])
    return document


@functools.lru_cache(maxsize=256)
def _source_append_count(upstream, origin, array_pointer):
    source = Path(upstream) / origin
    if not source.is_file():
        return 0
    return sum(1 for op in _ops(read_asset(source))
               if op.get('op') == 'add' and op.get('path') == array_pointer + '/-')


def plan_for(row, upstream):
    """Return a reviewable plan, including its concrete candidate JSON pointers."""
    from namegen_safety import assert_safe_namegen_translation
    assert_safe_namegen_translation(row['asset'], row['path'])
    if row.get('strategy') == 'npc_status_lookup' or row['asset'] == 'npcs/statuses.config':
        return {'strategy': 'npc_status_lookup', 'paths': [], 'reason': 'Exact runtime display lookup; array indices are irrelevant.'}
    parts = tuple(unptr(row['path']))
    if parts.count('-') != 1:
        raise ValueError('Exactly one append index is supported: ' + row['asset'] + row['path'])
    position = parts.index('-')
    upstream = str(Path(upstream).resolve())
    if row['asset'] == 'celestial/names.config':
        document = _celestial_document(upstream)
        exact_paths = list(_find(document, parts, row['source']))
        if not exact_paths:
            raise ValueError('FU appended source is absent from pinned celestial operations: ' + row['source'])
        indices = set()
        for path in exact_paths:
            index = int(unptr(path)[position])
            indices.update(range(max(0, index - CELESTIAL_NEIGHBORHOOD), index + CELESTIAL_NEIGHBORHOOD + 1))
        paths = [ptr(tuple(str(i) if p == '-' else p for p in parts)) for i in sorted(indices)]
        return {'strategy': 'celestial_reference_neighborhood', 'paths': paths,
                'reference_paths': exact_paths, 'index_radius': CELESTIAL_NEIGHBORHOOD,
                'source_url': REFERENCE['source_url'],
                'reason': 'Pinned FU operation sequence, including numeric/untranslated additions, applied after reference vanilla lengths.'}

    asset = row['asset']
    array_pointer = ptr(parts[:position])
    append_count = _source_append_count(upstream, row.get('origin', asset + '.patch'), array_pointer)
    if asset.startswith('objects/crafting/') and parts[0] == 'upgradeStages':
        minimum_limit, base_budget = 64, 32
        reason = 'Short crafting stage arrays; guard each possible display field.'
    elif asset.startswith('npcs/crew/'):
        minimum_limit, base_budget = 64, 32
        reason = 'Short crew dialogue arrays; guard each possible exact line.'
    else:
        minimum_limit, base_budget = 256, 128
        reason = 'Weapon names, bounty names and quest pools; bounded original-value search.'
    required = base_budget + append_count
    index_limit = minimum_limit
    while index_limit < required:
        index_limit *= 2
    paths = [ptr(tuple(str(i) if p == '-' else p for p in parts)) for i in range(index_limit)]
    return {'strategy': 'bounded_original_value_search', 'paths': paths,
            'index_limit': index_limit, 'fu_appended_values': append_count,
            'base_and_prior_mod_budget': base_budget, 'reason': reason}


def paths_for(row, upstream):
    return plan_for(row, upstream)['paths']


def summarize(rows, upstream):
    strategies = collections.Counter()
    assets = collections.defaultdict(lambda: {'catalog_entries': 0, 'guard_probes': 0, 'limits': set()})
    for row in rows:
        plan = plan_for(row, upstream)
        strategies[plan['strategy']] += 1
        data = assets[row['asset']]
        data['catalog_entries'] += 1
        data['guard_probes'] += len(plan['paths'])
        if 'index_limit' in plan:
            data['limits'].add(plan['index_limit'])
    for data in assets.values():
        data['limits'] = sorted(data['limits'])
    return {
        'reference': REFERENCE,
        'celestial_source_patch_sha256': CELESTIAL_PATCH_SHA256,
        'celestial_neighbor_radius': CELESTIAL_NEIGHBORHOOD,
        'catalog_entries': len(rows), 'strategies': dict(strategies),
        'guard_probes': sum(data['guard_probes'] for data in assets.values()),
        'assets': dict(sorted(assets.items())),
        'limitations': 'Reference positions and bounded searches do not cover arbitrary large preceding third-party modifications. All generated writes still require exact original-text guards.',
    }
