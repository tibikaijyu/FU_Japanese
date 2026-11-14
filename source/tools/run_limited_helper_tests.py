"""Execute the limited repair's existing Lua suites on portable Lupa runtimes."""
from __future__ import annotations

import argparse
import gc
import importlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'source/compat'))
from release_evidence import filesystem_files, input_state_sha256, sha
from test_extra_display_fallback import DLLS, Lua, build_suite
from test_lua_localization import lua_value


class RuntimeAdapter:
    def __init__(self, version, backend, runtime, binary):
        self.version = version
        self.backend = backend
        self.runtime = runtime
        self.binary = Path(binary).resolve()

    def execute(self, source, label):
        raise NotImplementedError

    def integer_global(self, name):
        raise NotImplementedError

    def string_global(self, name):
        raise NotImplementedError

    def close(self):
        raise NotImplementedError

    def artifact(self):
        return {'backend':self.backend, 'binary':str(self.binary),
                'binary_sha256':sha(self.binary.read_bytes())}


class LupaAdapter(RuntimeAdapter):
    def execute(self, source, label):
        return self.runtime.execute(source)

    def integer_global(self, name):
        return int(self.runtime.globals()[name])

    def string_global(self, name):
        value = self.runtime.globals()[name]
        if not isinstance(value, str):
            raise RuntimeError(f'Lua {self.version}: global {name} is not a string')
        return value

    def close(self):
        runtime, self.runtime = self.runtime, None
        del runtime
        gc.collect()


class CtypesAdapter(RuntimeAdapter):
    def execute(self, source, label):
        return self.runtime.run(source, label)

    def integer_global(self, name):
        return self.runtime.integer_global(name)

    def string_global(self, name):
        return self.runtime.string_global(name)

    def close(self):
        runtime, self.runtime = self.runtime, None
        runtime.close()


def create_runtime(version, backend):
    if backend != 'ctypes':
        module_name = 'lupa.lua' + version.replace('.', '')
        try:
            module = importlib.import_module(module_name)
        except (ImportError, OSError):
            if backend == 'lupa':
                raise
        else:
            runtime = module.LuaRuntime()
            return LupaAdapter(version, 'lupa', runtime, module.__file__)
    dll = DLLS[version]
    runtime = Lua(dll, version)
    return CtypesAdapter(version, 'ctypes', runtime, dll)


def run(output, lua_backend):
    output = Path(output)
    output.unlink(missing_ok=True)
    before = input_state_sha256(filesystem_files(ROOT))
    suite = unittest.TestSuite()
    for module in ('test_limited_repair_release', 'test_lua_localization_generation',
                   'test_limited_repository_evidence', 'test_limited_repository_evidence_public4'):
        suite.addTests(unittest.defaultTestLoader.loadTestsFromName(module))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful() or result.skipped or result.testsRun != 30:
        raise ValueError('All 30 limited packaging/generation/evidence tests must pass without skips')
    compat = ROOT / 'source/compat'
    mod = ROOT / 'mods/FU_Japanese'
    species = json.loads((mod / 'fujp/species_display.config').read_text(encoding='utf-8'))
    guides = json.loads((mod / 'fujp/guide_display.config').read_text(encoding='utf-8'))
    setup, extra_suite, names = build_suite(species, guides)
    runtimes = []
    for version in ('5.3', '5.4'):
        extra = create_runtime(version, lua_backend)
        core = None
        try:
            extra.execute(setup, 'initialize extra display suite')
            for asset in ('species_display.lua', 'guide_display.lua'):
                extra.execute((mod / 'fujp' / asset).read_text(encoding='utf-8'), 'load ' + asset)
            extra.execute(extra_suite, 'execute extra display suite')
            extra_cases = extra.integer_global('__caseCount')
            extra_assertions = extra.integer_global('__assertionCount')
            assert extra_cases == len(names), 'extra display case inventory differs from the executed cases'
            core = create_runtime(version, lua_backend)
            core.execute('localizedRoot=' + lua_value(mod.as_posix()) + '\n'
                         + 'upstreamRoot="";displayFallbackOnly=true;formatFixtures={};\n'
                         + 'displayDictionaries=' + lua_value(json.loads((mod / 'fujp/lua_display.config').read_text(encoding='utf-8'))),
                         'initialize core localization suite')
            core.execute((compat / 'test_lua_localization.lua').read_text(encoding='utf-8'), 'execute core localization suite')
            data = json.loads(core.string_global('luaLocalizationReport'))
            assert data['runtime'] == 'Lua ' + version
            assert data['cases'] == 8 and data['assertions'] == 142 and data['status'] == 'passed'
            runtime_info = extra.artifact()
            assert core.backend == extra.backend and core.binary == extra.binary
            runtimes.append({'runtime':data['runtime'], **runtime_info, 'core_cases':8, 'core_assertions':142,
                             'extra_cases':extra_cases, 'extra_assertions':extra_assertions, 'passed':True})
        finally:
            if core is not None:
                core.close()
            extra.close()
    after = input_state_sha256(filesystem_files(ROOT))
    if before != after:
        raise ValueError('Source/MOD inputs changed while running limited repair tests')
    harnesses = ('source/compat/test_extra_display_fallback.py',
                 'source/compat/test_lua_localization.lua',
                 'source/tools/run_limited_helper_tests.py')
    report = {'schema':1, 'passed':True, 'failures':0, 'errors':0, 'skipped':0,
              'input_state_sha256':after, 'unit_tests':result.testsRun, 'requested_lua_backend':lua_backend,
              'runtimes':runtimes,
              'harness_sha256':{name:sha((ROOT / name).read_bytes()) for name in harnesses},
              'helper_sha256':{path:sha((ROOT / path).read_bytes()) for path in (
                  'source/compat/followup_022/fujp/species_display.lua',
                  'source/compat/followup_022/fujp/guide_display.lua',
                  'mods/FU_Japanese/fujp/species_display.lua',
                  'mods/FU_Japanese/fujp/guide_display.lua')},
              'native_game_executed':False, 'whole_mod_runtime_tested':False}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report-output', type=Path, default=ROOT.parent / '.local/display-warning-20261114/limited-helper-tests.json')
    parser.add_argument('--lua-backend', choices=('auto', 'lupa', 'ctypes'), default='auto')
    arguments = parser.parse_args()
    run(arguments.report_output, arguments.lua_backend)
