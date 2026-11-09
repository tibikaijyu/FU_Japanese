"""Focused tests for isolated PAK packaging and round-trip validation."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from package_release import build_verified_pak, install_files, pak_install_files, verify_pak_tree


class PakReleaseTests(unittest.TestCase):
    def write_tree(self, root, entries):
        for name, data in entries.items():
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)

    def test_roundtrip_checks_paths_assets_and_canonical_metadata(self):
        entries = {
            "_metadata": b'{"version":"0.2.4-fu6.5.8","priority":1000}\n',
            "objects/example.object": b'{"name":"example"}\n',
            "scripts/example.lua": b"return true\n",
        }
        with tempfile.TemporaryDirectory() as temporary:
            source, unpacked = Path(temporary) / "source", Path(temporary) / "unpacked"
            source.mkdir(); unpacked.mkdir()
            self.write_tree(source, entries)
            self.write_tree(unpacked, {
                "_metadata": b'{\n  "priority" : 1000,\n  "version" : "0.2.4-fu6.5.8"\n}\n',
                "objects/example.object": entries["objects/example.object"],
                "scripts/example.lua": entries["scripts/example.lua"],
            })
            result = verify_pak_tree(source, unpacked)
        self.assertTrue(result["relative_paths_match"])
        self.assertTrue(result["non_metadata_raw_sha256_match"])
        self.assertTrue(result["metadata_json_deep_equal"])
        self.assertFalse(result["metadata_raw_sha256"]["equal"])
        self.assertFalse(result["all_raw_bytes_equal"])

    def test_roundtrip_rejects_asset_or_metadata_drift(self):
        with tempfile.TemporaryDirectory() as temporary:
            source, unpacked = Path(temporary) / "source", Path(temporary) / "unpacked"
            source.mkdir(); unpacked.mkdir()
            base = {"_metadata": b'{"priority":1}\n', "a.txt": b"a"}
            self.write_tree(source, base)
            self.write_tree(unpacked, {"_metadata": b'{"priority":1}\n', "a.txt": b"b"})
            with self.assertRaisesRegex(ValueError, "content SHA-256 mismatch"):
                verify_pak_tree(source, unpacked)
            (unpacked / "a.txt").write_bytes(b"a")
            (unpacked / "_metadata").write_bytes(b'{"priority":true}\n')
            with self.assertRaisesRegex(ValueError, "structure/value/type changed"):
                verify_pak_tree(source, unpacked)
            (unpacked / "_metadata").write_bytes(base["_metadata"])
            (unpacked / "extra.txt").write_bytes(b"extra")
            with self.assertRaisesRegex(ValueError, "path mismatch"):
                verify_pak_tree(source, unpacked)

    def test_pack_uses_only_mod_files_and_install_zip_payload_is_pak_only(self):
        files = {
            "mods/FU_Japanese/_metadata": b'{"version":"0.2.4-fu6.5.8"}\n',
            "mods/FU_Japanese/example.patch": b"[]\n",
            "source/tools/build.py": b"development only",
            "docs/INSTALL_JA.txt": b"See PAK_DISTRIBUTION.md for the PAK install steps.\n",
            "docs/PAK_DISTRIBUTION.md": b"PAK install guide",
        }
        with tempfile.TemporaryDirectory() as temporary:
            tools = Path(temporary) / "win32"
            tools.mkdir()
            (tools / "asset_packer.exe").write_bytes(b"mock packer")
            (tools / "asset_unpacker.exe").write_bytes(b"mock unpacker")

            def mock_run(args, **_kwargs):
                if args[0].endswith("asset_packer.exe"):
                    self.assertEqual(
                        sorted(path.relative_to(Path(args[1])).as_posix()
                               for path in Path(args[1]).rglob("*") if path.is_file()),
                        ["_metadata", "example.patch"],
                    )
                    Path(args[2]).write_bytes(b"mock pak bytes")
                else:
                    source = Path(args[1]).parent / "input" / "FU_Japanese"
                    shutil.copytree(source, Path(args[2]))
                return None

            with patch("package_release.subprocess.run", side_effect=mock_run):
                pak, report = build_verified_pak(files, tools, Path(temporary))
        self.assertEqual(pak, b"mock pak bytes")
        self.assertEqual(report["file_count"], 2)
        folder_selected = install_files(files)
        selected = pak_install_files(files, pak)
        self.assertIn("mods/FU_Japanese.pak", selected)
        self.assertFalse(any(name.startswith("mods/FU_Japanese/") for name in selected))
        self.assertNotIn("source/tools/build.py", selected)
        for install_payload in (folder_selected, selected):
            self.assertEqual(install_payload["INSTALL_JA.txt"],
                             b"See PAK_DISTRIBUTION.md for the PAK install steps.\n")
            self.assertIn("PAK_DISTRIBUTION.md", install_payload)

    def test_pak_release_id_requires_pak_tools(self):
        script = Path(__file__).with_name("package_release.py")
        result = subprocess.run(
            [sys.executable, str(script), "--pak-release-id", "0.2.4-public.1-pak.1"],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--pak-release-id requires --pak-tools-dir", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
