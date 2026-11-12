"""Execute the limited repair's existing Lua suites on portable Lupa runtimes."""
from __future__ import annotations

import argparse
import importlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/compat'))
from release_evidence import filesystem_files, input_state_sha256, sha
from test_extra_display_fallback import build_suite
from test_lua_localization import lua_value


def run(output):
    output = Path(output)
    output.unlink(missing_ok=True)
    before = input_state_sha256(filesystem_files(ROOT))
    suite = unittest.TestSuite()
    for module in ('test_limited_repair_release', 'test_lua_localization_generation',
                   'test_limited_repository_evidence'):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromName(module))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful() or result.skipped or result.testsRun != 25:
        raise ValueError('All 25 limited packaging/generation/evidence tests must pass without skips')
    compat = ROOT / 'source/compat'
    mod = ROOT / 'mods/FU_Japanese'
    species = json.loads((mod / 'fujp/species_display.config').read_text(encoding='utf-8'))
    guides = json.loads((mod / 'fujp/guide_display.config').read_text(encoding='utf-8'))
    setup, extra_suite, names = build_suite(species, guides)
    runtimes = []
    for version in ('53', '54'):
        LuaRuntime = importlib.import_module('lupa.lua' + version).LuaRuntime
        extra = LuaRuntime()
        extra.execute(setup)
        for asset in ('species_display.lua', 'guide_display.lua'):
            extra.execute((mod / 'fujp' / asset).read_text(encoding='utf-8'))
        extra.execute(extra_suite)
        assert extra.globals().__caseCount == len(names) == 249
        assert extra.globals().__assertionCount == 639
        core = LuaRuntime()
        core.execute('localizedRoot=' + lua_value(mod.as_posix()) + '\n'
                     + 'upstreamRoot="";displayFallbackOnly=true;formatFixtures={};\n'
                     + 'displayDictionaries=' + lua_value(json.loads((mod / 'fujp/lua_display.config').read_text(encoding='utf-8'))))
        core.execute((compat / 'test_lua_localization.lua').read_text(encoding='utf-8'))
        data = json.loads(core.globals().luaLocalizationReport)
        assert data['runtime'] == 'Lua ' + version[0] + '.' + version[1]
        assert data['cases'] == 8 and data['assertions'] == 142 and data['status'] == 'passed'
        runtimes.append({'runtime':data['runtime'], 'core_cases':8, 'core_assertions':142,
                         'extra_cases':249, 'extra_assertions':639, 'passed':True})
    after = input_state_sha256(filesystem_files(ROOT))
    if before != after:
        raise ValueError('Source/MOD inputs changed while running limited repair tests')
    harnesses = ('source/compat/test_extra_display_fallback.py',
                 'source/compat/test_lua_localization.lua',
                 'source/tools/run_limited_helper_tests.py')
    report = {'schema':1, 'passed':True, 'failures':0, 'errors':0, 'skipped':0,
              'input_state_sha256':after, 'unit_tests':result.testsRun, 'runtimes':runtimes,
              'harness_sha256':{name:sha((ROOT / name).read_bytes()) for name in harnesses},
              'native_game_executed':False, 'whole_mod_runtime_tested':False}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report-output', type=Path, default=ROOT / 'source/reports/limited_helper_tests_024_public3.json')
    run(parser.parse_args().report_output)
