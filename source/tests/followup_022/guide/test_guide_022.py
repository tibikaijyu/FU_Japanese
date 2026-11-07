#!/usr/bin/env python3
"""Validate guide source variants and execute actual display Lua with API stubs.

Does not launch Starbound. Fixtures are fixed official FU data, not saved player
files. Use --mod to verify an integrated release instead of this workdir's out.
"""
import argparse,copy,ctypes,ctypes.util,hashlib,json,re,sys
from pathlib import Path
from build_guide_022 import NAMES,physical_json,resolve,norm


def luaval(v):
    if v is None:return 'nil'
    if v is True:return 'true'
    if v is False:return 'false'
    if isinstance(v,str):return json.dumps(v,ensure_ascii=False).replace('\\/','/')
    if isinstance(v,(int,float)):return repr(v)
    if isinstance(v,list):return '{'+','.join(luaval(x) for x in v)+'}'
    if isinstance(v,dict):return '{'+','.join('['+luaval(k)+']='+luaval(x) for k,x in v.items())+'}'
    raise TypeError(type(v))

class Lua:
    def __init__(self):
        self.lib=ctypes.CDLL(ctypes.util.find_library('lua5.4') or ctypes.util.find_library('lua5.3'))
        self.lib.luaL_newstate.restype=ctypes.c_void_p
        self.lib.luaL_openlibs.argtypes=[ctypes.c_void_p]
        self.lib.luaL_loadbufferx.argtypes=[ctypes.c_void_p,ctypes.c_char_p,ctypes.c_size_t,ctypes.c_char_p,ctypes.c_char_p]
        self.lib.luaL_loadbufferx.restype=ctypes.c_int
        self.lib.lua_pcallk.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_int,ctypes.c_int,ctypes.c_longlong,ctypes.c_void_p]
        self.lib.lua_pcallk.restype=ctypes.c_int
        self.lib.lua_tolstring.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.POINTER(ctypes.c_size_t)]
        self.lib.lua_tolstring.restype=ctypes.c_char_p
        self.lib.lua_getglobal.argtypes=[ctypes.c_void_p,ctypes.c_char_p];self.lib.lua_getglobal.restype=ctypes.c_int
        self.lib.lua_tointegerx.argtypes=[ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p];self.lib.lua_tointegerx.restype=ctypes.c_longlong
        self.lib.lua_close.argtypes=[ctypes.c_void_p]
        self.state=self.lib.luaL_newstate();self.lib.luaL_openlibs(self.state)
    def run(self,source):
        b=source.encode('utf-8')
        status=self.lib.luaL_loadbufferx(self.state,b,len(b),b'@guide_022_tests.lua',None)
        if not status:status=self.lib.lua_pcallk(self.state,0,0,0,0,None)
        if status:raise AssertionError((self.lib.lua_tolstring(self.state,-1,None) or b'unknown Lua error').decode(errors='replace'))
    def number(self,key):
        self.lib.lua_getglobal(self.state,key.encode());return self.lib.lua_tointegerx(self.state,-1,None)
    def close(self):self.lib.lua_close(self.state)

COMMON=r'''
assertions = 0
local builtinAssert = assert
function check(condition, message)
  assertions = assertions + 1
  builtinAssert(condition, message)
end
function clone(x)
  if type(x) ~= "table" then return x end
  local r = {}
  for k,v in pairs(x) do r[k] = clone(v) end
  return r
end
function equal(a,b)
  if type(a) ~= type(b) then return false end
  if type(a) ~= "table" then return a == b end
  for k,v in pairs(a) do if not equal(v,b[k]) then return false end end
  for k,_ in pairs(b) do if a[k] == nil then return false end end
  return true
end
function field(doc,e)
  if e.index then return doc[e.field] and doc[e.field][e.index] end
  return doc[e.field]
end
function setfield(doc,e,value)
  if e.index then doc[e.field][e.index] = value else doc[e.field] = value end
end
local logs = {}
sb = {logInfo = function(message) table.insert(logs,message) end}
local readCount = 0
root = {assetJson = function(path)
  check(path == "/fujp/guide_display.config", "Only dedicated guide dictionary may be loaded")
  readCount = readCount + 1
  return CONFIG
end}
local loadedScripts = {}
require = function(path)
  check(path == "/fujp/guide_display.lua", "Only declared helper may be imported")
  if not loadedScripts[path] then
    loadedScripts[path] = true
    dofile(HELPER_PATH)
  end
  return nil -- Vanilla Starbound does not expose a module return value.
end
check(require("/fujp/guide_display.lua") == nil, "Starbound-style require returns nil")
local helper = fuJapaneseGuideDisplay
check(type(helper) == "table" and type(helper.localize) == "function", "Helper is exposed through its named global")
check(require("/fujp/guide_display.lua") == nil, "Cached require still returns nil")
check(#logs == 1 and logs[1] == "[FU Japanese 0.2.2] Guide display helper active", "one activation message")
'''


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work',required=True);ap.add_argument('--baseline',required=True);ap.add_argument('--mod');args=ap.parse_args()
    work=Path(args.work);baseline=Path(args.baseline);mod=Path(args.mod) if args.mod else work/'out'
    sys.path.insert(0,str(baseline/'source/tools'))
    from common import read_asset
    from validate import apply_batches,diff
    from build import check_translation
    report={'passed':False,'runtime_tested':False,'scope':'Actual Lua display helper and codex UI callback execution with stubbed Starbound APIs; exact FU LF/CRLF/mixed-source patch application. Not a game launch.','test_cases':[],'assertions':0}
    config=json.loads((mod/'fujp/guide_display.config').read_text())
    manifests=json.loads((work/'guide_022_manifest.json').read_text())
    overrides=json.loads((work/'guide_022_field_overrides.json').read_text())
    variants=json.loads((work/'guide_022_source_variants.json').read_text())
    originals={};windows={}
    for n in NAMES:
        asset='codex/documents/'+n+'.codex';p=work/'upstream'/asset
        raw=p.read_bytes().decode('utf-8-sig');lf_raw=raw.replace('\r\n','\n').replace('\r','\n')
        normal=read_asset(p);originals[normal['id']]=normal
        win=physical_json(lf_raw.replace('\n','\r\n'));windows[normal['id']]=win
        groups=json.loads((mod/(asset+'.patch')).read_text())
        entries=config['guides'][normal['id']]
        expected={('/'+e['field']+('/'+str(e['index']-1) if 'index' in e else '')):e['translation'] for e in entries}
        for source in [normal,win,physical_json(raw)]:
            after=apply_batches(source,groups)
            assert set(p for p,_,_ in diff(source,after))==set(expected),asset
            for path,target in expected.items():assert resolve(after,path)==target,(asset,path)
        # Every physical CRLF source corresponds to the LF original after normalization.
        for e in entries:
            path='/'+e['field']+('/'+str(e['index']-1) if 'index' in e else '')
            assert norm(resolve(win,path))==norm(e['source'])==e['normalizedSource']
        report['assertions']+=len(expected)*4+3
    report['test_cases'].append('All 10 guide assets: original LF, original physical line endings, Windows physical CRLF and escaped LF all translate only approved display fields')
    assert any('\r\n' in r['source'] and re.search(r'(?<!\r)\n',r['source']) for r in variants),'Need real mixed CRLF/escaped-LF fixture'
    report['test_cases'].append('Mixed physical CRLF and escaped LF is represented accurately rather than replacing every newline blindly')
    for row in overrides:assert not check_translation(row['source'],row['translation']),(row['asset'],row['path'])
    report['assertions']+=len(overrides)+1
    report['test_cases'].append('All contextual corrections preserve control tags, numeric values, placeholders, and newline counts')
    core_target=config['guides']['ffguide'][next(i for i,r in enumerate(config['guides']['ffguide']) if r['field']=='longContentPages')]['translation']
    assert 'mod.js' not in core_target
    assert 'https://steamcommunity.com/sharedfiles/filedetails/?id=1618972523' in next(r['translation'] for r in overrides if r['asset']=='codex/documents/networkguide2.codex' and r['path']=='/contentPages/0')
    report['assertions']+=2
    report['test_cases'].append('Core Guide no longer contains invented mod.js wording; external guide URL is preserved exactly')
    ui_asset='interface/scripted/xcustomcodex/xcodexui.config'
    ui_original=read_asset(work/'upstream'/ui_asset)
    ui_updated=apply_batches(ui_original,json.loads((mod/(ui_asset+'.patch')).read_text()))
    assert ui_updated['gui']['windowTitle']['title']=='拡張コーデックス'
    ui_previous=apply_batches(ui_original,json.loads((baseline/'mods/FU_Japanese'/(ui_asset+'.patch')).read_text()))
    assert set(p for p,_,_ in diff(ui_previous,ui_updated))=={'/gui/windowTitle/title','/gui/codexListRace/value'}
    report['assertions']+=2;report['test_cases'].append('Codex window title corrected with no UI layout/callback changes')
    original_lua=(baseline/'mods/FU_Japanese/interface/scripted/xcustomcodex/xcodexui.lua').read_text()
    new_lua=(mod/'interface/scripted/xcustomcodex/xcodexui.lua').read_text()
    before='rawCodexData = root.assetJson(codexInfo[2] .. codexInfo[1] .. ".codex")'
    after='rawCodexData = fuJapaneseGuide.localize(root.assetJson(codexInfo[2] .. codexInfo[1] .. ".codex"))'
    assert new_lua=='require("/fujp/guide_display.lua")\nlocal fuJapaneseGuide = fuJapaneseGuideDisplay\n'+original_lua.replace(before,after)
    report['assertions']+=1;report['test_cases'].append('Existing localized codex UI changed only by helper require and two asset-read display hooks')
    prefix='CONFIG = '+luaval(config)+'\nORIGINALS = '+luaval(originals)+'\nWINDOWS = '+luaval(windows)+'\nHELPER_PATH = '+luaval(str(mod/'fujp/guide_display.lua'))+'\n'
    code=prefix+COMMON+r'''
-- Exact known English, windows CRLF+LF, and other formatting-only variants.
for id, original in pairs(ORIGINALS) do
  local before = clone(original)
  for case = 1,3 do
    local input = clone(case == 2 and WINDOWS[id] or original)
    if case == 3 then
      for _,e in ipairs(CONFIG.guides[id]) do
        setfield(input,e," \t" .. field(input,e):gsub("[ \t\r\n]+"," \r\n\t ") .. "\r\n ")
      end
    end
    local untouched = clone(input)
    local result = helper.localize(input)
    check(equal(input,untouched), "helper must not mutate caller-owned asset tables")
    for _,e in ipairs(CONFIG.guides[id]) do check(field(result,e) == e.translation, id .. " known field") end
    for k,v in pairs(input) do
      if k ~= "title" and k ~= "description" and k ~= "contentPages" and k ~= "longContentPages" then
        check(equal(v,result[k]), "Non-display field unchanged: " .. k)
      end
    end
  end
  local translated = clone(original)
  for _,e in ipairs(CONFIG.guides[id]) do setfield(translated,e,e.translation) end
  check(helper.localize(translated) == translated,"Already translated asset retained by identity")
  check(equal(original,before),"Original fixture unchanged")
end
check(readCount == 1, "dictionary loaded once per Lua context")
-- Arbitrary Japanese and changed English are not overwritten, even in known guides.
for _, text in ipairs({"別の日本語訳を残す", "A new paragraph from a future FU version.", "1000 changed numeric value"}) do
  local input = clone(ORIGINALS.ffguide)
  input.longContentPages[1] = text
  local result = helper.localize(input)
  check(result.longContentPages[1] == text,"Unknown or already Japanese passage retained")
end
local unknown = clone(ORIGINALS.ffguide)
unknown.id = "third_party_guide"
check(helper.localize(unknown) == unknown,"Unknown codex ID stays unchanged")
check(helper.localize(nil) == nil,"nil safe")
check(helper.localize(false) == false,"boolean safe")
check(helper.localize(42) == 42,"number safe")
check(helper.localize("text") == "text","non-table safe")
local missing = {id="ffguide",title=false,contentPages=42,longContentPages={false}}
local result = helper.localize(missing)
check(equal(result,missing),"Missing or nonstring fields stay unchanged")
-- A forged dictionary entry cannot modify IDs, numbers or control subtrees.
table.insert(CONFIG.guides.ffguide, {field="id",source="ffguide",normalizedSource="ffguide",translation="BROKEN_ID"})
table.insert(CONFIG.guides.ffguide, {field="species",source="fu",normalizedSource="fu",translation="BROKEN_SPECIES"})
table.insert(CONFIG.guides.ffguide, {field="title",source=ORIGINALS.ffguide.title,normalizedSource=ORIGINALS.ffguide.title,translation=100})
table.insert(CONFIG.guides.ffguide, {field="longContentPages",index=0,source="Control",normalizedSource="Control",translation="BROKEN"})
local protected = helper.localize(clone(ORIGINALS.ffguide))
check(protected.id == "ffguide" and protected.species == "fu","Dictionary cannot write control fields")
check(#logs == 1,"No per-page or per-frame log spam")
'''
    lua=Lua();lua.run(code);report['assertions']+=lua.number('assertions');lua.close()
    report['test_cases'].extend([
        'Lua: all 62 known fields translate for exact, CRLF and formatting-only English inputs',
        'Lua: copy-on-write preserves original tables and all IDs, arrays, numbers and control values',
        'Lua: already Japanese/unknown/changed English and unknown codex IDs are retained',
        'Lua: malformed/missing fields are tolerated; dictionary entries cannot write controls',
        'Lua: dictionary cached once and activation log emitted once without page-level spam',
        'Lua: Starbound-style require executes once, returns nil both times, and exposes only the named global helper API'
    ])
    missing_config=prefix+COMMON.replace('return CONFIG','error("missing dictionary")')+r'''
local input = clone(ORIGINALS.ffguide)
check(helper.localize(input) == input,"Unavailable dictionary preserves original")
check(helper.localize(input) == input,"Unavailable dictionary remains safe")
check(readCount == 1,"Failed load not spammed")
'''
    lua=Lua();lua.run(missing_config);report['assertions']+=lua.number('assertions');lua.close()
    report['test_cases'].append('Lua: unavailable optional dictionary falls back to the original guide without throwing')
    # Exercise the real viewer callbacks through the FU category and page buttons.
    ui_code=prefix+'GUI_PATH = '+luaval(str(mod/'interface/scripted/xcustomcodex/xcodexui.lua'))+'\n'+COMMON+r'''
local datastore = { ["/codex/documents/ffguidepower.codex"] = clone(WINDOWS.ffguidepower) }
local originalData = clone(datastore)
root.assetJson = function(path)
  if path == "/fujp/guide_display.config" then return CONFIG end
  check(datastore[path] ~= nil,"Unexpected guide lookup: " .. path)
  return clone(datastore[path])
end
local savedProperties = { {"ffguidepower","/codex/documents/"} }
player = { getProperty = function(key)
  check(key == "xcodex.knownCodexEntries","Known codex IDs are only read")
  return clone(savedProperties)
end }
local widgetText, widgetData, counters = {}, {}, {}
widget = {
  setText = function(path,value) widgetText[path] = value end,
  setData = function(path,value) widgetData[path] = value end,
  getData = function(path) return widgetData[path] end,
  getListSelected = function(path) return "1" end,
  addListItem = function(path) counters[path]=(counters[path] or 0)+1; return tostring(counters[path]) end,
  clearListItems = function(path) counters[path]=0 end,
  setButtonEnabled=function()end, setFontColor=function()end, setImage=function()end,
  setButtonImage=function()end, addChild=function()end
}
local baseTostring, baseAssert = tostring,assert
function CreateLoggingOverride() return function()end,function()end,error,function()end,baseAssert,baseTostring end
local importHelper = require
require = function(path)
  if path == "/fujp/guide_display.lua" then return importHelper(path) end
  check(path == "/scripts/xcore_customcodex/LoggingOverride.lua" or path == "/scripts/xcore_customcodex/InitializationUtility.lua","Unexpected UI dependency")
  return nil
end
dofile(GUI_PATH)
postinit()
RaceButtonClicked()
check(widgetText.codexListRace == "選択中のカテゴリ：ガイド","Japanese category header")
ListButtonClicked()
local expected = {}
local title
for _,e in ipairs(CONFIG.guides.ffguidepower) do
  if e.field == "longContentPages" then expected[e.index] = e.translation end
  if e.field == "title" then title = e.translation end
end
check(widgetText.codexTitle == title,"Translated codex title actually reaches widget")
check(widgetText["codexText.textElement"] == expected[1],"Translated first long page actually reaches widget")
check(widgetText.currentPageLabel == "ページ 1 / " .. #expected,"Japanese page counter")
for i=2,#expected do NextButtonClicked(); check(widgetText["codexText.textElement"]==expected[i],"Next page translation") end
NextButtonClicked();check(widgetText["codexText.textElement"]==expected[#expected],"Cannot pass last page")
for i=#expected-1,1,-1 do PreviousButtonClicked();check(widgetText["codexText.textElement"]==expected[i],"Previous page translation") end
PreviousButtonClicked();check(widgetText["codexText.textElement"]==expected[1],"Cannot precede first page")
check(equal(datastore,originalData),"UI display path does not write game assets")
check(savedProperties[1][1]=="ffguidepower" and savedProperties[1][2]=="/codex/documents/","Saved codex IDs and paths unchanged")
check(#logs==1,"Single activation diagnostic through UI")
'''
    lua=Lua();lua.run(ui_code);report['assertions']+=lua.number('assertions');lua.close()
    report['test_cases'].append('Actual codex UI: postinit/category/list/next/previous callbacks deliver Japanese title and all power-guide pages while preserving IDs and page limits')
    report.update({'passed':True,'tests_run':len(report['test_cases']),'guide_ids':list(config['guides']),'guide_display_fields':sum(map(len,config['guides'].values())),'manual_field_overrides':len(overrides),'additional_crlf_guard_groups':len(variants),'mod_hashes':{a['asset']:hashlib.sha256((mod/a['asset']).read_bytes()).hexdigest() for a in manifests['assets']}})
    (work/'guide_022_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('passed','tests_run','assertions','guide_display_fields','additional_crlf_guard_groups','runtime_tested')},ensure_ascii=False))

if __name__=='__main__':main()
