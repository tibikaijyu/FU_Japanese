"""Tests source-to-MOD synchronization for the reviewed FU display helpers."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from lua_localization import DISPLAY_HELPER_SOURCES, build_display_helpers


class DisplayHelperGenerationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / "source"
        self.output = Path(self.temp.name) / "mods/FU_Japanese"
        for source_rel, _ in DISPLAY_HELPER_SOURCES:
            path = self.project / source_rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(("return " + repr(source_rel) + "\n").encode())

    def test_syncs_every_reviewed_helper_byte_for_byte_after_syntax_checks(self):
        with patch("lua_localization.run_lua") as syntax_check:
            generated = build_display_helpers(self.project, self.output, object())
        self.assertEqual(len(generated), 3)
        self.assertEqual(syntax_check.call_count, 3)
        for (source_rel, asset_rel), (source, destination) in zip(DISPLAY_HELPER_SOURCES, generated):
            self.assertEqual(destination, self.output / asset_rel)
            self.assertEqual(source, self.project / source_rel)
            self.assertEqual(destination.read_bytes(), (self.project / source_rel).read_bytes())

    def test_missing_helper_fails_before_any_generated_file_is_written(self):
        (self.project / DISPLAY_HELPER_SOURCES[-1][0]).unlink()
        with patch("lua_localization.run_lua"):
            with self.assertRaises(FileNotFoundError):
                build_display_helpers(self.project, self.output, object())
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
