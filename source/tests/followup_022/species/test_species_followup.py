#!/usr/bin/env python3
"""Exercise the actual display helper and stat-window boundary with Lua 5.4.

This uses fixed FU data and widget/root stubs. It does not run Starbound, test
font layout, or establish which raw string the user's installed PAK contains.
"""
import argparse
import collections
import copy
import ctypes
import ctypes.util
import hashlib
import json
from pathlib import Path
import re
import sys

from build_species_followup import parse_preserving_newlines, normalize, source_fields


def lua_literal(value):
    if value is None: return 'nil'
    if value is True: return 'true'
    if value is False: return 'false'
    if isinstance(value, str): return json.dumps(value, ensure_ascii=False)
    if isinstance(value, (int, float)): return str(value)
    if isinstance(value, list): return '{'+','.join(lua_literal(v) for v in value)+'}'
    if isinstance(value, dict): return '{'+','.join('['+lua_literal(k)+']='+lua_literal(v) for k,v in value.items())+'}'
    raise TypeError(type(value))


def run_lua(script):
    path = ctypes.util.find_library('lua5.4')
    if not path: raise RuntimeError('Lua 5.4 shared library is required for this test')
    lib = ctypes.CDLL(path)
    lib.luaL_newstate.restype = ctypes.c_void_p
    lib.luaL_openlibs.argtypes = [ctypes.c_void_p]
    lib.luaL_loadbufferx.argtypes = [ctypes.c_void_p,ctypes.c_char_p,ctypes.c_size_t,ctypes.c_char_p,ctypes.c_char_p]
    lib.luaL_loadbufferx.restype = ctypes.c_int
    lib.lua_pcallk.argtypes = [ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_ssize_t,ctypes.c_void_p]
    lib.lua_pcallk.restype = ctypes.c_int
    lib.lua_tolstring.argtypes = [ctypes.c_void_p,ctypes.c_int,ctypes.POINTER(ctypes.c_size_t)]
    lib.lua_tolstring.restype = ctypes.c_void_p
    lib.lua_tointegerx.argtypes = [ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p]
    lib.lua_tointegerx.restype = ctypes.c_longlong
    lib.lua_close.argtypes = [ctypes.c_void_p]
    state = lib.luaL_newstate()
    try:
        lib.luaL_openlibs(state)
        raw = script.encode('utf-8')
        error = lib.luaL_loadbufferx(state, raw, len(raw), b'species_regression', b't')
        if not error: error = lib.lua_pcallk(state, 0, 1, 0, 0, None)
        if error:
            size = ctypes.c_size_t()
            pointer = lib.lua_tolstring(state, -1, ctypes.byref(size))
            raise AssertionError(ctypes.string_at(pointer, size.value).decode('utf-8', errors='replace'))
        return lib.lua_tointegerx(state, -1, None)
    finally:
        lib.lua_close(state)


def test(baseline, upstream, result):
    baseline, upstream, result = map(Path, (baseline, upstream, result))
    sys.path.insert(0, str(baseline/'source/tools'))
    from common import read_asset
    from validate import apply_batches, diff
    from build import check_translation
    out = result/'out'
    config = json.loads((out/'fujp/species_display.config').read_text())
    fields = json.loads((result/'all_species_display_fields.json').read_text())
    overrides = json.loads((result/'field_overrides.json').read_text())
    variants = json.loads((result/'normalized_source_variants.json').read_text())
    manifest = json.loads((result/'manifest.json').read_text())
    assertions = 0
    def check(value, context):
        nonlocal assertions
        assertions += 1
        if not value: raise AssertionError(context)

    # Verify physical and escaped newlines independently of production parsing.
    raw = '{"value":"First\\nSecond\nThird"}'
    check(parse_preserving_newlines(raw)['value'] == 'First\nSecond\nThird', 'LF parsing')
    check(parse_preserving_newlines(raw.replace('\n','\r\n'))['value'] == 'First\nSecond\r\nThird', 'mixed CRLF parsing')
    for row in overrides:
        check(not check_translation(row['source'], row['translation']), (row['asset'], row['path'], 'text structure'))
    for row in manifest:
        path = out/row['asset']
        check(hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'], ('output hash', row['asset']))
        old = baseline/'mods/FU_Japanese'/row['asset']
        check((hashlib.sha256(old.read_bytes()).hexdigest() if old.exists() else None) == row['baseline_sha256'], ('baseline hash', row['asset']))
    by_field = {r['id']: r for r in fields}
    for row in variants:
        original = by_field[row['field_id']]
        check(normalize(row['source']) == normalize(original['source']), ('variant content',row['asset']))
        fixture = {'text':row['source'],'kind':'keep_id','numbers':[1.05,42]}
        group = copy.deepcopy(row['group'])
        for op in group:op['path']='/text'
        replaced = apply_batches(fixture,[group])
        check(replaced == {**fixture,'text':row['translation']}, ('variant apply',row['asset']))
        changed = {**fixture,'text':row['source']+' NEW BALANCE'}
        check(apply_batches(changed,[group]) == changed, ('unknown source preserved',row['asset']))
        check(apply_batches({'kind':'keep_id'},[group]) == {'kind':'keep_id'}, 'missing field guard')

    # Full .species assets are available for FU-owned races. Apply their source
    # patches and localization under both repository and physical-CRLF input.
    allowed = {(r['asset'],r['path'],r['translation']) for r in fields}
    complete_cases = 0
    for source_file in sorted((upstream/'species').glob('*.species')):
        asset = source_file.relative_to(upstream).as_posix()
        localized = out/(asset+'.patch')
        if not localized.exists():localized=baseline/'mods/FU_Japanese'/(asset+'.patch')
        if not localized.exists():continue
        for mode in ('lf','physical_crlf'):
            raw = source_file.read_bytes().decode('utf-8-sig').replace('\r\n','\n')
            if mode == 'physical_crlf':raw=raw.replace('\n','\r\n')
            before = parse_preserving_newlines(raw)
            companion = upstream/(asset+'.patch')
            if companion.exists():
                raw = companion.read_bytes().decode('utf-8-sig').replace('\r\n','\n')
                if mode == 'physical_crlf':raw=raw.replace('\n','\r\n')
                before = apply_batches(before,parse_preserving_newlines(raw))
            after = apply_batches(before,json.loads(localized.read_text()))
            for path, old, new in diff(before,after):
                check((asset,path,new) in allowed, ('unexpected full asset change',asset,path))
                check(isinstance(old,str) and isinstance(new,str), ('non-string change',asset,path))
            for key in ('kind','nameGen','genders','statusEffects','defaultBlueprints'):
                # Gender visual labels are not inside genders; these are controls.
                check(before.get(key)==after.get(key), ('control changed',asset,key))
            description = after.get('charCreationTooltip',{}).get('description','')
            check(bool(re.search(r'[\u3040-\u30ff\u3400-\u9fff]',description)), ('description not Japanese',asset,mode))
            complete_cases += 1

    cfg_literal = lua_literal(config)
    helper_path = 'modRoot.."/fujp/species_display.lua"'
    stat_path = 'modRoot.."/interface/scripted/statWindow/statWindow.lua"'
    script = '''
local modRoot = ... or os.getenv("FUJP_TEST_MOD") or "mods/FU_Japanese"
local checks=0
local function check(condition, context)
  checks=checks+1
  assert(condition, context)
end
local fixtureData=CONFIG
local logCount=0
local configReads=0
local currentSpecies
sb={logInfo=function(message)
  check(message=="[FU Japanese 0.2.2] Species display helper active", "diagnostic contains only the version marker")
  logCount=logCount+1
end}
root={assetJson=function(path)
  if path=="/fujp/species_display.config" then configReads=configReads+1; return fixtureData end
  check(path=="/species/"..currentSpecies.kind..".species", "correct species lookup ID")
  return currentSpecies
end}
local loadedModules={}
require=function(path)
  if path=="/scripts/util.lua" then return nil end
  check(path=="/fujp/species_display.lua", "only the intended module is required")
  if not loadedModules[path] then
    assert(loadfile(HELPER))()
    loadedModules[path]=true
  end
  -- Starbound require discards Lua chunk return values.
  return nil
end
local labels={}
widget={clearListItems=function(path) check(path=="racialDesc.textList", "clear the existing list") end,
        setText=function(path,value) labels[path]=value end}
assert(loadfile(STAT))()
local helper=fuJapaneseSpeciesDisplay
check(type(helper)=="table" and type(helper.description)=="function", "global module namespace is exported")
check(require("/fujp/species_display.lua")==nil,"Starbound-style require returns nil")
local function rendered(s)
  return (s:gsub("\\n      ","\\n^gray;>>>^reset;"):gsub("\\n    ","\\n^gray;>>^reset;"):gsub("\\n  ","\\n^gray;>^reset;"))
end
for race,record in pairs(fixtureData.species) do
  for _,candidate in ipairs(record.descriptions) do
    check(helper.description(race,candidate.source)==candidate.translation,"exact source "..race)
    local whitespace=" \\t"..candidate.source:gsub("[ \\t\\r\\n\\f\\v]+", "\\r\\n\\t ").." \\n"
    local converted=helper.description(race,whitespace)
    -- Duplicate source variants may differ only in Japanese line wrapping.
    check(converted:gsub("[ \\t\\r\\n\\f\\v]+", "")==candidate.translation:gsub("[ \\t\\r\\n\\f\\v]+", ""),"whitespace source "..race)
    check(helper.description(race,candidate.translation)==candidate.translation,"existing Japanese "..race)
    local unknown=candidate.source.." NEW EFFECT 987"
    check(helper.description(race,unknown)==unknown,"unknown update "..race)
    check(helper.description("unknown_race",candidate.source)==candidate.source,"unknown race")
    currentSpecies={kind=race,charCreationTooltip={title="Unknown Display Name",description=whitespace},
                    nameGen={"keep_namegen_id"},numeric={1.05,42}}
    populateRacialDescription(race,false)
    check(labels['racialDesc.textElement']==rendered(converted),'actual stat-window output '..race)
    check(labels['racialLabel']=="種族特性 ― Unknown Display Name",'unknown title preserved '..race)
    check(currentSpecies.kind==race and currentSpecies.nameGen[1]=="keep_namegen_id" and currentSpecies.numeric[2]==42,"input control data unchanged")
  end
  for _,candidate in ipairs(record.names) do
    check(helper.name(race,candidate.source)==candidate.translation,"friendly name "..race)
    check(helper.name(race,candidate.translation)==candidate.translation,"existing Japanese name "..race)
    check(helper.name(race,candidate.source.." Renamed")==candidate.source.." Renamed","unknown name preserved")
  end
end
check(helper.description("human",nil)==nil,"nil input")
check(helper.description("human",false)==false,"boolean input")
check(helper.description("human",42)==42,"number input")
check(helper.description(nil,"Original")=="Original","nil race")
check(helper.description({},"Original")=="Original","table race")
check(configReads==1,"one cached config read")
check(logCount==1,"no repeated diagnostic messages during display calls")
-- A missing optional lookup config must preserve the existing English.
root.assetJson=function() error('config unavailable') end
assert(loadfile(HELPER))()
local withoutConfig=fuJapaneseSpeciesDisplay
check(withoutConfig.description("human","Original text")=="Original text","asset failure fallback")
return checks
'''.replace('CONFIG',cfg_literal).replace('HELPER',helper_path).replace('STAT',stat_path)
    (result/'species_runtime_test.lua').write_text(script,encoding='utf-8')
    lua_checks=run_lua('return assert(load(' + lua_literal(script) +
                       ', "@species_runtime_test"))(' + lua_literal(out.resolve().as_posix()) + ')')
    report={'passed':True,'version':'0.2.2','python_assertions':assertions,'lua_assertions':lua_checks,
            'complete_species_cases_lf_and_crlf':complete_cases,
            'line_ending_variant_groups_tested':len(variants),'description_variants_tested':sum(len(v['descriptions']) for v in config['species'].values()),
            'field_overrides_checked':len(overrides),'runtime_tested':False,
            'scope':'Actual Lua helper and stat-window display function with fixed FU data and mocked root/widget APIs; Starbound-style require executes the helper and returns nil; full known FU species assets with LF and physical CRLF; all field override tags/numbers/newlines; exact source guards and unknown-source preservation.',
            'limits':'Does not run Starbound or determine the exact untranslated text in the user PAK. Native window rendering and layout require game-side confirmation.'}
    (result/'test_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--baseline',required=True)
    p.add_argument('--upstream',required=True)
    p.add_argument('--result',required=True)
    a=p.parse_args()
    test(a.baseline,a.upstream,a.result)
