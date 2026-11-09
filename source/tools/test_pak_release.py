"""Focused tests for isolated PAK packaging and round-trip validation."""
from pathlib import Path
import shutil
import subprocess
import contextlib
import io
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from package_release import (
    FONT_FILE_ALLOWLIST,
    build_verified_font_pak,
    build_verified_pak,
    install_files,
    package,
    pak_install_files,
    verify_pak_tree,
)


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
        self.assertFalse(any(name.startswith("optional/FU_Japanese_Font/") for name in selected))
        self.assertNotIn("source/tools/build.py", selected)
        for install_payload in (folder_selected, selected):
            self.assertEqual(install_payload["INSTALL_JA.txt"],
                             b"See PAK_DISTRIBUTION.md for the PAK install steps.\n")
            self.assertIn("PAK_DISTRIBUTION.md", install_payload)

    def test_font_pak_uses_exact_allowlist_and_license_files_are_outside_it(self):
        files = {
            "optional/FU_Japanese_Font/_metadata": b'{"name":"FU Japanese Font"}\n',
            "optional/FU_Japanese_Font/hobo.ttf": b"font bytes",
            "optional/FU_Japanese_Font/ATTRIBUTION.txt": b"font attribution",
            "optional/FU_Japanese_Font/LICENSE-MPLUS-EN.txt": b"English license",
            "optional/FU_Japanese_Font/LICENSE-MPLUS-JA.txt": b"Japanese license",
            "mods/FU_Japanese/_metadata": b'{"version":"0.2.4-fu6.5.8"}\n',
            "mods/FU_Japanese/ATTRIBUTION.txt": b"FU attribution",
            "mods/FU_Japanese/LICENSE-FU-CC-BY-4.0.txt": b"CC BY text",
            "LICENSE.md": (
                b"[FU license](mods/FU_Japanese/LICENSE-FU-CC-BY-4.0.txt)\n"
                b"[Font license](optional/FU_Japanese_Font/LICENSE-MPLUS-JA.txt)\n"
            ),
            "THIRD_PARTY_NOTICES.md": (
                b"[FU attribution](mods/FU_Japanese/ATTRIBUTION.txt)\n"
                b"[Font attribution](optional/FU_Japanese_Font/ATTRIBUTION.txt)\n"
                b"[English license](optional/FU_Japanese_Font/LICENSE-MPLUS-EN.txt)\n"
            ),
            "docs/INSTALL_JA.txt": b"install",
            "docs/PAK_DISTRIBUTION.md": b"pak guide",
        }
        self.assertEqual({name.split("/", 2)[-1] for name in files if name.startswith("optional/FU_Japanese_Font/")},
                         FONT_FILE_ALLOWLIST)
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
                        sorted(FONT_FILE_ALLOWLIST),
                    )
                    Path(args[2]).write_bytes(b"mock font pak")
                else:
                    shutil.copytree(Path(args[1]).parent / "input" / "FU_Japanese_Font", Path(args[2]))
                return None

            with patch("package_release.subprocess.run", side_effect=mock_run):
                font_pak, verification = build_verified_font_pak(files, tools, Path(temporary))
        self.assertEqual(font_pak, b"mock font pak")
        self.assertEqual(verification["file_count"], len(FONT_FILE_ALLOWLIST))
        selected = pak_install_files(files, b"mock main pak", font_pak)
        self.assertEqual(selected["mods/FU_Japanese.pak"], b"mock main pak")
        self.assertEqual(selected["optional/FU_Japanese_Font.pak"], b"mock font pak")
        self.assertNotIn("mods/FU_Japanese/ATTRIBUTION.txt", selected)
        self.assertNotIn("optional/FU_Japanese_Font/ATTRIBUTION.txt", selected)
        self.assertEqual(selected["LICENSES/FU_Japanese/ATTRIBUTION.txt"], b"FU attribution")
        self.assertEqual(selected["LICENSES/FU_Japanese/LICENSE-FU-CC-BY-4.0.txt"], b"CC BY text")
        self.assertEqual(selected["LICENSES/FU_Japanese_Font/ATTRIBUTION.txt"], b"font attribution")
        self.assertEqual(selected["LICENSES/FU_Japanese_Font/LICENSE-MPLUS-EN.txt"], b"English license")
        self.assertEqual(selected["LICENSES/FU_Japanese_Font/LICENSE-MPLUS-JA.txt"], b"Japanese license")
        for document in ("LICENSE.md", "THIRD_PARTY_NOTICES.md"):
            for path in ("mods/FU_Japanese/", "optional/FU_Japanese_Font/"):
                self.assertNotIn(path.encode(), selected[document])
            for path in ("LICENSES/FU_Japanese/", "LICENSES/FU_Japanese_Font/"):
                self.assertIn(path.encode(), selected[document])

    def test_package_outputs_only_allowlisted_pak_zip_and_preserves_old_dist(self):
        files = {
            "mods/FU_Japanese/_metadata": b'{"version":"0.2.4-fu6.5.8"}\n',
            "mods/FU_Japanese/ATTRIBUTION.txt": b"FU attribution",
            "mods/FU_Japanese/LICENSE-FU-CC-BY-4.0.txt": b"CC BY text",
            "optional/FU_Japanese_Font/_metadata": b'{"name":"FU Japanese Font"}\n',
            "optional/FU_Japanese_Font/hobo.ttf": b"font bytes",
            "optional/FU_Japanese_Font/ATTRIBUTION.txt": b"font attribution",
            "optional/FU_Japanese_Font/LICENSE-MPLUS-EN.txt": b"English license",
            "optional/FU_Japanese_Font/LICENSE-MPLUS-JA.txt": b"Japanese license",
            "LICENSE.md": b"[FU license](mods/FU_Japanese/LICENSE-FU-CC-BY-4.0.txt)\n",
            "THIRD_PARTY_NOTICES.md": (
                b"[FU attribution](mods/FU_Japanese/ATTRIBUTION.txt)\n"
                b"[Font license](optional/FU_Japanese_Font/LICENSE-MPLUS-JA.txt)\n"
            ),
            "docs/INSTALL_JA.txt": b"Install PAK",
            "docs/PAK_DISTRIBUTION.md": b"PAK only",
        }
        verification = {"relative_paths_match": True, "file_count": 2,
                        "non_metadata_raw_sha256_match": True, "metadata_json_deep_equal": True}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            output = root / "dist"
            output.mkdir(parents=True)
            old_archive = output / "FU_Japanese_0.2.3-public.9-pak.1-install.zip"
            old_archive.write_bytes(b"preserve old release")
            tools = root / "win32"
            tools.mkdir()
            with patch("package_release.load_public_files", return_value=files), \
                 patch("package_release.validate_release", return_value="0.2.4-fu6.5.8"), \
                 patch("package_release.build_verified_pak", return_value=(b"main pak", verification)), \
                 patch("package_release.build_verified_font_pak", return_value=(b"font pak", verification)), \
                 contextlib.redirect_stdout(io.StringIO()):
                report = package(root, output, "0.2.4-public.2", tools,
                                 "0.2.4-public.2-pak.1")

            self.assertEqual(report["upload_allowlist"], ["FU_Japanese_0.2.4-public.2-pak.1-install.zip"])
            self.assertEqual([row["file"] for row in report["artifacts"]], report["upload_allowlist"])
            self.assertEqual(report["pak_distribution"]["packages"][0]["path"], "mods/FU_Japanese.pak")
            self.assertEqual(report["pak_distribution"]["packages"][1]["path"],
                             "optional/FU_Japanese_Font.pak")
            self.assertEqual(old_archive.read_bytes(), b"preserve old release")
            self.assertFalse((output / "FU_Japanese_0.2.4-public.2-install.zip").exists())
            self.assertFalse((output / "FU_Japanese_0.2.4-public.2-source.zip").exists())
            archive_path = output / report["upload_allowlist"][0]
            with zipfile.ZipFile(archive_path) as archive:
                names = set(archive.namelist())
                self.assertTrue(any(name.endswith("/mods/FU_Japanese.pak") for name in names))
                self.assertTrue(any(name.endswith("/optional/FU_Japanese_Font.pak") for name in names))
                self.assertFalse(any("/mods/FU_Japanese/" in name for name in names))
                self.assertFalse(any("/optional/FU_Japanese_Font/" in name for name in names))
                self.assertFalse(any("/source/" in name for name in names))
            checksums = (output / report["checksum_file"]).read_text(encoding="utf-8").splitlines()
            self.assertEqual(len(checksums), 1)
            self.assertIn(report["upload_allowlist"][0], checksums[0])

    def test_missing_tools_fail_without_creating_archives(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            output = root / "dist"
            with self.assertRaisesRegex(ValueError, "folder fallback is disabled"):
                package(root, output, "0.2.4-public.2")
            self.assertFalse(output.exists())

    def test_pack_failure_writes_no_archive(self):
        files = {"mods/FU_Japanese/_metadata": b'{}\n'}
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repo"
            output = root / "dist"
            with patch("package_release.load_public_files", return_value=files), \
                 patch("package_release.validate_release", return_value="0.2.4-fu6.5.8"), \
                 patch("package_release.build_verified_pak", side_effect=RuntimeError("unpacker failed")):
                with self.assertRaisesRegex(RuntimeError, "unpacker failed"):
                    package(root, output, "0.2.4-public.2", Path(temporary),
                            "0.2.4-public.2-pak.1")
            self.assertEqual(list(output.glob("*.zip")), [])

    def test_cli_requires_official_pak_tools(self):
        script = Path(__file__).with_name("package_release.py")
        result = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--pak-tools-dir", result.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
