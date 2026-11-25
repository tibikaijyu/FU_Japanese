"""The new release may add only its reviewed writer to the public.4 payload."""
import unittest

import particle_repair_release as release


class ParticleReleaseScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = release.current_public_files(release.ROOT)

    def test_current_payload_matches_the_reviewed_delta(self):
        expected = release.assert_payload(self.files)
        self.assertEqual(expected[release.ASSET], release.REVIEWED_SHA)

    def test_unrelated_game_change_is_rejected(self):
        changed = dict(self.files)
        changed['mods/FU_Japanese/unreviewed.lua'] = b'return true'
        with self.assertRaises(ValueError):
            release.assert_payload(changed)

    def test_source_and_mod_must_both_match_the_reviewed_writer(self):
        for name in (release.SOURCE, 'mods/FU_Japanese/' + release.ASSET):
            changed = dict(self.files)
            changed[name] += b'\n'
            with self.assertRaises(ValueError):
                release.assert_payload(changed)


if __name__ == '__main__':
    unittest.main(verbosity=2)
