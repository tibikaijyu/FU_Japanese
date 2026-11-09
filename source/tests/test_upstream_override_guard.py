from __future__ import annotations
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from extract import extract
from build import build
from upstream_overrides import manifest

ASSET = "radiomessages/fu_quests.radiomessages"
COMMIT = "1c80b714c8b7da9ce3d35f237850ffdb236b9a2e"
FIXTURE = ROOT / "upstream-overrides" / ASSET

class UpstreamOverrideGuardTest(unittest.TestCase):
    def write_manifest(self, project, source):
        path = project / "upstream-overrides" / ASSET
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(source)
        data = {"version":1,"assets":{ASSET:{"path":"upstream-overrides/"+ASSET,"repository":"sayterdarkwynd/FrackinUniverse","commit":COMMIT,"sha256":hashlib.sha256(source).hexdigest()}}}
        (project / "source").mkdir(parents=True, exist_ok=True)
        (project / "source/upstream_overrides.json").write_text(json.dumps(data),encoding="utf-8")
        return path

    def test_changed_radio_source_blocks_extract_and_build_before_writes(self):
        source = FIXTURE.read_bytes()
        with tempfile.TemporaryDirectory(dir=ROOT) as temp:
            project = Path(temp) / "project"
            path = self.write_manifest(project, source)
            dest = project / "source"
            dest.mkdir(parents=True,exist_ok=True)
            (dest / "catalog.jsonl").write_text("old-catalog\n",encoding="utf-8")
            (dest / "append_catalog.jsonl").write_text("",encoding="utf-8")
            path.write_bytes(source + b" ")
            with self.assertRaisesRegex(ValueError,"hash mismatch"):
                extract(project / "upstream-overrides",dest,[ASSET])
            self.assertEqual((dest / "catalog.jsonl").read_text(encoding="utf-8"),"old-catalog\n")
            out = project.parent / "mods/FU_Japanese"
            out.mkdir(parents=True)
            marker = out / "marker.txt"
            marker.write_text("preserve",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"hash mismatch"):
                build(project,project.parent / "upstream",project / "machine.json",out,"missing-inputs.json",ASSET)
            self.assertEqual(marker.read_text(encoding="utf-8"),"preserve")

if __name__ == "__main__":
    unittest.main()
