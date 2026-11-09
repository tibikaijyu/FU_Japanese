from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from append_index_basis import PakAssets, capture
from append_index_plans import paths_for


def varint(value):
    groups = [value & 0x7f]
    value >>= 7
    while value:
        groups.insert(0, (value & 0x7f) | 0x80)
        value >>= 7
    return bytes(groups)


def sbstring(value):
    data = value.encode("utf-8")
    return varint(len(data)) + data


def package(path, asset_name, payload):
    index_offset = 16 + len(payload)
    index = (b"INDEX" + varint(0) + varint(1) + sbstring("/" + asset_name)
             + (16).to_bytes(8, "big") + len(payload).to_bytes(8, "big"))
    path.write_bytes(b"SBAsset6" + index_offset.to_bytes(8, "big") + payload + index)


class AppendIndexBasisTest(unittest.TestCase):
    def test_capture_records_all_exact_duplicate_occurrences(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            base_asset = "fixtures/names.config"
            base = root / "base.pak"
            payload = json.dumps({"names": [{"text": "Shared"}]}).encode()
            package(base, base_asset, payload)
            layer = root / "fu"
            patch_path = layer / (base_asset + ".patch")
            patch_path.parent.mkdir(parents=True)
            patch_path.write_text(json.dumps([{"op": "add", "path": "/names/-", "value": {"text": "Shared"}}]), encoding="utf-8")
            catalog = root / "append_catalog.jsonl"
            row = {"id": "row-1", "asset": base_asset, "path": "/names/-/text", "source": "Shared", "strategy": "indexed_guards"}
            catalog.write_text(json.dumps(row) + chr(10), encoding="utf-8")
            manifest_path = root / "append_index_basis.json"

            empty_layer = root / "empty"
            empty_layer.mkdir()
            capture(base, [("FU", layer), ("Other", empty_layer)], catalog, manifest_path)

            updated = json.loads(catalog.read_text(encoding="utf-8").strip())
            basis = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(paths_for(updated, basis), ["/names/0/text", "/names/1/text"])
            self.assertEqual(basis["assets"][base_asset]["layers"][1]["layer"], "FU")
            with PakAssets(base) as as_package:
                self.assertEqual(as_package.read(base_asset), payload)
            self.assertNotIn("base_package", basis)
            capture(base, [("FU", layer), ("Other", empty_layer)], catalog, manifest_path, verify_only=True)
            with self.assertRaisesRegex(ValueError, "hashes/order/positions"):
                capture(base, [("Other", empty_layer), ("FU", layer)], catalog, manifest_path, verify_only=True)
            with self.assertRaisesRegex(ValueError, "unique"):
                capture(base, [("FU", layer), ("FU", empty_layer)], catalog, manifest_path, verify_only=True)
            with self.assertRaisesRegex(ValueError, "missing or unsupported"):
                capture(base, [("Missing", root / "missing")], catalog, manifest_path, verify_only=True)
            absent_base = root / "absent.pak"
            package(absent_base, "fixtures/other.config", json.dumps({"ok": True}).encode())
            with self.assertRaisesRegex(ValueError, "No base asset found"):
                capture(absent_base, [], catalog, manifest_path, verify_only=True)
            patch_path.write_text(json.dumps([{"op": "add", "path": "/names/-", "value": {"text": "Changed"}}]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "hashes/order/positions"):
                capture(base, [("FU", layer), ("Other", empty_layer)], catalog, manifest_path, verify_only=True)

    def test_basis_hash_mismatch_requires_recapture(self):
        row = {"id": "row-2", "asset": "a.config", "path": "/names/-", "basis_sha256": "old"}
        basis = {"assets": {"a.config": {"effective_sha256": "new", "paths": {"row-2": ["/names/0"]}}}}
        with self.assertRaisesRegex(ValueError, "re-audit"):
            paths_for(row, basis)


if __name__ == "__main__":
    unittest.main()
