#!/usr/bin/env python3
"""Execute real localized Lua functions using the system Lua shared library."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(PROJECT/'tools'))
from lua_localization import FORMAT, load_lua, run_lua, quote_lua


def lua_value(value):
    if isinstance(value, str): return quote_lua(value)
    if value is True: return 'true'
    if value is False: return 'false'
    if value is None: return 'nil'
    if isinstance(value,(float,int)): return str(value)
    if isinstance(value,list): return '{'+','.join(lua_value(v) for v in value)+'}'
    return '{'+','.join('['+lua_value(k)+']='+lua_value(v) for k,v in value.items())+'}'


def main():
    p=argparse.ArgumentParser();p.add_argument('--upstream',required=True,type=Path);p.add_argument('--mod',required=True,type=Path)
    args=p.parse_args()
    translations=json.loads((PROJECT/'source/lua_translations.json').read_text())
    formats=[]
    for source,target in translations.items():
        specs=FORMAT.findall(source)
        if not specs: continue
        arguments=[]
        for spec in specs:
            if spec.endswith('%'): continue
            arguments.append('argument' if spec.endswith(('s','q')) else 42)
        formats.append({'source':source,'target':target,'args':arguments})
    dictionaries=json.loads((args.mod/'fujp/lua_display.config').read_text())
    source='\n'.join([
        'upstreamRoot='+quote_lua(str(args.upstream.resolve())),
        'localizedRoot='+quote_lua(str(args.mod.resolve())),
        'displayDictionaries='+lua_value(dictionaries),
        'formatFixtures='+lua_value(formats),
        (PROJECT/'compat/test_lua_localization.lua').read_text(),
    ])
    report=json.loads(run_lua(load_lua(),source,'@test_lua_localization',execute=True,result_global='luaLocalizationReport'))
    report['scope']='Actual Lua functions with small Starbound API fixtures; game rendering not exercised'
    report['tests']=[
        'Unknown values and types preserved', 'All bee subtype display aliases and case handling',
        'Species and pet asset metadata with fallback', 'Station command IDs and button states unchanged',
        'Fuel IDs and colors unchanged', 'Sapling tree IDs and icons unchanged',
        'Bee genomes and numerical stats unchanged for day/night/both/unidentified states',
        'Bee frame numerical effects preserved', 'Armor stats and class tags unchanged',
        'Weapon damage/asset/category IDs unchanged', 'Food aging and food value unchanged',
        'Well water output and storage unchanged', 'GPS time and calendar values unchanged',
        'Ship pet selection and portrait IDs unchanged', 'Condenser weight keys unchanged',
        'Quest bitmap title overlays retain quest IDs, completion state, and navigation',
        'Original format argument types and numbers preserved'
    ]
    report['tested_lua_sha256']={p.relative_to(args.mod).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(args.mod.rglob('*.lua'))}
    (PROJECT/'reports/lua_behavior_tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='tested_lua_sha256'},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
