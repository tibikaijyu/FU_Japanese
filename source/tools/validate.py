#!/usr/bin/env python3
"""Check generated localization structure and text-only changes against FU."""
import argparse
import collections
import copy
import hashlib
import json
from pathlib import Path
import jsonpatch
import jsonpointer
from common import read_asset, dump
from build import check_translation
from namegen_safety import assert_safe_namegen_patch


class TestFailed(Exception):
    pass


def upstream_asset(project, upstream, asset):
    from upstream_overrides import resolve_asset
    return resolve_asset(project, upstream, asset)

def apply_batches(document, operations):
    result = copy.deepcopy(document)
    for op in operations:
        if isinstance(op,list):
            try:
                result = apply_batches(result,op)
            except TestFailed:
                pass
            continue
        if op['op']=='test':
            try:
                actual = jsonpointer.resolve_pointer(result,op['path'])
                matches = 'value' not in op or actual == op['value']
            except (jsonpointer.JsonPointerException,TypeError,KeyError,IndexError):
                matches=False
            if op.get('inverse'):
                matches=not matches
            if not matches:
                raise TestFailed(op['path'])
        else:
            result = jsonpatch.apply_patch(result,[op],in_place=False)
    return result


def diff(before,after,path=''):
    if type(before) is not type(after):
        return [(path,before,after)]
    if isinstance(before,dict):
        if before.keys()!=after.keys():
            return [(path,before,after)]
        return [d for k in before for d in diff(before[k],after[k],path+'/'+str(k).replace('~','~0').replace('/','~1'))]
    if isinstance(before,list):
        if len(before)!=len(after):
            return [(path,before,after)]
        return [d for i,(a,b) in enumerate(zip(before,after)) for d in diff(a,b,path+'/'+str(i))]
    return [] if before==after else [(path,before,after)]


def validate(project,upstream,mod):
    project,upstream,mod=Path(project),Path(upstream),Path(mod)
    rows=[json.loads(l) for l in (project/'source/translated_catalog.jsonl').read_text(encoding='utf-8').splitlines()]
    allowed={(r['asset'],r['path'],r['source'],r['translation']) for r in rows}
    from followup_022 import patch_allowances
    allowed.update(patch_allowances(project))
    append_path=project/'source/append_translated_catalog.jsonl'
    append_rows=[json.loads(l) for l in append_path.read_text(encoding='utf-8').splitlines()] if append_path.exists() else []
    allowed.update((r['asset'],p,r['source'],r['translation']) for r in append_rows for p in r['generated_paths'])
    embedded_file=project/'reports/embedded_manifest.json'
    embedded_rows=json.loads(embedded_file.read_text(encoding='utf-8')) if embedded_file.exists() else []
    embedded={(r['asset'],r['path'],r['source'],r['target']):r for r in embedded_rows}
    allowed.update(embedded)
    adaptation_file=project/'source/authored_adaptations.json'
    adaptations=json.loads(adaptation_file.read_text(encoding='utf-8')) if adaptation_file.exists() else []
    authored={(r['asset'],r['path']):r for r in adaptations}
    ui_manifest_file=project/'reports/ui_image_label_manifest.json'
    ui_rows=json.loads(ui_manifest_file.read_text(encoding='utf-8')) if ui_manifest_file.exists() else []
    def group_identity(asset, group):
        return (asset,json.dumps(group,ensure_ascii=False,sort_keys=True,separators=(',',':')))
    approved_ui={group_identity(r['asset'],r['group']):r for r in ui_rows}
    ui_by_asset=collections.defaultdict(list)
    for row in ui_rows:
        ui_by_asset[row['asset']].append(row)
    summary={
        'patch_files_parsed':0,'guarded_groups_checked':0,
        'known_full_assets_verified':0,'known_full_asset_strings_changed':0,
        'patch_only_assets_without_vanilla_or_other_mod_base':0,
        'source_guard_mismatches_in_known_assets':[],
        'known_asset_source_patch_errors':[],
        'errors':[],'runtime_tested':False,
        'authored_dialogue_groups_checked':0,
        'ui_presentation_groups_checked':0,
    }
    manifest={}
    for file in sorted(mod.rglob('*')):
        if not file.is_file():continue
        rel=file.relative_to(mod).as_posix()
        manifest[rel]=hashlib.sha256(file.read_bytes()).hexdigest()
        if file.suffix!='.patch':continue
        asset=rel[:-6]
        groups=json.loads(file.read_text(encoding='utf-8'))
        # A matching catalog entry cannot authorize a control-ID translation.
        try:
            assert_safe_namegen_patch(asset, groups)
        except ValueError as error:
            summary['errors'].append({'asset':asset,'error':str(error)})
        summary['patch_files_parsed']+=1
        if not isinstance(groups,list):
            summary['errors'].append({'asset':asset,'error':'not_patch_array'})
            continue
        for group in groups:
            ui_entry=approved_ui.get(group_identity(asset,group))
            if ui_entry:
                fixture=read_asset(upstream_asset(project,upstream,asset))
                first_guard=group[0]
                incompatible=jsonpatch.apply_patch(fixture,[{'op':'replace','path':first_guard['path'],'value':'__version_mismatch__'}])
                assert apply_batches(incompatible,[group])==incompatible
                missing=jsonpatch.apply_patch(fixture,[{'op':'remove','path':first_guard['path']}])
                assert apply_batches(missing,[group])==missing
                summary['ui_presentation_groups_checked']+=1
                continue
            if isinstance(group,list) and len(group)==2 and group[0].get('op')=='test' and 'value' not in group[0]:
                a,b=group
                entry=authored.get((asset,a['path']))
                if not entry or b!={'op':'replace','path':a['path'],'value':entry['translation']}:
                    summary['errors'].append({'asset':asset,'error':'unapproved_presence_guarded_dialogue'})
                else:
                    original=jsonpointer.resolve_pointer(read_asset(upstream/asset),a['path'])
                    assert hashlib.sha256(original.encode()).hexdigest()==entry['upstream_sha256']
                    fixture={'text':'Existing quoted dialogue','sentinel':42}
                    mini=[[{**a,'path':'/text'},{**b,'path':'/text'}]]
                    assert apply_batches(fixture,mini)=={'text':entry['translation'],'sentinel':42}
                    assert apply_batches({'sentinel':42},mini)=={'sentinel':42}
                    summary['authored_dialogue_groups_checked']+=1
                continue
            if not isinstance(group,list) or len(group)!=2 or group[0].get('op')!='test' or group[1].get('op')!='replace':
                summary['errors'].append({'asset':asset,'error':'unexpected_operation'})
                continue
            a,b=group
            key=(asset,a['path'],a['value'],b['value'])
            if a['path']!=b['path'] or key not in allowed:
                summary['errors'].append({'asset':asset,'error':'unapproved_translation_path'})
            if key in embedded:
                from embedded_json import parse_parameters
                nested_before=parse_parameters(a['value'])
                nested_after=parse_parameters(b['value'])
                approved={(r['path'],r['source'],r['target']) for r in embedded[key]['display_changes']}
                observed=set(diff(nested_before,nested_after))
                if observed!=approved:
                    summary['errors'].append({'asset':asset,'path':a['path'],'error':'non_display_embedded_change'})
                issues=[p for r in embedded[key]['display_changes'] for p in check_translation(r['source'],r['target'])]
            else:
                issues=check_translation(a['value'],b['value'])
            if issues:
                summary['errors'].append({'asset':asset,'path':a['path'],'error':issues})
            # Isolate semantic checks from schemas absent in this checkout.
            fixture={'text':a['value'],'sentinel':{'number':42,'id':'keep_gameplay_id'}}
            mini=[[{**a,'path':'/text'},{**b,'path':'/text'}]]
            replaced=apply_batches(fixture,mini)
            assert replaced=={'text':b['value'],'sentinel':fixture['sentinel']}
            incompatible={'text':'__version_mismatch__','sentinel':fixture['sentinel']}
            assert apply_batches(incompatible,mini)==incompatible
            assert apply_batches({'sentinel':fixture['sentinel']},mini)=={'sentinel':fixture['sentinel']}
            summary['guarded_groups_checked']+=1
        basepath=upstream_asset(project,upstream,asset)
        if not basepath.exists():
            summary['patch_only_assets_without_vanilla_or_other_mod_base']+=1
            continue
        before=read_asset(basepath)
        upstream_patch=upstream_asset(project,upstream,asset+'.patch')
        if upstream_patch.exists():
            try:
                before=apply_batches(before,read_asset(upstream_patch))
            except (TestFailed,jsonpatch.JsonPatchException,jsonpointer.JsonPointerException,KeyError,TypeError,IndexError) as e:
                summary['known_asset_source_patch_errors'].append({'asset':asset,'error':str(e)[:180]})
                continue
        sources_by_path=collections.defaultdict(set)
        for group in groups:
            if group_identity(asset,group) in approved_ui:
                continue
            if 'value' in group[0]:
                sources_by_path[group[0]['path']].add(group[0]['value'])
        for pointer, expected_sources in sources_by_path.items():
            try: actual=jsonpointer.resolve_pointer(before,pointer)
            except (jsonpointer.JsonPointerException,KeyError,IndexError,TypeError):actual=None
            # Multiple guarded upstream variants at one path are intentional.
            if not isinstance(actual,str) or actual not in expected_sources:
                summary['source_guard_mismatches_in_known_assets'].append({'asset':asset,'path':pointer})
        after=apply_batches(before,groups)
        # Independently undo only the UI presentation paths and then enforce
        # the ordinary display-string-only diff on the remaining document.
        string_only_after=copy.deepcopy(after)
        for ui_entry in reversed(ui_by_asset.get(asset,[])):
            for change in reversed(ui_entry['changes']):
                actual=jsonpointer.resolve_pointer(string_only_after,change['path'])
                if actual!=change['target']:
                    summary['errors'].append({'asset':asset,'path':change['path'],'error':'ui_presentation_target_mismatch'})
                undo={'op':'replace' if change['source_exists'] else 'remove','path':change['path']}
                if change['source_exists']:
                    undo['value']=change['source']
                string_only_after=jsonpatch.apply_patch(string_only_after,[undo])
        differences=diff(before,string_only_after)
        for path,a,b in differences:
            if (asset,path) in authored:
                entry=authored[(asset,path)]
                if b!=entry['translation'] or hashlib.sha256(a.encode()).hexdigest()!=entry['upstream_sha256']:
                    summary['errors'].append({'asset':asset,'path':path,'error':'unapproved_authored_dialogue_change'})
                continue
            if not isinstance(a,str) or not isinstance(b,str) or (asset,path,a,b) not in allowed:
                summary['errors'].append({'asset':asset,'path':path,'error':'non_display_or_gameplay_change'})
        summary['known_full_assets_verified']+=1
        summary['known_full_asset_strings_changed']+=len(differences)
    # A failing batch must leave the next independent batch runnable.
    assert apply_batches({'a':'changed','b':'en'},[
        [{'op':'test','path':'/a','value':'en'},{'op':'replace','path':'/a','value':'日本語'}],
        [{'op':'test','path':'/b','value':'en'},{'op':'replace','path':'/b','value':'日本語'}]
    ])=={'a':'changed','b':'日本語'}
    metadata=json.loads((mod/'_metadata').read_text())
    assert not metadata.get('requires',[]), 'A localization add-on must not introduce a missing-dependency startup error'
    assert metadata.get('includes')==['FrackinUniverse']
    assert metadata.get('priority')==1000
    summary['metadata_hard_dependencies']=metadata.get('requires',[])
    summary['metadata_optional_load_after']=metadata.get('includes',[])
    assert not list(mod.rglob('*.patch.patch'))
    assert not list(mod.rglob('*.exe'))
    compat=mod/'zb/zb_textTyper.lua'
    if compat.exists():
        assert compat.read_bytes()==(project/'compat/zb/zb_textTyper.lua').read_bytes()
    sbvn=mod/'interface/scripted/sbvn/pandorasboxsbvngui.lua'
    if sbvn.exists():
        assert sbvn.read_bytes()==(project/'compat/interface/scripted/sbvn/pandorasboxsbvngui.lua').read_bytes()
    statuses={r['source']:r['translation'] for r in append_rows if r['strategy']=='npc_status_lookup'}
    if statuses:
        from append_localization import NPC_SCRIPT, npc_override
        expected=npc_override((upstream/NPC_SCRIPT).read_text(encoding='utf-8'),statuses)
        assert (mod/NPC_SCRIPT).read_text(encoding='utf-8')==expected
    lua_report_file=project/'reports/lua_validation.json'
    if lua_report_file.exists():
        lua_report=json.loads(lua_report_file.read_text(encoding='utf-8'))
        assert not lua_report['syntax_errors'] and not lua_report['untranslated']
        for entry in lua_report['files']:
            assert hashlib.sha256((mod/entry['asset']).read_bytes()).hexdigest()==entry['localized_sha256'], entry['asset']
        for entry in lua_report['support_assets']:
            assert hashlib.sha256((mod/entry['asset']).read_bytes()).hexdigest()==entry['sha256'], entry['asset']
        summary['localized_lua_files_verified']=lua_report['file_count']
        summary['lua_display_literal_changes']=lua_report['translated_literals']
        expected_raw={'_metadata','ATTRIBUTION.txt','LICENSE-FU-CC-BY-4.0.txt',
                      'zb/zb_textTyper.lua','interface/scripted/sbvn/pandorasboxsbvngui.lua',NPC_SCRIPT}
        expected_raw.update(r['asset'] for r in lua_report['files'])
        expected_raw.update(r['asset'] for r in lua_report['support_assets'])
        actual_raw={name for name in manifest if not name.endswith('.patch')}
        assert actual_raw==expected_raw, {'unexpected':sorted(actual_raw-expected_raw),'missing':sorted(expected_raw-actual_raw)}
    summary['mod_version']=metadata['version']
    assert summary['ui_presentation_groups_checked']==len(ui_rows)
    summary['supplemental_append_fields']=len(append_rows)
    summary['embedded_json_display_fields']=sum(len(r['display_changes']) for r in embedded_rows)
    summary['passed']=not summary['errors']
    summary['scope']='JSON structure, guarded patch semantics, known FU source assets, display-only diffs; not a Starbound runtime test'
    dump(project/'reports/validation.json',summary)
    dump(project/'reports/mod_sha256.json',manifest)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    if not summary['passed']:raise SystemExit(1)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--project',required=True)
    p.add_argument('--upstream',required=True)
    p.add_argument('--mod',required=True)
    a=p.parse_args()
    validate(a.project,a.upstream,a.mod)
