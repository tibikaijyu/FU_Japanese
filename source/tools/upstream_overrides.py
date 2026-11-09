from __future__ import annotations
import hashlib
import json
from pathlib import Path

EXPECTED_ASSETS = {"radiomessages/fu_quests.radiomessages"}

def manifest(project):
    project = Path(project)
    path = project / "source/upstream_overrides.json"
    if not path.is_file():
        raise ValueError("Pinned upstream override manifest is missing")
    data = json.loads(path.read_text(encoding="utf-8"))
    assets = data.get("assets", {})
    if set(assets) != EXPECTED_ASSETS:
        raise ValueError("Pinned upstream override scope must be exactly the radio asset")
    for asset, entry in assets.items():
        if entry.get("repository") != "sayterdarkwynd/FrackinUniverse" or entry.get("commit") != "1c80b714c8b7da9ce3d35f237850ffdb236b9a2e":
            raise ValueError("Pinned radio override source revision changed")
        asset_path = project / entry["path"]
        if not asset_path.is_file():
            raise ValueError("Pinned upstream override is missing: " + asset)
        digest = hashlib.sha256(asset_path.read_bytes()).hexdigest()
        if digest != entry.get("sha256"):
            raise ValueError("Pinned upstream override hash mismatch: " + asset)
    return data

def resolve_asset(project, upstream, asset):
    data = manifest(project)
    entry = data.get("assets", {}).get(asset)
    if entry:
        return Path(project) / entry["path"]
    return Path(upstream) / asset
