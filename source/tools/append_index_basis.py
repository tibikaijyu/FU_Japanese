from __future__ import annotations
"""Capture exact append-field JSON pointers from the installed Starbound asset layers.

Only catalog-referenced assets are read from packages. Commercial asset bytes are
kept in memory and are never copied into the repository or the generated manifest.
"""
import argparse
import collections
import hashlib
import json
import os
import struct
from pathlib import Path

import pyjson5

from common import sanitize, unptr
from validate import apply_batches


class Cursor:
    def __init__(self, data):
        self.data = data
        self.pos = 0

    def varint(self):
        value = 0
        while True:
            if self.pos >= len(self.data):
                raise ValueError("Unexpected end of SBAsset6 index")
            byte = self.data[self.pos]
            self.pos += 1
            value = (value << 7) | (byte & 0x7f)
            if not byte & 0x80:
                return value

    def string(self):
        size = self.varint()
        end = self.pos + size
        if end > len(self.data):
            raise ValueError("SBAsset6 string exceeds index")
        value = self.data[self.pos:end].decode("utf-8")
        self.pos = end
        return value

    def skip_dynamic(self):
        if self.pos >= len(self.data):
            raise ValueError("Unexpected end of SBAsset6 metadata")
        kind = self.data[self.pos]
        self.pos += 1
        if kind == 1:
            return
        if kind == 2:
            self.pos += 8
        elif kind == 3:
            self.pos += 1
        elif kind == 4:
            self.varint()
        elif kind == 5:
            self.string()
        elif kind == 6:
            for _ in range(self.varint()):
                self.skip_dynamic()
        elif kind == 7:
            for _ in range(self.varint()):
                self.string()
                self.skip_dynamic()
        else:
            raise ValueError(f"Unsupported SBON metadata type: {kind}")
        if self.pos > len(self.data):
            raise ValueError("SBAsset6 metadata exceeds index")


class PakAssets:
    def __init__(self, path):
        self.path = Path(path)
        with self.path.open("rb") as stream:
            header = stream.read(16)
            if len(header) != 16 or header[:8] != b"SBAsset6":
                raise ValueError(f"Not an SBAsset6 package: {self.path}")
            index_offset = int.from_bytes(header[8:16], "big")
            stream.seek(index_offset)
            index = stream.read()
        if not index.startswith(b"INDEX"):
            raise ValueError(f"Missing SBAsset6 INDEX block: {self.path}")
        cursor = Cursor(index)
        cursor.pos = 5
        metadata_fields = cursor.varint()
        for _ in range(metadata_fields):
            cursor.string()
            cursor.skip_dynamic()
        self.entries = {}
        for _ in range(cursor.varint()):
            name = cursor.string()
            if cursor.pos + 16 > len(index):
                raise ValueError("Truncated SBAsset6 file entry")
            offset = int.from_bytes(index[cursor.pos:cursor.pos + 8], "big")
            length = int.from_bytes(index[cursor.pos + 8:cursor.pos + 16], "big")
            cursor.pos += 16
            self.entries[name.lstrip("/")] = (offset, length)
        self.stream = self.path.open("rb")

    def read(self, name):
        entry = self.entries.get(name)
        if entry is None:
            return None
        offset, length = entry
        self.stream.seek(offset)
        data = self.stream.read(length)
        if len(data) != length:
            raise ValueError(f"Truncated SBAsset6 asset {name} in {self.path}")
        return data

    def close(self):
        self.stream.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class AssetLayer:
    def __init__(self, name, path):
        self.name = name
        self.path = Path(path)
        self.pak = PakAssets(path) if self.path.is_file() else None

    def read(self, relative):
        if self.pak:
            return self.pak.read(relative)
        path = self.path / relative
        return path.read_bytes() if path.is_file() else None

    def close(self):
        if self.pak:
            self.pak.close()


def parse_asset(data):
    text = data.decode("utf-8-sig")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return pyjson5.loads(sanitize(text))


def pointer_parts(pointer):
    return [part.replace("~1", "/").replace("~0", "~")
            for part in pointer.split("/")[1:]]


def find_paths(document, parts, source, prefix=()):
    if not parts:
        return ["".join("/" + str(item).replace("~", "~0").replace("/", "~1")
                       for item in prefix)] if document == source else []
    key, rest = parts[0], parts[1:]
    paths = []
    if key == "-":
        if isinstance(document, list):
            for index, value in enumerate(document):
                paths.extend(find_paths(value, rest, source, prefix + (str(index),)))
    elif isinstance(document, dict) and key in document:
        paths.extend(find_paths(document[key], rest, source, prefix + (key,)))
    elif isinstance(document, list) and key.isdigit() and int(key) < len(document):
        paths.extend(find_paths(document[int(key)], rest, source, prefix + (key,)))
    return paths


def asset_hash(document):
    encoded = json.dumps(document, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def layer_argument(value):
    if "=" not in value:
        raise argparse.ArgumentTypeError("Layer must be NAME=PATH")
    name, path = value.split("=", 1)
    if not name or not path:
        raise argparse.ArgumentTypeError("Layer must be NAME=PATH")
    return name, Path(path)


def capture(base, layers, catalog_path, manifest_path, verify_only=False):
    base = Path(base)
    if not base.is_file():
        raise ValueError(f"Base package is missing or not a file: {base}")
    names = [name for name, _path in layers]
    if len(names) != len(set(names)) or "base" in names:
        raise ValueError("Layer names must be unique and must not be 'base'")
    for name, layer_path in layers:
        layer_path = Path(layer_path)
        if not layer_path.exists() or not (layer_path.is_file() or layer_path.is_dir()):
            raise ValueError(f"Layer path is missing or unsupported: {name}={layer_path}")
    rows = [json.loads(line) for line in Path(catalog_path).read_text(encoding="utf-8").splitlines()]
    assets = sorted({row["asset"] for row in rows if row["asset"] != "npcs/statuses.config"})
    sources = [AssetLayer("base", base), *[AssetLayer(name, path) for name, path in layers]]
    try:
        basis_assets = {}
        for asset in assets:
            document = None
            used = []
            for source in sources:
                raw = source.read(asset)
                patch_raw = source.read(asset + ".patch")
                if raw is not None:
                    document = parse_asset(raw)
                    used.append({"layer": source.name, "kind": "full", "sha256": hashlib.sha256(raw).hexdigest()})
                if patch_raw is not None:
                    if document is None:
                        raise ValueError(f"Patch without a lower-priority base: {source.name}:{asset}")
                    document = apply_batches(document, parse_asset(patch_raw))
                    used.append({"layer": source.name, "kind": "patch", "sha256": hashlib.sha256(patch_raw).hexdigest()})
            if document is None:
                raise ValueError(f"No base asset found: {asset}")
            paths = {}
            for row in rows:
                if row["asset"] != asset:
                    continue
                matches = find_paths(document, pointer_parts(row["path"]), row["source"])
                if not matches:
                    raise ValueError(f"Source text not present in installed basis: {asset}{row['path']} ({row['id']})")
                if len(matches) != len(set(matches)):
                    raise ValueError(f"Duplicate JSON pointer while resolving {row['id']}")
                paths[row["id"]] = matches
            basis_assets[asset] = {
                "effective_sha256": asset_hash(document),
                "layers": used,
                "paths": paths,
            }
        basis_assets["npcs/statuses.config"] = {
            "effective_sha256": "runtime-status-lookup",
            "layers": [],
            "paths": {},
        }
    finally:
        for source in sources:
            source.close()

    basis = {
        "version": 1,
        "base_source": "Starbound 1.4.4 assets/packed.pak",
        "layer_order": [name for name, _path in layers],
        "assets": basis_assets,
        "note": "Per-asset bytes are hashed; source paths and commercial/third-party contents are not stored.",
    }
    basis["manifest_sha256"] = hashlib.sha256(
        json.dumps(basis, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if verify_only:
        expected = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        expected.pop("manifest_sha256", None)
        actual = dict(basis)
        actual.pop("manifest_sha256", None)
        if actual != expected:
            raise ValueError("Installed append inputs differ from captured hashes/order/positions; recapture and re-audit.")
        for row in rows:
            if row.get("basis_sha256") != basis_assets[row["asset"]]["effective_sha256"]:
                raise ValueError("append_catalog basis hash is stale; rerun append_index_basis.py: " + row["asset"])
        print(json.dumps({"verified": True, "manifest_sha256": basis["manifest_sha256"],
                          "assets": len(assets), "catalog_rows": len(rows)}, indent=2))
        return

    updated_rows = []
    for row in rows:
        item = dict(row)
        item["basis_sha256"] = basis_assets[item["asset"]]["effective_sha256"]
        updated_rows.append(item)

    manifest_path = Path(manifest_path)
    catalog_path = Path(catalog_path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_tmp = manifest_path.with_suffix(manifest_path.suffix + ".tmp")
    catalog_tmp = catalog_path.with_suffix(catalog_path.suffix + ".tmp")
    manifest_tmp.write_text(json.dumps(basis, ensure_ascii=False, indent=2) + chr(10), encoding="utf-8", newline="\n")
    catalog_tmp.write_text("".join(json.dumps(row, ensure_ascii=False) + chr(10) for row in updated_rows), encoding="utf-8", newline="\n")
    os.replace(manifest_tmp, manifest_path)
    os.replace(catalog_tmp, catalog_path)
    counts = collections.Counter(len(paths) for info in basis_assets.values() for paths in info["paths"].values())
    print(json.dumps({
        "manifest": str(manifest_path),
        "manifest_sha256": basis["manifest_sha256"],
        "catalog_rows": len(updated_rows),
        "assets": len(assets),
        "resolved_occurrences": sum(count * amount for count, amount in counts.items()),
        "path_counts": dict(sorted(counts.items())),
    }, ensure_ascii=False, indent=2))


def load_inputs(inputs_path):
    config = json.loads(Path(inputs_path).read_text(encoding="utf-8"))
    return config["base_pak"], [(item["name"], Path(item["path"])) for item in config["layers"]]


def capture_inputs(project, inputs_path):
    base, layers = load_inputs(inputs_path)
    capture(base, layers, Path(project) / "source/append_catalog.jsonl",
            Path(project) / "source/append_index_basis.json")


def verify_inputs(project, inputs_path):
    base, layers = load_inputs(inputs_path)
    capture(base, layers, Path(project) / "source/append_catalog.jsonl",
            Path(project) / "source/append_index_basis.json", verify_only=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-pak")
    parser.add_argument("--layer", action="append", default=[], type=layer_argument,
                        help="Ordered asset source NAME=PAK_OR_DIRECTORY; repeat in game load order")
    parser.add_argument("--catalog", default="source/source/append_catalog.jsonl")
    parser.add_argument("--manifest", default="source/source/append_index_basis.json")
    parser.add_argument("--verify", action="store_true",
                        help="Verify current inputs against the captured manifest without writing files")
    parser.add_argument("--inputs-json", help="Verify a local JSON containing base_pak and ordered [{name,path}] layers")
    parser.add_argument("--capture-inputs-json", help="Capture the installed layers from a local JSON input config")
    parser.add_argument("--project", default=".", help="FU build project directory containing source/ and reports/")
    args = parser.parse_args()
    if args.capture_inputs_json:
        capture_inputs(args.project, args.capture_inputs_json)
    elif args.inputs_json:
        verify_inputs(args.project, args.inputs_json)
    elif args.base_pak:
        capture(args.base_pak, args.layer, args.catalog, args.manifest, verify_only=args.verify)
    else:
        parser.error("Provide --base-pak or --inputs-json")

if __name__ == "__main__":
    main()
