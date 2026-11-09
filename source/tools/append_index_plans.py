"""Fixed, asset-derived JSON pointers for FU appended display fields."""
from __future__ import annotations

import collections


def plan_for(row, basis):
    """Resolve a row only through the captured, hash-pinned effective asset basis."""
    if row.get("strategy") == "npc_status_lookup" or row["asset"] == "npcs/statuses.config":
        return {"strategy": "npc_status_lookup", "paths": [], "reason": "Exact runtime display lookup; array indices are irrelevant."}
    asset = basis.get("assets", {}).get(row["asset"])
    if not asset:
        raise ValueError("Missing append basis asset; recapture against installed layers: " + row["asset"])
    if row.get("basis_sha256") != asset.get("effective_sha256"):
        raise ValueError("Append basis hash changed; re-audit asset before building: " + row["asset"])
    paths = asset.get("paths", {}).get(row["id"])
    if not paths:
        raise ValueError("No exact source pointer in captured asset basis: " + row["asset"] + row["path"])
    if len(paths) != len(set(paths)):
        raise ValueError("Duplicate pointer in append basis: " + row["id"])
    return {"strategy": "fixed_index", "paths": paths, "basis_sha256": asset["effective_sha256"]}


def paths_for(row, basis):
    return plan_for(row, basis)["paths"]


def summarize(rows, basis):
    strategies = collections.Counter()
    assets = collections.defaultdict(lambda: {"catalog_entries": 0, "fixed_occurrences": 0})
    for row in rows:
        plan = plan_for(row, basis)
        strategies[plan["strategy"]] += 1
        item = assets[row["asset"]]
        item["catalog_entries"] += 1
        item["fixed_occurrences"] += len(plan["paths"])
    return {
        "basis_version": basis.get("version"),
        "catalog_entries": len(rows),
        "strategies": dict(strategies),
        "fixed_occurrences": sum(item["fixed_occurrences"] for item in assets.values()),
        "assets": dict(sorted(assets.items())),
        "input_manifest_sha256": basis.get("manifest_sha256"),
    }
