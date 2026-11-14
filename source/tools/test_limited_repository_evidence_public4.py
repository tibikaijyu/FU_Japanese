"""Exercise the public.4 approval without modifying the historical public.3 proof."""
import copy
import json
import unittest

import limited_repository_evidence_public4 as evidence
from release_evidence import filesystem_files, input_state_sha256, sha


class Public4EvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = filesystem_files(evidence.ROOT)
        extra = {evidence.BASELINE,evidence.HISTORICAL}
        extra.update(evidence.FONT_PREFIX + name for name in evidence.FONT_ALLOWLIST)
        extra.update(source for source,_ in evidence.DOCS)
        for path in extra:
            cls.current[path] = (evidence.ROOT / path).read_bytes()

    def fixture(self):
        files = dict(self.current)
        baseline = json.loads(files[evidence.BASELINE])
        historical = json.loads(files[evidence.HISTORICAL])
        current_helpers = {asset:sha(files[path]) for asset,path in evidence.SOURCE_PATHS.items()}
        tests = {
            'passed':True, 'failures':0, 'errors':0, 'skipped':0, 'unit_tests':30,
            'input_state_sha256':'pending',
            'harness_sha256':{p:sha(files[p]) for p in evidence.HARNESS_PATHS},
            'helper_sha256':{p:sha(files[p]) for p in (
                'source/compat/followup_022/fujp/species_display.lua',
                'source/compat/followup_022/fujp/guide_display.lua',
                'mods/FU_Japanese/fujp/species_display.lua',
                'mods/FU_Japanese/fujp/guide_display.lua')},
            'runtimes':[{'runtime':v,'backend':'ctypes','binary_sha256':'a'*64,
                         'core_cases':8,'core_assertions':142,'extra_cases':262,
                         'extra_assertions':785,'passed':True} for v in ('Lua 5.3','Lua 5.4')],
            'native_game_executed':False,'whole_mod_runtime_tested':False,
        }
        record = {
            'schema':1,'scope':'two-helper-display-repair','release_id':'0.2.4-public.4',
            'input_state_sha256':'pending','test_report_sha256':'pending',
            'baseline_manifest_sha256':sha(files[evidence.BASELINE]),
            'historical_public3_record_sha256':sha(files[evidence.HISTORICAL]),
            'input_pak_sha256':historical['pak_sha256'],
            'approved_helpers':current_helpers,
            'baseline_helpers':{asset:historical['approved_helpers'][asset] for asset in evidence.SOURCE_PATHS},
            'changed_game_assets':sorted(evidence.SOURCE_PATHS),
            'tested_config_sha256':{n:sha(files['mods/FU_Japanese/'+n]) for n in (
                'fujp/lua_display.config','fujp/species_display.config','fujp/guide_display.config')},
            'official_roundtrip':{'file_count':len(baseline),'relative_paths_match':True,
                'non_metadata_raw_sha256_match':True,'metadata_json_deep_equal':True},
            'font_roundtrip':{'file_count':len(evidence.FONT_ALLOWLIST),'relative_paths_match':True,
                'non_metadata_raw_sha256_match':True,'metadata_json_deep_equal':True},
            'font_pak_sha256':'b'*64,
            'font_files':{n:sha(files[evidence.FONT_PREFIX+n]) for n in evidence.FONT_ALLOWLIST},
            'artifact':{'file':'FU_Japanese_0.2.4-public.4-pak.1-install.zip','files':14,
                        'bytes':100,'sha256':'c'*64,'crc_and_content_verified':True},
            'upload_allowlist':['FU_Japanese_0.2.4-public.4-pak.1-install.zip'],
            'packaged_paths':[dest for _,dest in evidence.DOCS],
            'packaged_document_sha256':{src:sha(files[src]) for src,_ in evidence.DOCS},
            'whole_mod_rebuilt':False,'native_game_executed':False,
            'multiplayer_disconnect_cause_verified':False,
        }
        files[evidence.TESTS] = json.dumps(tests).encode()
        state = input_state_sha256(files)
        tests['input_state_sha256'] = state
        files[evidence.TESTS] = json.dumps(tests).encode()
        record['input_state_sha256'] = state
        record['test_report_sha256'] = sha(files[evidence.TESTS])
        files[evidence.RECORD] = json.dumps(record).encode()
        return files, record, tests

    def test_accepts_explicit_two_helper_public4_approval(self):
        files, _, _ = self.fixture()
        self.assertEqual(evidence.validate(files)['release_id'],'0.2.4-public.4')

    def test_rejects_historical_public3_record_as_public4_approval(self):
        files, _, _ = self.fixture()
        files[evidence.RECORD] = files[evidence.HISTORICAL]
        with self.assertRaises(ValueError):
            evidence.validate(files)

    def test_rejects_unapproved_game_asset_even_after_rebinding_report(self):
        files, record, tests = self.fixture()
        files['mods/FU_Japanese/fujp/lua_display.lua'] += b'\n'
        state = input_state_sha256(files)
        record['input_state_sha256'] = tests['input_state_sha256'] = state
        files[evidence.TESTS] = json.dumps(tests).encode()
        record['test_report_sha256'] = sha(files[evidence.TESTS])
        files[evidence.RECORD] = json.dumps(record).encode()
        with self.assertRaisesRegex(ValueError,'outside its two approved helpers'):
            evidence.validate(files)

    def test_rejects_font_file_set_or_document_drift(self):
        files, record, _ = self.fixture()
        record['font_files']['hobo.ttf'] = '0'*64
        files[evidence.RECORD] = json.dumps(record).encode()
        with self.assertRaisesRegex(ValueError,'font payload'):
            evidence.validate(files)
        files, record, _ = self.fixture()
        files[evidence.FONT_PREFIX + 'unexpected.ttf'] = b'not allowlisted'
        with self.assertRaisesRegex(ValueError,'font payload'):
            evidence.validate(files)
        files, record, _ = self.fixture()
        files['docs/README_JA.md'] += b'\n'
        record['packaged_document_sha256']['docs/README_JA.md'] = '0'*64
        files[evidence.RECORD] = json.dumps(record).encode()
        with self.assertRaisesRegex(ValueError,'Packaged document'):
            evidence.validate(files)


if __name__ == '__main__':
    unittest.main(verbosity=2)
