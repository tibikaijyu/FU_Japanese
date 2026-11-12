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
    p=argparse.ArgumentParser();p.add_argument('--upstream',type=Path);p.add_argument('--mod',required=True,type=Path)
    p.add_argument('--lua-library',type=Path,help='explicit Lua 5.3/5.4 shared library path')
    p.add_argument('--report-output',type=Path,help='write the behavior report to this path')
    p.add_argument('--display-fallback-only',action='store_true',help='run only FU display-helper fallback cases (no upstream tree required)')
    args=p.parse_args()
    if not args.display_fallback_only and args.upstream is None:
        p.error('--upstream is required unless --display-fallback-only is set')
    translations=json.loads((PROJECT/'source/lua_translations.json').read_text(encoding='utf-8'))
    formats=[]
    for source,target in translations.items():
        specs=FORMAT.findall(source)
        if not specs: continue
        arguments=[]
        for spec in specs:
            if spec.endswith('%'): continue
            arguments.append('argument' if spec.endswith(('s','q')) else 42)
        formats.append({'source':source,'target':target,'args':arguments})
    dictionaries=json.loads((args.mod/'fujp/lua_display.config').read_text(encoding='utf-8'))
    source='\n'.join([
        'upstreamRoot='+quote_lua(str(args.upstream.resolve()) if args.upstream else ''),
        'localizedRoot='+quote_lua(str(args.mod.resolve())),
        'displayFallbackOnly='+str(args.display_fallback_only).lower(),
        'displayDictionaries='+lua_value(dictionaries),
        'formatFixtures='+lua_value(formats),
        (PROJECT/'compat/test_lua_localization.lua').read_text(encoding='utf-8'),
    ])
    report=json.loads(run_lua(load_lua(args.lua_library),source,'@test_lua_localization',execute=True,result_global='luaLocalizationReport'))
    report['scope']='FU display helper fallback fixtures; no upstream tree required' if args.display_fallback_only else 'Actual Lua functions with small Starbound API fixtures; game rendering not exercised'
    if args.lua_library:
        report['lua_library']=args.lua_library.name
        report['lua_library_sha256']=hashlib.sha256(args.lua_library.read_bytes()).hexdigest()
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
    if args.display_fallback_only:
        report['tests'] = report.pop('case_names', [])
    else:
        report['tests'] = report.get('case_names', report['tests'])
    report['tested_lua_sha256']={p.relative_to(args.mod).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(args.mod.rglob('*.lua'))}
    config_assets=('fujp/lua_display.config','fujp/species_display.config','fujp/guide_display.config')
    report['tested_display_config_sha256']={asset:hashlib.sha256((args.mod/asset).read_bytes()).hexdigest()
                                           for asset in config_assets if (args.mod/asset).is_file()}
    output=args.report_output or (PROJECT/'reports/lua_behavior_tests.json')
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='tested_lua_sha256'},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
