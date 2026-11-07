#!/usr/bin/env python3
"""Build a guarded Starbound localization mod from auditable translations."""
import argparse
import os
import collections
import hashlib
import json
import re
import shutil
from pathlib import Path
from common import PROTECTED, tokens, dump
from namegen_safety import assert_safe_namegen_translation, retired_character_name_assets

UPSTREAM_COMMIT = '17868d86c9bb7bc00f92038fb78b48cebd1b41b8'
MOD_VERSION = '0.2.3'
# Check numeric magnitudes here. Signs/percent in machine output are checked
# separately by the MT audit; reviewed Japanese may express "+1" as "1増加".
# A period after "approx." or an ellipsis is not a decimal point.
NUMBERS = re.compile(r'(?<![A-Za-z_.])\.\d+|\d+(?:[.,]\d+)*')
COLORS = re.compile(r'\^[^;\n]*;')
RESIDUAL_MARKERS = re.compile(r'__(?:PH|TERM|NUM|KEEP)\d+__|\b(?:ZXQ|QZX)\d+(?:ZXQ|QZX)\b')


def load_mapping(path):
    path = Path(path)
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding='utf-8'))
    if isinstance(data, dict):
        return data
    return {r['source']:r.get('translation',r.get('ja')) for r in data}


def number_list(value):
    return NUMBERS.findall(PROTECTED.sub('', value))


def check_translation(source, target):
    problems = []
    if not isinstance(target, str) or not target.strip():
        return ['empty_or_nonstring_translation']
    if collections.Counter(tokens(source)) != collections.Counter(tokens(target)):
        problems.append('protected_token_mismatch')
    if COLORS.findall(source) != COLORS.findall(target):
        problems.append('color_sequence_mismatch')
    if source.count('\n') != target.count('\n'):
        problems.append('newline_count_mismatch')
    if collections.Counter(number_list(source)) - collections.Counter(number_list(target)):
        problems.append('source_numeric_value_missing')
    if RESIDUAL_MARKERS.search(target):
        problems.append('temporary_marker_leftover')
    if '\ufffd' in target or '\x00' in target:
        problems.append('invalid_output_character')
    return problems


def term_translation(source, glossary):
    # A display name can be surrounded by color tags and layout spaces.
    match = re.fullmatch(r'((?:(?:\^[^;\n]*;)|\s)*)(.*?)((?:(?:\^[^;\n]*;)|\s)*)', source, re.S)
    if not match:
        return None
    leading, core, trailing = match.groups()
    found = glossary.get(core.casefold())
    if found is not None:
        return leading + found + trailing
    # Consistent ore/bar names without touching item IDs.
    for suffix, japanese in [(' Bar','インゴット'),(' Ore','鉱石')]:
        if core.casefold().endswith(suffix.casefold()):
            material = glossary.get(core[:-len(suffix)].casefold())
            if material:
                return leading + material + japanese + trailing
    return None


def build(project, upstream, machine_path, out):
    project, upstream, out = Path(project), Path(upstream), Path(out)
    catalog_bytes = (project/'source/catalog.jsonl').read_bytes()
    catalog = [json.loads(line) for line in catalog_bytes.decode('utf-8').splitlines()]
    # Reject unsafe historical catalogs before deleting or writing output.
    for row in catalog:
        assert_safe_namegen_translation(row['asset'], row['path'])
    append_catalog = project/'source/append_catalog.jsonl'
    if append_catalog.exists():
        for line in append_catalog.read_text(encoding='utf-8').splitlines():
            row = json.loads(line)
            assert_safe_namegen_translation(row['asset'], row['path'])
    machine = load_mapping(machine_path)
    partial = {}
    partial_methods = {}
    for path in sorted((project/'source').glob('partial_*.json')):
        mapping = load_mapping(path)
        partial.update(mapping)
        partial_methods.update({key:('machine_terminology' if path.name=='partial_residual_terms.json' else 'machine_repaired') for key in mapping})
    manual = {}
    for path in sorted((project/'source').glob('manual_*.json')):
        manual.update(load_mapping(path))
    glossary = {k.casefold():v for k,v in load_mapping(project/'source/glossary.json').items()}
    def select_translation(source):
        method = 'machine'
        target = machine.get(source)
        if isinstance(target, dict):
            target = target.get('translation', target.get('ja'))
        if source in partial:
            target, method = partial[source], partial_methods[source]
        term = term_translation(source, glossary)
        if term is not None:
            target, method = term, 'glossary'
        if source in manual:
            target, method = manual[source], 'manual'
        return target, method
    patches = collections.defaultdict(list)
    results = []
    kept = []
    rejected = []
    selected = []
    for row in catalog:
        source = row['source']
        target, method = select_translation(source)
        if target is None:
            kept.append({**row,'reason':'not_translated'})
            continue
        issues = check_translation(source,target)
        if issues:
            rejected.append({**row,'translation':target,'method':method,'reasons':issues})
            continue
        if target == source:
            kept.append({**row,'reason':'unchanged_name_or_retained_source','method':method})
            continue
        if not re.search(r'[\u3040-\u30ff\u3400-\u9fff]',PROTECTED.sub('',target)):
            kept.append({**row,'reason':'no_japanese_output','method':method})
            continue
        group = [
            {'op':'test','path':row['path'],'value':source},
            {'op':'replace','path':row['path'],'value':target}
        ]
        patches[row['asset']].append(group)
        result = {**row,'translation':target,'method':method}
        results.append(result)
        selected.append({k:result[k] for k in ('id','asset','path','source','translation','category','method','origin')})
    if out.exists():
        # Output must be a task-owned generated directory, never a game directory.
        if out.name != 'FU_Japanese':
            raise ValueError('Refusing to clean a directory not named FU_Japanese')
        shutil.rmtree(out)
    out.mkdir(parents=True)
    # Replace old character-name patches during in-place updates as well.
    # Empty patches leave the original training data and generator rules together.
    for asset in retired_character_name_assets(project):
        dump(out/(asset+'.patch'), [])
    for asset, groups in sorted(patches.items()):
        if Path(asset).is_absolute() or '..' in Path(asset).parts:
            raise ValueError('Unsafe asset path: ' + asset)
        dump(out/(asset+'.patch'),groups)
    from append_localization import build as build_appends
    append_report = build_appends(project, upstream, out, select_translation, check_translation)
    embedded_report = None
    embedded_path = project/'source/embedded_catalog.jsonl'
    if embedded_path.exists():
        from embedded_json import build_patches as build_embedded
        embedded_rows = [json.loads(line) for line in embedded_path.read_text(encoding='utf-8').splitlines()]
        embedded_translations = {}
        for row in embedded_rows:
            target, method = select_translation(row['source'])
            if target is not None:
                problems = check_translation(row['source'], target)
                if problems:
                    raise ValueError('Invalid embedded display translation: ' + str(problems))
                embedded_translations[row['source']] = target
        extra_patches, embedded_manifest, embedded_report = build_embedded(embedded_rows, embedded_translations)
        for asset, groups in extra_patches.items():
            destination = out/(asset+'.patch')
            existing = json.loads(destination.read_text(encoding='utf-8')) if destination.exists() else []
            dump(destination, existing + groups)
        dump(project/'reports/embedded_manifest.json', embedded_manifest)
        dump(project/'reports/embedded_coverage.json', embedded_report)
    adaptations_path = project/'source/authored_adaptations.json'
    adaptations = json.loads(adaptations_path.read_text(encoding='utf-8')) if adaptations_path.exists() else []
    for row in adaptations:
        # A hash records the exact reviewed source without redistributing the
        # long third-party quotation that this original Japanese dialogue replaces.
        from common import read_asset
        from jsonpointer import resolve_pointer
        original = resolve_pointer(read_asset(upstream/row['asset']), row['path'])
        if hashlib.sha256(original.encode()).hexdigest() != row['upstream_sha256']:
            raise ValueError('Authored adaptation source changed: ' + row['asset'] + row['path'])
        if tokens(original) != tokens(row['translation']):
            raise ValueError('Authored dialogue must preserve the original display commands')
        destination = out/(row['asset']+'.patch')
        existing = json.loads(destination.read_text(encoding='utf-8')) if destination.exists() else []
        existing.append([{'op':'test','path':row['path']},
                         {'op':'replace','path':row['path'],'value':row['translation']}])
        dump(destination, existing)
    ui_report = None
    if (project/'source/ui_image_labels.json').exists():
        from ui_image_labels import build_patches as build_ui_labels
        ui_patches, ui_manifest, ui_report = build_ui_labels(project, upstream)
        for asset, groups in ui_patches.items():
            destination = out/(asset+'.patch')
            existing = json.loads(destination.read_text(encoding='utf-8')) if destination.exists() else []
            dump(destination, existing + groups)
    dump(out/'_metadata',{
        'name':'FUJapaneseTranslation2026',
        'friendlyName':"Frackin' Universe 日本語化 - 非公式版",
        'author':'Japanese localization generated and reviewed with ChatGPT; FU by Sayter and contributors',
        'version':MOD_VERSION+'-fu6.5.8',
        'description':'FU 6.5.8 (17868d8) Japanese localization: JSON, Lua display strings, NPC status, Pandora dialogue, and UI image-label replacements. Machine translation plus individually reviewed Japanese. Japanese font required.',
        # Localization must not prevent the base game from starting when the
        # Workshop content is unavailable. Includes is optional load ordering.
        'requires':[],
        'includes':['FrackinUniverse'],
        'priority':1000
    })
    for asset in ('zb/zb_textTyper.lua', 'interface/scripted/sbvn/pandorasboxsbvngui.lua'):
        compat = project/'compat'/asset
        if compat.exists():
            (out/asset).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(compat,out/asset)
    # Lua's display aliases reuse the validated current JSON pet-status text.
    (project/'source/translated_catalog.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in selected),encoding='utf-8')
    lua_report = None
    lua_staging = project/'lua-build'
    if (project/'source/lua_manifest.json').exists():
        from lua_localization import build as build_lua
        lua_report = build_lua(upstream, project, lua_staging)
    if lua_staging.exists():
        declared_assets = ([r['asset'] for r in lua_report['files']] +
                           [r['asset'] for r in lua_report['support_assets']]) if lua_report else []
        if len(declared_assets)!=len(set(declared_assets)):
            raise ValueError('Duplicate Lua output manifest entries')
        for name in sorted(declared_assets):
            asset = Path(name)
            file = lua_staging/asset
            if (out/asset).exists():
                if (out/asset).read_bytes()==file.read_bytes():
                    continue
                raise ValueError('Two modules overwrite the same asset differently: ' + str(asset))
            (out/asset).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(file,out/asset)
    shutil.copy2(upstream/'LICENSE.txt',out/'LICENSE-FU-CC-BY-4.0.txt')
    (out/'ATTRIBUTION.txt').write_text(
        "Frackin' Universe Japanese Translation (unofficial)\n\n"
        "Original work: Frackin' Universe by Sayter and the Frackin' Universe contributors.\n"
        "Source: https://github.com/sayterdarkwynd/FrackinUniverse\n"
        f"Revision: {UPSTREAM_COMMIT}\n"
        "Upstream metadata version: 6.5.8\n"
        "Original license: Creative Commons Attribution 4.0 International.\n"
        "https://creativecommons.org/licenses/by/4.0/\n"
        "Full original contributor credits: https://github.com/sayterdarkwynd/FrackinUniverse/blob/" + UPSTREAM_COMMIT + "/_FUcredits.config\n\n"
        "Changes: Japanese display text in JSON, selected Lua literals and display-boundary lookups; "
        "guarded JSON patches, nested Tiled parameters, array-added text, and UI captions; "
        "UTF-8 compatibility changes to zb/zb_textTyper.lua and the Pandora SBVN renderer.\n"
        "Translation produced for this request using FuguMT machine translation and ChatGPT review. "
        "New translation text, original replacement dialogue and adapted FU scripts are distributed under CC BY 4.0.\n"
        "This build is not endorsed by the original authors or Chucklefish.\n",
        encoding='utf-8')
    from followup_022 import apply as apply_followup_022
    followup_report = apply_followup_022(project, out, retained_rows=kept)
    if followup_report:
        results = [json.loads(line) for line in (project/'source/translated_catalog.jsonl').read_text(encoding='utf-8').splitlines()]
        lua_report = json.loads((project/'reports/lua_validation.json').read_text(encoding='utf-8'))
        kept = json.loads((project/'reports/retained.json').read_text(encoding='utf-8'))
    report = {
        'upstream_commit':UPSTREAM_COMMIT,
        'upstream_metadata_version':'6.5.8',
        'mod_output':Path(os.path.relpath(out.resolve(), project.resolve())).as_posix(),
        'catalog_entries':len(catalog),
        'catalog_sha256':hashlib.sha256(catalog_bytes).hexdigest(),
        'catalog_unique_sources':len({r['source'] for r in catalog}),
        'translated_entries':len(results),
        'translated_unique_sources':len({r['source'] for r in results}),
        'patch_files':len(patches),
        'methods_entries':dict(collections.Counter(r['method'] for r in results)),
        'methods_unique_sources':{m:len({r['source'] for r in results if r['method']==m}) for m in ('manual','glossary','machine_repaired','machine_terminology','machine')},
        'categories':{c:{'extracted':sum(r['category']==c for r in catalog),'translated':sum(r['category']==c for r in results)} for c in sorted({r['category'] for r in catalog})},
        'retained_entries':len(kept),
        'retained_reasons':dict(collections.Counter(r['reason'] for r in kept)),
        'rejected_entries':len(rejected),
        'rejected_reasons':dict(collections.Counter(x for r in rejected for x in r['reasons'])),
        'runtime_tested':False,
        'followup_022':followup_report,
        'baseline_runtime_confirmation':{'version':'0.1.1','confirmed_by':'user','scope':'Game starts and Japanese text is displayed; not an exhaustive screen audit.'},
        'append_coverage':append_report,
        'embedded_coverage':embedded_report,
        'authored_dialogue_adaptations':len(adaptations),
        'ui_image_label_coverage':ui_report,
        'lua_coverage':{k:v for k,v in (lua_report or {}).items() if k not in {'files','support_assets'}},
        'notes':['Main counts refer to extracted JSON display fields. Supplemental Lua, array append, and embedded-JSON reports are separate.', 'Guard probes at multiple possible indices count as one translated source occurrence, not many.', 'Deliberately retained fictional languages, identifiers and abbreviations are documented separately.']
    }
    reports = project/'reports'
    reports.mkdir(exist_ok=True)
    dump(reports/'coverage.json',report)
    dump(reports/'rejected.json',rejected)
    dump(reports/'retained.json',kept)
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--project',required=True)
    p.add_argument('--upstream',required=True)
    p.add_argument('--machine',required=True)
    p.add_argument('--output',required=True)
    args=p.parse_args()
    build(args.project,args.upstream,args.machine,args.output)
