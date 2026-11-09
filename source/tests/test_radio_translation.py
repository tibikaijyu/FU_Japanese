from __future__ import annotations
import hashlib
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from common import read_asset
from validate import apply_batches
from build import check_translation, verify_radio_catalog, build
from upstream_overrides import manifest

ASSET = "radiomessages/fu_quests.radiomessages"
PROJECT = ROOT
MOD = ROOT.parent / "mods/FU_Japanese"

class RadioTranslationTest(unittest.TestCase):
    def test_catalog_rows_must_match_all_pinned_radio_text_and_sender_fields(self):
        rows = [json.loads(line) for line in (PROJECT / 'source/catalog.jsonl').read_text(encoding='utf-8').splitlines()]
        verify_radio_catalog(PROJECT, rows)
        radio_rows = [row for row in rows if row['asset'] == ASSET]
        with self.assertRaisesRegex(ValueError, 'Radio catalog does not match'):
            verify_radio_catalog(PROJECT, [row for row in rows if row is not radio_rows[0]])
        stale = [dict(row) for row in rows]
        target = next(row for row in stale if row['asset'] == ASSET)
        target['source'] += ' stale'
        with self.assertRaisesRegex(ValueError, 'Radio catalog does not match'):
            verify_radio_catalog(PROJECT, stale)

    def test_partial_build_modes_are_mutually_exclusive_at_entry(self):
        with self.assertRaisesRegex(ValueError, 'Choose --asset-only or --indexed-assets'):
            build(PROJECT, None, None, MOD, asset_only=ASSET, indexed_assets=True)

    def test_pinned_radio_patch_translates_all_bodies_and_only_display_fields(self):
        override = manifest(PROJECT)["assets"][ASSET]
        source_path = PROJECT / override["path"]
        self.assertEqual(hashlib.sha256(source_path.read_bytes()).hexdigest(), override["sha256"])
        before = read_asset(source_path)
        patch_path = MOD / (ASSET + ".patch")
        groups = read_asset(patch_path)
        after = apply_batches(before, groups)
        self.assertEqual(len(before), 26)
        self.assertEqual(len(groups), 46)
        self.assertEqual(set(before), set(after))
        for message_id, original in before.items():
            translated = after[message_id]
            for field in original:
                if field not in {"text", "senderName"}:
                    self.assertEqual(original[field], translated[field], (message_id, field))
            self.assertNotEqual(original["text"], translated["text"], message_id)
            self.assertRegex(translated["text"], r"[\u3040-\u30ff\u3400-\u9fff]")
            self.assertEqual(check_translation(original["text"], translated["text"]), [], message_id)
        self.assertIn("[Shift] + [Mouse 1]", after["fu_start_Complete2a"]["text"])
        self.assertIn("[ Mouse 1 ]", after["fu_start_Complete2a"]["text"])

if __name__ == "__main__":
    unittest.main()
