#!/usr/bin/env python3
"""Build scoped guide display corrections from the prior release and fixed FU source."""
import argparse, collections, copy, hashlib, json, re, sys
from pathlib import Path

NAMES = ['ffguide','ffguide2','ffguide3','ffguide4','ffguide5','ffguide6','ffguidebattle','ffguidepower','networkguide','networkguide2']

def dump(p, value):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(s):return re.sub(r'[ \t\r\n\v\f]+',' ',s).strip(' ')
def resolve(value, pointer):
    for p in pointer.split('/')[1:]:value=value[int(p)] if isinstance(value,list) else value[p.replace('~1','/').replace('~0','~')]
    return value

def physical_json(text):
    # Preserve physical CR versus LF inside strings; keep escaped \\n as LF.
    import pyjson5
    out=[];quote=None;comment=None;escaped=False;i=0
    while i<len(text):
        c=text[i];nxt=text[i+1] if i+1<len(text) else ''
        if comment=='line':
            if c=='\n':comment=None;out.append(c)
            i+=1;continue
        if comment=='block':
            if c=='*' and nxt=='/':comment=None;out.append(' ');i+=2
            else:i+=1
            continue
        if quote:
            if escaped:out.append(c);escaped=False
            elif c=='\\':out.append(c);escaped=True
            elif c==quote:out.append(c);quote=None
            elif c=='\n':out.append('\\n')
            elif c=='\r':out.append('\\r')
            elif c=='\t':out.append('\\t')
            else:out.append(c)
        elif c in ('"',"'"):quote=c;out.append(c)
        elif c=='/' and nxt in ('/','*'):comment='line' if nxt=='/' else 'block';out.append(' ');i+=1
        else:out.append(c)
        i+=1
    return pyjson5.loads(''.join(out).lstrip('\ufeff'))

def build(root,baseline):
    root,baseline=map(Path,(root,baseline))
    sys.path.insert(0,str(baseline/'source/tools'))
    from common import read_asset
    from build import check_translation
    catalog=[json.loads(s) for s in (baseline/'source/source/translated_catalog.jsonl').read_text().splitlines()]
    rows=[r for r in catalog if r['asset'].startswith('codex/documents/') and Path(r['asset']).stem in NAMES]
    row_index={(r['asset'],r['path']):r for r in rows}
    originals={n:read_asset(root/'upstream/codex/documents'/f'{n}.codex') for n in NAMES}
    core=originals['ffguide']['longContentPages'][0]
    translations=json.loads((root/'core_line_translations.json').read_text())
    lines=core.split('\n')
    for key,translated in translations.items():
        idx=int(key);assert lines[idx],idx;lines[idx]=translated
    core_ja='\n'.join(lines)
    for i,line in enumerate(lines):
        # Nonblank body lines must be translated, except markup dividers and URL.
        if i not in {int(x) for x in translations}:
            assert not re.search(r'[A-Za-z]{3}',re.sub(r'\^[^;]+;','',line)),(i,line)
    problems=check_translation(core,core_ja);assert not problems,problems
    (root/'core_guide_ja.txt').write_text(core_ja,encoding='utf-8')
    overrides={('codex/documents/ffguide.codex','/longContentPages/0'):core_ja}
    title_terms={
        'FU Guide':'FUガイド','Core Guide':'基本ガイド','Biomes':'バイオーム','Stats':'能力値',
        'Medical Station Buffs':'医療ステーションの強化効果','Environments':'環境','Food and Armor':'食料と防具',
        'Battle':'戦闘','Generators and You':'発電機の使い方','Beginner ITN':'アイテムネットワーク入門','Item Network':'アイテムネットワーク'}
    short={
        'To read this codex, use your ^orange;Personal Tricorder^reset; and click the Book icon.':'このコーデックスを読むには、^orange;個人用トライコーダー^reset;を使って、本のアイコンをクリックしてください。',
        'Use the Enhanced Codex Viewer to read this. Access it in your Tricorder.':'この本は、トライコーダーから開ける拡張コーデックスで読めます。',
        "View in your Tricorder Codex tab in the 'FU' section.":'トライコーダーのコーデックスを開き、「FU」のカテゴリから読んでください。',
        'FU Stats':'FUの能力値',
        'A comprehensive list of medical station buffs.':'医療ステーションで受けられる強化効果の一覧。',
        'Effects and You':'環境と状態効果について',
        'Armor Up and Nom':'食事と防具で冒険に備えよう',
        'Changes to Weapons and Combat in FU.':'FUでの武器と戦闘の変更点。',
        'Power Your Lab':'研究施設に電力を供給しよう',
        "A Beginner's Guide to ITN":'アイテムネットワーク入門',
        'Tutorials for how to work Networks':'アイテムネットワークの使い方',
        'For a detailed guide on how to operate the ITD networks, from setup to execution, please refer to the following URL (located on the Steam page and CF Forums pages of FU as a link, as well): https://steamcommunity.com/sharedfiles/filedetails/?id=1618972523':'ITDネットワークの設置から運用まで、詳しい使い方は次のURLを参照してください。FUのSteamページやChucklefishフォーラムにもリンクがあります：https://steamcommunity.com/sharedfiles/filedetails/?id=1618972523',
        'Also, check out the official wiki page on ITDs here: https://frackinuniverse.miraheze.org/wiki/ITD':'ITDについては、公式Wikiのページも参照してください：https://frackinuniverse.miraheze.org/wiki/ITD',
        "Dos & Don'ts:\n\n  Do create branching ITD trees along a string of containers where you feel you need to.\n\n  Do Not create any sort of infinite back-and-forth loop that shifts the same items between the same containers unless you have a very good reason to do so. This can be a substantial source of lag.":'運用のコツと注意点：\n\n  必要に応じて、並べた収納容器に沿ってITDの経路を分岐させてください。\n\n  明確な理由がない限り、同じアイテムを同じ容器の間で延々と往復させる無限ループは作らないでください。大きな処理遅延の原因になります。',
        'Credits:\n\n  Kherae for making all this arcane schlock work.\n  HelloWorld123 for writing the original Network Guide.\n  TP for Steambound Reloaded.\n  Cratesmith for the Vesselbound Container Link Code.\n  Terminal for figuring out how to reverse entropy and for writing this guide.':'クレジット：\n\n  Kherae：この複雑な仕組みを動くものにしてくれたことに感謝します。\n  HelloWorld123：元のネットワークガイドの執筆。\n  TP：Steambound Reloadedの制作。\n  Cratesmith：Vesselboundのコンテナ接続コードの制作。\n  Terminal：エントロピーを逆転させる方法の解明と、このガイドの執筆。',
        'Item Types:\n  Hand Tools (Flashlight, rope, picks)\n  Instruments (Violin, xylaphone, assflute)\n  Thrown weapons (Throwing knives, bombs)\n  Augments\n  Collars\n  Dyes':'アイテムの種類：\n  道具（懐中電灯、ロープ、つるはし）\n  楽器（バイオリン、木琴、お尻フルート）\n  投てき武器（投げナイフ、爆弾）\n  拡張パーツ\n  首輪\n  染料'
    }
    for r in rows:
        key=(r['asset'],r['path'])
        if r['path']=='/title':
            t=r['source']
            for src,ja in title_terms.items():t=t.replace(src,ja)
            overrides[key]=t
        elif r['source'] in short:overrides[key]=short[r['source']]
    out=root/'out';out.mkdir(exist_ok=True)
    field_overrides=[];variants=[];config={};provenance=[]
    baseline_hashes={};outputs=[]
    for n in NAMES:
        asset='codex/documents/'+n+'.codex';rel=asset+'.patch'
        src=root/'upstream'/asset
        stable=root/'stable_658'/asset
        assert src.read_bytes()==stable.read_bytes(),asset
        raw=src.read_bytes().decode('utf-8-sig')
        lf_raw=raw.replace('\r\n','\n').replace('\r','\n')
        windows=physical_json(lf_raw.replace('\n','\r\n'))
        lf=physical_json(lf_raw);assert lf==originals[n]
        physical=physical_json(raw)
        assert physical in (lf,windows), 'Inspect mixed physical line-ending source: '+asset
        provenance.append({'asset':asset,'upstream_sha256':sha(src),'stable_658_sha256':sha(stable),'identical_between_tag_658_and_pinned_head':True,'physical_crlf_lines':raw.count('\r\n')})
        patch=json.loads((baseline/'mods/FU_Japanese'/rel).read_text())
        base_patches=copy.deepcopy(patch)
        baseline_hashes[rel]=sha(baseline/'mods/FU_Japanese'/rel)
        entries=[]
        for group in patch:
            a,b=group;assert a['op']=='test' and b['op']=='replace' and a['path']==b['path']
            path=a['path'];row=row_index[(asset,path)]
            assert resolve(lf,path)==a['value']==row['source']
            assert b['value']==row['translation']
            target=overrides.get((asset,path),row['translation'])
            issues=check_translation(row['source'],target);assert not issues,(asset,path,issues)
            if target!=row['translation']:
                field_overrides.append({**row,'translation':target,'previous_translation':row['translation'],'method':'manual_guide_022','reason':'Field-specific guide readability correction; core guide manually retranslated.'})
            b['value']=target
            parts=path.split('/')[1:]
            assert parts[0] in {'title','description','contentPages','longContentPages'}
            entry={'field':parts[0],'source':a['value'],'normalizedSource':norm(a['value']),'translation':target}
            if len(parts)>1:entry['index']=int(parts[1])+1
            entries.append(entry)
            crlf=resolve(windows,path)
            if crlf!=a['value']:
                variant=[{**a,'value':crlf},copy.deepcopy(b)]
                variants.append({'asset':asset,'path':path,'source':crlf,'translation':target,'base_id':row['id'],'variant':'Physical LF converted to CRLF in source bytes; escaped newline values remain LF.','group':variant})
        patch.extend(r['group'] for r in variants if r['asset']==asset)
        dump(out/rel,patch);outputs.append(rel)
        config[originals[n]['id']]=entries
    dump(out/'fujp/guide_display.config',{'version':1,'guides':config})
    outputs.append('fujp/guide_display.config');outputs.append('fujp/guide_display.lua')
    lua_asset='interface/scripted/xcustomcodex/xcodexui.lua'
    old=(baseline/'mods/FU_Japanese'/lua_asset).read_text(encoding='utf-8')
    before='rawCodexData = root.assetJson(codexInfo[2] .. codexInfo[1] .. ".codex")'
    after='rawCodexData = fuJapaneseGuide.localize(root.assetJson(codexInfo[2] .. codexInfo[1] .. ".codex"))'
    assert old.count(before)==2
    lua='require("/fujp/guide_display.lua")\nlocal fuJapaneseGuide = fuJapaneseGuideDisplay\n'+old.replace(before,after)
    p=out/lua_asset;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(lua,encoding='utf-8')
    baseline_hashes[lua_asset]=sha(baseline/'mods/FU_Japanese'/lua_asset);outputs.append(lua_asset)
    ui_asset='interface/scripted/xcustomcodex/xcodexui.config'
    ui_rel=ui_asset+'.patch'
    ui_rows=[r for r in catalog if r['asset']==ui_asset]
    ui=json.loads((baseline/'mods/FU_Japanese'/ui_rel).read_text())
    ui_corrections={'/gui/windowTitle/title':('High-Fidelity Codex','拡張コーデックス'),
                    '/gui/codexListRace/value':('No Selected Race','カテゴリ未選択')}
    for group in ui:
        a,b=group
        if a['path'] in ui_corrections:
            source,target=ui_corrections[a['path']]
            r=next(r for r in ui_rows if r['path']==a['path']);assert r['source']==source
            b['value']=target
            field_overrides.append({**r,'translation':b['value'],'previous_translation':r['translation'],'method':'manual_guide_022','reason':'Correct codex viewer title translation.'})
    dump(out/ui_rel,ui);baseline_hashes[ui_rel]=sha(baseline/'mods/FU_Japanese'/ui_rel);outputs.append(ui_rel)
    dump(root/'guide_022_field_overrides.json',field_overrides)
    dump(root/'guide_022_source_variants.json',variants)
    report={'guide_ids':list(config),'guide_count':len(config),'guide_display_fields':sum(map(len,config.values())),
        'core_guide_source_chars':len(core),'core_guide_translation_chars':len(core_ja),'core_guide_newline_count':core.count('\n'),
        'manual_field_overrides':len(field_overrides),'additional_crlf_guard_groups':len(variants),
        'assets':[{'asset':rel,'baseline_sha256':baseline_hashes.get(rel),'sha256':sha(out/rel)} for rel in outputs],
        'lua_display_hook_changes':[{'asset':lua_asset,'before':before,'after':after,'occurrences':2}],
        'lua_import_contract':'Starbound require returns nil. The helper exports global fuJapaneseGuideDisplay, which the viewer aliases after require.',
        'upstream_commit':'17868d86c9bb7bc00f92038fb78b48cebd1b41b8','stable_658_commit':'329e714b3fe87571055c8ad7aa38135d199d3317',
        'provenance':provenance,'runtime_tested':False,
        'cause_status':'Original guide translations and UI labels already existed; user PAK bytes are unavailable. Exact cause of the reported English display is not established. These changes cover formatting-only source differences at JSON and GUI display boundaries.',
        'scope':'Only known guide IDs and title/description/contentPages/longContentPages. Unknown text and Japanese already supplied by another patch are retained.'}
    dump(root/'guide_022_manifest.json',report)
    print(json.dumps({k:report[k] for k in ('guide_count','guide_display_fields','manual_field_overrides','additional_crlf_guard_groups','runtime_tested')},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--work',required=True);p.add_argument('--baseline',required=True);a=p.parse_args();build(a.work,a.baseline)
