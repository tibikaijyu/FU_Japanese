#!/usr/bin/env python3
"""Build field-scoped race-information fixes against the distributed 0.2.1.

Only exact known English strings are localized. Native JSON guards also cover
the values obtained when the official raw JSON's physical line endings are
CRLF; escaped JSON \\n sequences remain LF. The Lua display boundary separately
accepts ASCII-whitespace differences in a whole, known description.
"""
import argparse
import collections
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

import pyjson5
from curation import DESCRIPTIONS, NAMES, LABELS, CHARCREATION, STATWINDOW, DESCRIPTION_TERMS

COMMIT = '17868d86c9bb7bc00f92038fb78b48cebd1b41b8'
STAT = 'interface/scripted/statWindow/statWindow.config'
CREATION = 'interface/windowconfig/charcreation.config'
RACEINFO = 'interface/objectcrafting/fu_racialiser/fu_raceinfo.config'
LUA = 'interface/scripted/statWindow/statWindow.lua'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def ptr(parts):
    return ''.join('/' + str(x).replace('~', '~0').replace('/', '~1') for x in parts)


def walk(value, parts=()):
    if isinstance(value, dict):
        for k, v in value.items():
            yield from walk(v, parts+(str(k),))
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from walk(v, parts+(str(i),))
    elif isinstance(value, str):
        yield ptr(parts), value


def patch_ops(value):
    if isinstance(value, list):
        for item in value:
            yield from patch_ops(item)
    elif isinstance(value, dict) and 'op' in value:
        yield value


def parse_preserving_newlines(text):
    """Escape physical control characters only inside JSON string literals."""
    out = []
    quote = comment = None
    escaped = False
    i = 0
    text = text.lstrip('\ufeff')
    while i < len(text):
        c = text[i]
        nxt = text[i+1] if i+1 < len(text) else ''
        if comment == 'line':
            if c == '\n':
                comment = None
                out.append(c)
        elif comment == 'block':
            if c == '*' and nxt == '/':
                comment = None
                out.append(' ')
                i += 1
            elif c in '\r\n':
                out.append(c)
        elif quote is not None:
            if escaped:
                out.append(c)
                escaped = False
            elif c == '\\':
                out.append(c)
                escaped = True
            elif c == quote:
                out.append(c)
                quote = None
            elif c in '\r\n\t':
                out.append({'\r':'\\r', '\n':'\\n', '\t':'\\t'}[c])
            else:
                out.append(c)
        elif c in ('"', "'"):
            quote = c
            out.append(c)
        elif c == '/' and nxt in ('/', '*'):
            comment = 'line' if nxt == '/' else 'block'
            out.append(' ')
            i += 1
        else:
            out.append(c)
        i += 1
    return pyjson5.loads(''.join(out))


def source_fields(raw, is_patch):
    data = parse_preserving_newlines(raw)
    result = collections.defaultdict(list)
    if is_patch:
        for op in patch_ops(data):
            if op.get('op') in {'add', 'replace'} and 'value' in op:
                for tail, value in walk(op['value']):
                    result[op['path']+tail].append(value)
    else:
        for pointer, value in walk(data):
            result[pointer].append(value)
    return result


def normalize(text):
    return re.sub(r'[ \t\r\n\f\v]+', ' ', text).strip(' ')


def build(baseline, upstream, output):
    baseline, upstream, output = map(Path, (baseline, upstream, output))
    sys.path.insert(0, str(baseline/'source/tools'))
    from build import check_translation
    rows = [json.loads(s) for s in (baseline/'source/source/translated_catalog.jsonl').read_text().splitlines()]
    by_id = {r['id']: r for r in rows}
    reviewed_sources = {by_id[k]['source']: v for k, v in DESCRIPTIONS.items()}
    selected = [r for r in rows if (
        r['asset'].startswith('species/') and r['asset'].endswith('.species') or
        r['asset'] in {STAT, CREATION, RACEINFO})]
    output.mkdir(parents=True, exist_ok=True)
    out = output/'out'
    out.mkdir(exist_ok=True)
    fields, overrides, variants = [], [], []
    files = {}
    source_cache = {}
    source_provenance = {}
    display = {'schemaVersion':1, 'version':'0.2.2', 'species':{}}
    reviewed_descriptions = 0
    retained_fields = []

    def patches(asset):
        if asset not in files:
            files[asset] = json.loads((baseline/'mods/FU_Japanese'/(asset+'.patch')).read_text())
        return files[asset]

    for row in selected:
        asset, pointer, source = row['asset'], row['path'], row['source']
        target = row['translation']
        method = 'inherited_v0.2.1'
        reason = None
        species_field = asset.startswith('species/') and asset.endswith('.species')
        if species_field and pointer == '/charCreationTooltip/description':
            if source in reviewed_sources:
                target = reviewed_sources[source]
                method = 'reviewed_description_022'
                reviewed_descriptions += 1
            else:
                for old, new in DESCRIPTION_TERMS.items():
                    target = target.replace(old, new)
                method = 'terminology_022' if target != row['translation'] else method
        elif species_field and pointer.startswith('/charGenTextLabels/'):
            target = LABELS.get(source, target)
            method = 'reviewed_label_022'
        elif species_field and pointer == '/charCreationTooltip/title':
            target = NAMES.get(source, target)
            method = 'reviewed_species_name_022'
        elif species_field and pointer == '/charCreationTooltip/subTitle':
            target = {
                'Ne':'Ne',
                'Insectoid xenophobes':'異種族を嫌う昆虫型の種族',
                'Warrior race from the Kortakk nebula':'コルタック星雲出身の戦士の種族',
                'awwwwwwwww':'かわいい、ふわふわ',
                'Should be murdered.':'排除すべき存在。',
            }.get(source, target)
            method = 'reviewed_subtitle_022'
            if source == 'Ne':
                reason = 'chemical_or_species_formula'
        elif asset == RACEINFO and pointer.endswith('/name') and pointer.count('/') == 3:
            target = NAMES.get(source, target)
            method = 'reviewed_species_name_022' if source in NAMES else method
        elif asset == STAT and pointer.startswith('/gui/'):
            target = STATWINDOW.get(source, target)
            method = 'reviewed_interface_022'
        elif asset == CREATION:
            target = CHARCREATION.get(source, target)
            method = 'reviewed_interface_022'

        issues = check_translation(source, target)
        assert not issues, (asset, pointer, issues)
        revised = {**row, 'translation':target, 'method':method}
        if reason:
            revised['retained_reason'] = reason
            retained_fields.append(revised)
        fields.append(revised)
        if target != row['translation']:
            found = 0
            for group in patches(asset):
                if (len(group) == 2 and group[0].get('op') == 'test' and group[0].get('path') == pointer
                        and group[0].get('value') == source and group[1].get('op') == 'replace'):
                    assert group[1]['value'] == row['translation']
                    group[1]['value'] = target
                    found += 1
            assert found == 1, (asset, pointer, 'expected one old field')
            change = {**revised, 'previous_translation':row['translation']}
            overrides.append(change)

        if not species_field:
            continue
        if pointer in {'/charCreationTooltip/description', '/charCreationTooltip/title'}:
            race = Path(asset).stem
            bucket = display['species'].setdefault(race, {'descriptions':[], 'names':[]})
            key = 'descriptions' if pointer.endswith('/description') else 'names'
            bucket[key].append({'source':source, 'translation':target})
        # Only variants derived from the actual source literal are emitted.
        origin = row['origin']
        if origin not in source_cache:
            raw_bytes = (upstream/origin).read_bytes()
            raw = raw_bytes.decode('utf-8-sig')
            physical_lf = raw.replace('\r\n', '\n')
            windows_raw = physical_lf.replace('\n', '\r\n')
            source_cache[origin] = (source_fields(physical_lf, origin.endswith('.patch')),
                                    source_fields(windows_raw, origin.endswith('.patch')))
            source_provenance[origin] = {'asset':origin, 'sha256':sha(raw_bytes),
                'url':f'https://raw.githubusercontent.com/sayterdarkwynd/FrackinUniverse/{COMMIT}/{origin}'}
        originals, windows = source_cache[origin]
        choices = originals.get(pointer, [])
        matches = [i for i, value in enumerate(choices)
                   if value.replace('\r\n','\n').replace('\r','') == source]
        assert matches, (asset, pointer, 'guard not found in original source')
        for i in matches:
            value = windows[pointer][i]
            if value == source:
                continue
            assert normalize(value) == normalize(source)
            group = [{'op':'test','path':pointer,'value':value},
                     {'op':'replace','path':pointer,'value':target}]
            if group not in patches(asset):
                patches(asset).append(group)
                variants.append({'asset':asset, 'field_id':row['id'], 'path':pointer,
                    'source':value, 'translation':target, 'group':group,
                    'variant':'physical_crlf_preserving_escaped_json_newlines',
                    'origin':origin, 'origin_sha256':source_provenance[origin]['sha256']})

    # Base-game names are display aliases only; species IDs are unchanged.
    for race, name in {'apex':'Apex','avian':'Avian','floran':'Floran','glitch':'Glitch',
                       'human':'Human','hylotl':'Hylotl','novakid':'Novakid',
                       'fenerox':'Fenerox','radien':'Radien','shadow':'Shadow'}.items():
        bucket = display['species'].setdefault(race, {'descriptions':[], 'names':[]})
        alias = {'source':name, 'translation':NAMES[name]}
        if alias not in bucket['names']:
            bucket['names'].append(alias)

    # Equal source text with different line wrapping can share a fallback. Check
    # that the resulting Japanese differs only in ASCII whitespace as well.
    collisions = []
    for race, value in display['species'].items():
        for key in ('descriptions', 'names'):
            seen = {}
            for entry in value[key]:
                n = normalize(entry['source'])
                if n in seen and seen[n] != entry['translation']:
                    strip = lambda s: re.sub(r'[ \t\r\n\f\v]+','',s)
                    assert strip(seen[n]) == strip(entry['translation']), (race, key, 'ambiguous fallback')
                    collisions.append({'race':race, 'field':key, 'reason':'line_wrapping_only'})
                seen[n] = entry['translation']

    for asset, groups in files.items():
        write_json(out/(asset+'.patch'), groups)
    write_json(out/'fujp/species_display.config', display)
    helper = Path(__file__).with_name('species_display.lua')
    (out/'fujp/species_display.lua').write_bytes(helper.read_bytes())
    original_lua = (baseline/'mods/FU_Japanese'/LUA).read_text(encoding='utf-8')
    hooks = [
        ('require "/scripts/util.lua"\n', 'require "/scripts/util.lua"\nrequire "/fujp/species_display.lua"\n'),
        ('\tlocal racialName = (notRecognized and "") or JSON.charCreationTooltip.title\n',
         '\tlocal racialName = (notRecognized and "") or JSON.charCreationTooltip.title\n\tracialName = fuJapaneseSpeciesDisplay.name(race, racialName)\n'),
        ('\tlocal str = JSON.charCreationTooltip.description\n',
         '\tlocal str = JSON.charCreationTooltip.description\n\tstr = fuJapaneseSpeciesDisplay.description(race, str)\n'),
    ]
    lua = original_lua
    for before, after in hooks:
        assert lua.count(before) == 1, before
        lua = lua.replace(before, after)
    (out/LUA).parent.mkdir(parents=True, exist_ok=True)
    (out/LUA).write_text(lua, encoding='utf-8')
    manifest = []
    for path in sorted(out.rglob('*')):
        if not path.is_file(): continue
        relative = path.relative_to(out).as_posix()
        old = baseline/'mods/FU_Japanese'/relative
        if old.exists() and old.read_bytes() == path.read_bytes():
            path.unlink()
            continue
        manifest.append({'asset':relative, 'baseline_sha256':sha(old.read_bytes()) if old.exists() else None,
                         'sha256':sha(path.read_bytes()), 'bytes':path.stat().st_size})
    write_json(output/'field_overrides.json', overrides)
    write_json(output/'normalized_source_variants.json', variants)
    write_json(output/'all_species_display_fields.json', [r for r in fields if r['asset'].startswith('species/')])
    write_json(output/'retained_fields.json', retained_fields)
    write_json(output/'source_provenance.json', list(source_provenance.values()))
    write_json(output/'manifest.json', manifest)
    write_json(output/'lua_hooks.json', {'asset':LUA, 'baseline_sha256':sha(original_lua.encode()),
                                       'output_sha256':sha(lua.encode()), 'changes':[{'before':a,'after':b} for a,b in hooks]})
    summary = {'version':'0.2.2', 'upstream_commit':COMMIT, 'runtime_tested':False,
        'source_provenance_files':len(source_provenance), 'changed_game_files':len(manifest),
        'field_overrides':len(overrides), 'native_line_ending_variants':len(variants),
        'species_with_description_fallback':sum(bool(v['descriptions']) for v in display['species'].values()),
        'description_source_variants':sum(len(v['descriptions']) for v in display['species'].values()),
        'individually_reviewed_description_fields':reviewed_descriptions,
        'retained_symbol_fields':len(retained_fields), 'canonical_layout_collisions':collisions,
        'limits':['No Starbound game runtime was available.',
                  'The uploaded log does not contain the actual untranslated species string; its precise cause remains unconfirmed.',
                  'Fallback accepts only a known race ID and a whole known source text differing solely by ASCII whitespace.',
                  'Unknown updated text and existing Japanese are preserved; no unconditional overwrite is used.',
                  'Third-party compatibility race descriptions retain their previous machine baseline except field-scoped terminology corrections unless their complete source matches an individually reviewed description.']}
    write_json(output/'report.json', summary)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--baseline', required=True)
    p.add_argument('--upstream', required=True)
    p.add_argument('--output', required=True)
    a = p.parse_args()
    build(a.baseline, a.upstream, a.output)
