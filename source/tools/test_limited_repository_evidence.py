"""Reject stale or widened limited-release proof while retaining its baseline."""
import copy
import json
import unittest
from unittest.mock import patch

import limited_repository_evidence as evidence
from limited_repair_release import CONFIG_ASSETS, EXPECTED_INPUT_PAK_SHA256, HELPER_ASSETS
from release_evidence import ROOT, filesystem_files, input_state_sha256, sha


class LimitedRepositoryEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current = filesystem_files(ROOT)
        cls.current[evidence.BASELINE] = (ROOT / evidence.BASELINE).read_bytes()

    def fixture(self):
        files = dict(self.current)
        baseline = json.loads(files[evidence.BASELINE])
        state = input_state_sha256(files)
        tests = {'passed':True, 'unit_tests':25, 'failures':0, 'errors':0, 'skipped':0,
                 'input_state_sha256':state, 'native_game_executed':False,
                 'harness_sha256':{p:sha(files[p]) for p in evidence.HARNESSES},
                 'runtimes':[{'runtime':v, 'core_cases':8, 'core_assertions':142,
                              'extra_cases':249, 'extra_assertions':639, 'passed':True}
                             for v in ('Lua 5.3', 'Lua 5.4')]}
        record = {'schema':1, 'scope':'three-helper-repair', 'release_id':'0.2.4-public.3',
                  'artifact':evidence.ARTIFACT, 'generation_report_sha256':evidence.GENERATION_SHA256,
                  'input_state_sha256':state, 'input_pak_sha256':EXPECTED_INPUT_PAK_SHA256,
                  'baseline_manifest_sha256':sha(files[evidence.BASELINE]),
                  'approved_helpers':HELPER_ASSETS,
                  'baseline_helpers':{p:baseline[p] for p in HELPER_ASSETS},
                  'tested_config_sha256':{p:sha(files['mods/FU_Japanese/' + p]) for p in CONFIG_ASSETS},
                  'official_roundtrip':{'file_count':len(baseline), 'relative_paths_match':True,
                                        'non_metadata_raw_sha256_match':True, 'metadata_json_deep_equal':True},
                  'whole_mod_rebuilt':False, 'native_game_executed':False}
        return files, copy.deepcopy(record), tests

    @staticmethod
    def bind(files, record, tests):
        files[evidence.TESTS] = json.dumps(tests).encode()
        record['test_report_sha256'] = sha(files[evidence.TESTS])
        files[evidence.RECORD] = json.dumps(record).encode()

    def test_accepts_the_current_three_helper_scope(self):
        files, record, tests = self.fixture()
        current_helpers = {asset:sha(files[path]) for asset,path in evidence.SOURCE_PATHS.items()}
        record['approved_helpers'] = current_helpers
        with patch.object(evidence, 'HELPER_ASSETS', current_helpers):
            self.bind(files, record, tests)
            self.assertEqual(evidence.validate(files)['scope'], 'three-helper-repair')

    def test_rejects_current_payload_under_historical_public3_helper_hashes(self):
        files, record, tests = self.fixture()
        self.bind(files, record, tests)
        with self.assertRaisesRegex(ValueError, 'Reviewed helper differs'):
            evidence.validate(files)

    def test_rejects_changed_source_with_old_test_proof(self):
        files, record, tests = self.fixture()
        files['source/tools/run_limited_helper_tests.py'] += b'\n'
        self.bind(files, record, tests)
        with self.assertRaisesRegex(ValueError, 'stale'):
            evidence.validate(files)

    def test_rejects_a_different_helper_even_after_rebinding_the_inventory(self):
        files, record, tests = self.fixture()
        files['mods/FU_Japanese/fujp/guide_display.lua'] += b'\n'
        record['input_state_sha256'] = tests['input_state_sha256'] = input_state_sha256(files)
        self.bind(files, record, tests)
        with self.assertRaisesRegex(ValueError, 'Reviewed helper differs'):
            evidence.validate(files)

    def test_rejects_changed_artifact_failed_roundtrip_or_whole_mod_claim(self):
        files, record, tests = self.fixture()
        for key in ('artifact', 'roundtrip', 'claim'):
            candidate = copy.deepcopy(record)
            if key == 'artifact': candidate['artifact']['sha256'] = '0' * 64
            elif key == 'roundtrip': candidate['official_roundtrip']['metadata_json_deep_equal'] = False
            else: candidate['whole_mod_rebuilt'] = True
            self.bind(files, candidate, tests)
            with self.subTest(key=key), self.assertRaises(ValueError):
                evidence.validate(files)


if __name__ == '__main__':
    unittest.main(verbosity=2)
