"""Regression checks for public packaging, provenance, and portable Lua fixtures."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
import zipfile

from package_release import ROOT, install_files, load_public_files, safe_public_path, sha, write_zip


class PublicReleaseTests(unittest.TestCase):
    def test_zip_is_repeatable_and_has_a_verifiable_manifest(self):
        payload = {"mods/FU_Japanese/example.patch": b"[]\n", "README.md": "日本語\n".encode()}
        with tempfile.TemporaryDirectory() as directory:
            a, b = Path(directory) / "a.zip", Path(directory) / "b.zip"
            write_zip(a, "release", payload)
            write_zip(b, "release", dict(reversed(list(payload.items()))))
            self.assertEqual(a.read_bytes(), b.read_bytes())
            with zipfile.ZipFile(a) as archive:
                self.assertIsNone(archive.testzip())
                for line in archive.read("release/SHA256SUMS.txt").decode().splitlines():
                    expected, name = line.split("  ", 1)
                    self.assertEqual(expected, sha(archive.read("release/" + name)))

    def test_manifest_rejects_changed_content_and_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "file.txt").write_bytes(b"original")
            entry = sha(b"original") + "  file.txt\n"
            (root / "SHA256SUMS.txt").write_text(entry)
            self.assertEqual(load_public_files(root)["file.txt"], b"original")
            (root / "file.txt").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                load_public_files(root)
            (root / "file.txt").write_bytes(b"original")
            (root / "SHA256SUMS.txt").write_text(entry + entry)
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                load_public_files(root)

    def test_local_and_unsafe_paths_are_rejected(self):
        for name in ("../secret", "/absolute", "C:/private", ".git/config", ".local/private",
                     "docs/development/notes.md", "source/reports/scope/raw.jsonl",
                     "source/reports/run.log", "source/machine_translation/fugumt-model/model.bin"):
            with self.subTest(name=name):
                self.assertFalse(safe_public_path(name))
        self.assertTrue(safe_public_path("source/compat/followup_022/fujp/species_display.lua"))

    def test_install_keeps_notices_and_model_provenance_without_development_data(self):
        files = {name: b"fixture" for name in (
            "mods/FU_Japanese/_metadata", "mods/FU_Japanese/ATTRIBUTION.txt",
            "optional/FU_Japanese_Font/LICENSE-MPLUS-EN.txt", "LICENSE.md",
            "docs/INSTALL_JA.txt", "docs/PAK_DISTRIBUTION.md",
            "source/machine_translation/model_provenance.json",
            "source/machine_translation/pre_review_semantic_candidates.jsonl", "source/tools/build.py")}
        selected = install_files(files)
        self.assertIn("PAK_DISTRIBUTION.md", selected)
        self.assertIn("INSTALL_JA.txt", selected)
        self.assertIn("source/machine_translation/model_provenance.json", selected)
        self.assertIn("optional/FU_Japanese_Font/LICENSE-MPLUS-EN.txt", selected)
        self.assertNotIn("source/tools/build.py", selected)
        self.assertNotIn("source/machine_translation/pre_review_semantic_candidates.jsonl", selected)

    @unittest.skipUnless(importlib.util.find_spec("lupa"), "Optional Lua regression requires lupa==2.6")
    def test_portable_species_fixture_executes_actual_lua_with_explicit_mod_path(self):
        from lupa.lua54 import LuaRuntime
        script = (ROOT / "source/tests/followup_022/species/result/species_runtime_test.lua").read_text(encoding="utf-8")
        checks = LuaRuntime().execute(script, (ROOT / "mods/FU_Japanese").as_posix())
        self.assertGreater(checks, 1000)


if __name__ == "__main__":
    unittest.main(verbosity=2)
