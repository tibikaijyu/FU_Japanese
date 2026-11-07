"""Execute the actual original/localized NPC status action in a Lua VM."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'tools'))
from append_localization import NPC_SCRIPT, lua_quote, npc_override
from lua_localization import load_lua, run_lua


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('upstream', type=Path)
    parser.add_argument('mod', type=Path)
    args = parser.parse_args()
    rows = [json.loads(line) for line in (HERE.parent/'source/append_translated_catalog.jsonl').read_text(encoding='utf-8').splitlines()]
    mapping = {r['source']:r['translation'] for r in rows if r['strategy']=='npc_status_lookup'}
    original_path = (args.upstream/NPC_SCRIPT).resolve()
    output_path = (args.mod/NPC_SCRIPT).resolve()
    original = original_path.read_text(encoding='utf-8')
    assert output_path.read_text(encoding='utf-8') == npc_override(original, mapping)
    cases = ''.join('{' + lua_quote(s) + ',' + lua_quote(t) + '},\n' for s,t in sorted(mapping.items()))
    program = '''
local assertions=0
local function check(condition,message)
  assert(condition,message)
  assertions=assertions+1
end
local function simulate(path,value,randomValue)
  local env=setmetatable({}, {__index=_G})
  local output,logs,nametags=nil,0,0
  env.require=function() end
  env.math={random=function() return randomValue end}
  env.storage={}
  env.personalityType=function() return "generic" end
  env.randomStatusText=function(personality)
    check(personality=="generic","Personality changed")
    return value
  end
  env.npc={
    setStatusText=function(text) output=text end,
    setDisplayNametag=function(enabled) check(enabled==true,"Nametag visibility changed"); nametags=nametags+1 end,
    npcType=function() return "fixture" end,
    species=function() return "human" end
  }
  env.sb={logError=function() logs=logs+1 end}
  assert(loadfile(path,"t",env))()
  check(env.randomizeStatusText({},{})==true,"Behavior return changed")
  check(output==env.storage.statusText,"Displayed and stored status differ")
  check(nametags==1,"Nametag call count changed")
  return output,logs
end
local original_path=ORIGINAL
local localized_path=LOCALIZED
local cases={CASES}
for _,case in ipairs(cases) do
  local old,oldLog=simulate(original_path,case[1],0.1)
  local new,newLog=simulate(localized_path,case[1],0.1)
  check(old==case[1] and new==case[2],"Exact source status did not localize")
  check(oldLog==newLog,"Logging behavior changed")
  local absent=simulate(localized_path,case[1],0.9)
  check(absent==nil,"Random status suppression changed")
end
for _,value in ipairs({"Unknown third-party line", "別のMODの表示", "", false, 42, {"invalid"}}) do
  local old,oldLog=simulate(original_path,value,0.1)
  local new,newLog=simulate(localized_path,value,0.1)
  check(old==new,"Unknown or invalid value behavior changed")
  check(oldLog==newLog,"Invalid input logging changed")
end
local empty=simulate(localized_path,nil,0.1)
check(empty==nil,"nil status changed")
npcStatusReport=string.format('{"status":"passed","translated_status_cases":%d,"assertions":%d,"runtime":"%s"}',#cases,assertions,_VERSION)
'''.replace('ORIGINAL',lua_quote(str(original_path))).replace('LOCALIZED',lua_quote(str(output_path))).replace('CASES',cases)
    report = json.loads(run_lua(load_lua(), program, '@npc_status_tests', execute=True, result_global='npcStatusReport'))
    report['upstream_sha256'] = hashlib.sha256(original_path.read_bytes()).hexdigest()
    report['localized_sha256'] = hashlib.sha256(output_path.read_bytes()).hexdigest()
    report['scope'] = 'Actual Lua NPC action with mocked game APIs; original random gate, invalid-value handling, return value and nametag behavior preserved.'
    (HERE/'npc_status_test_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
