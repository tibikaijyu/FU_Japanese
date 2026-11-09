#!/usr/bin/env python3
"""Package the validated MOD as a verified, PAK-only install ZIP (stdlib only)."""
import argparse
import hashlib
import json
import posixpath
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
RELEASE_ID = "0.2.4-public.2"
ZIP_TIME = (2026, 11, 7, 0, 0, 0)
INSTALL_DOC_PATHS = {
    "docs/README_JA.md": "README_JA.md",
    "docs/INSTALL_JA.txt": "INSTALL_JA.txt",
    "docs/PAK_DISTRIBUTION.md": "PAK_DISTRIBUTION.md",
}
INSTALL_DOCS = {
    *INSTALL_DOC_PATHS, "CHANGELOG.md", "LICENSE.md",
    "THIRD_PARTY_NOTICES.md", "LICENSES/MIT-tools.txt",
    "docs/verification/2026-11-07-user-report.md",
    "source/machine_translation/README.md",
    "source/machine_translation/model_provenance.json",
}
REQUIRED_SOURCE = {
    "source/machine_translation/model_provenance.json",
    "source/machine_translation/pre_review_semantic_candidates.jsonl",
    "source/source/catalog.jsonl", "source/compat/followup_022/fujp/species_display.lua",
}
FONT_PREFIX = "optional/FU_Japanese_Font/"
FONT_FILE_ALLOWLIST = {
    "_metadata", "hobo.ttf", "ATTRIBUTION.txt",
    "LICENSE-MPLUS-EN.txt", "LICENSE-MPLUS-JA.txt",
}
LICENSE_COPY_PATHS = {
    "mods/FU_Japanese/LICENSE-FU-CC-BY-4.0.txt": "LICENSES/FU_Japanese/LICENSE-FU-CC-BY-4.0.txt",
    "mods/FU_Japanese/ATTRIBUTION.txt": "LICENSES/FU_Japanese/ATTRIBUTION.txt",
    "optional/FU_Japanese_Font/ATTRIBUTION.txt": "LICENSES/FU_Japanese_Font/ATTRIBUTION.txt",
    "optional/FU_Japanese_Font/LICENSE-MPLUS-EN.txt": "LICENSES/FU_Japanese_Font/LICENSE-MPLUS-EN.txt",
    "optional/FU_Japanese_Font/LICENSE-MPLUS-JA.txt": "LICENSES/FU_Japanese_Font/LICENSE-MPLUS-JA.txt",
}
LICENSE_LINK_REWRITES = {
    "mods/FU_Japanese/LICENSE-FU-CC-BY-4.0.txt": LICENSE_COPY_PATHS["mods/FU_Japanese/LICENSE-FU-CC-BY-4.0.txt"],
    "mods/FU_Japanese/ATTRIBUTION.txt": LICENSE_COPY_PATHS["mods/FU_Japanese/ATTRIBUTION.txt"],
    "optional/FU_Japanese_Font/ATTRIBUTION.txt": LICENSE_COPY_PATHS["optional/FU_Japanese_Font/ATTRIBUTION.txt"],
    "optional/FU_Japanese_Font/LICENSE-MPLUS-EN.txt": LICENSE_COPY_PATHS["optional/FU_Japanese_Font/LICENSE-MPLUS-EN.txt"],
    "optional/FU_Japanese_Font/LICENSE-MPLUS-JA.txt": LICENSE_COPY_PATHS["optional/FU_Japanese_Font/LICENSE-MPLUS-JA.txt"],
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def safe_public_path(name):
    path = PurePosixPath(name)
    if (not name or path.is_absolute() or ".." in path.parts or
            any(c in name for c in "\\:\r\n") or path.as_posix() != name):
        return False
    forbidden = {".git", ".local", ".venv", "venv", "__pycache__", "fugumt-model"}
    if forbidden.intersection(path.parts):
        return False
    return not (name.startswith(("docs/development/", "source/reports/scope/")) or
                name.endswith((".log", ".zip", ".pyc")))

def load_public_files(root):
    """The reviewed checksum manifest is the explicit source-package allowlist."""
    files = {}
    for line in (root / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        match = re.fullmatch(r"([0-9a-f]{64})  (.+)", line)
        if not match or not safe_public_path(match[2]):
            raise ValueError("Unsafe or malformed public checksum entry")
        expected, name = match.groups()
        if name in files or name == "SHA256SUMS.txt":
            raise ValueError("Duplicate or self-referential checksum entry")
        file = root / name
        if file.is_symlink() or not file.resolve().is_relative_to(root.resolve()):
            raise ValueError("Symlinks are not supported: " + name)
        data = file.read_bytes()
        if sha(data) != expected:
            raise ValueError("Public checksum mismatch: " + name)
        files[name] = data
    return files

def validate_release(files):
    for name in REQUIRED_SOURCE | INSTALL_DOCS:
        if name not in files:
            raise ValueError("Required source/notice missing: " + name)
    report = json.loads(files["source/reports/validation.json"])
    metadata = json.loads(files["mods/FU_Japanese/_metadata"])
    if not report["passed"] or metadata["version"] != report["mod_version"]:
        raise ValueError("Release validation does not match the MOD version")
    prefix = "mods/FU_Japanese/"
    actual = {name[len(prefix):]: sha(data) for name, data in files.items() if name.startswith(prefix)}
    if actual != json.loads(files["source/reports/mod_sha256.json"]):
        raise ValueError("Game files differ from the validated MOD")
    coverage = json.loads(files["source/reports/coverage.json"])
    if sha(files["source/source/catalog.jsonl"]) != coverage["catalog_sha256"]:
        raise ValueError("Coverage predates the catalog")
    if (coverage["rejected_entries"] or coverage["append_coverage"]["rejected"] or
            coverage["retained_reasons"].get("not_translated", 0)):
        raise ValueError("Unresolved translation validation failures")
    audit = json.loads(files["source/reports/final_residual_decisions.json"])
    for key in ("missing_translation_fields", "unclassified_whole_fields", "structural_errors",
                "mixed_english_clause_unique_sources"):
        if audit[key]:
            raise ValueError("Completeness audit failed: " + key)
    for name, expected in audit["input_sha256"].items():
        if sha(files["source/source/" + name]) != expected:
            raise ValueError("Completeness audit predates: " + name)
    from release_evidence import validate_release_evidence
    validate_release_evidence(files, expected_version=metadata["version"].split("-fu")[0])
    return metadata["version"]

def install_files(files):
    return {INSTALL_DOC_PATHS.get(name, name): data for name, data in files.items()
            if name.startswith(("mods/FU_Japanese/", "optional/FU_Japanese_Font/")) or name in INSTALL_DOCS}

def write_zip(destination, prefix, files):
    if destination.is_symlink():
        raise ValueError("Refusing to replace a symlink")
    payload = dict(files)
    payload["SHA256SUMS.txt"] = "".join(
        f"{sha(data)}  {name}\n" for name, data in sorted(files.items())
    ).encode("utf-8")
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(payload.items()):
            if not safe_public_path(name):
                raise ValueError("Invalid archive path: " + name)
            info = zipfile.ZipInfo(prefix + "/" + name, ZIP_TIME)
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    with zipfile.ZipFile(destination) as archive:
        expected_names = {prefix + "/" + name for name in payload}
        if set(archive.namelist()) != expected_names or len(archive.infolist()) != len(expected_names):
            raise ValueError("ZIP file list mismatch")
        # Reading every member verifies CRC; compare the exact archived payload too.
        for name, data in payload.items():
            if archive.read(prefix + "/" + name) != data:
                raise ValueError("ZIP content mismatch: " + name)
    return {"file": destination.name, "files": len(payload), "bytes": destination.stat().st_size,
            "sha256": sha(destination.read_bytes()), "crc_and_content_verified": True}

def canonical_json(data):
    """Return type-sensitive canonical JSON bytes for metadata comparison."""
    value = json.loads(data.decode("utf-8"))
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")

def tree_inventory(directory):
    """Inventory regular files by Starbound-relative path and raw SHA-256."""
    directory = Path(directory)
    result = {}
    for item in directory.rglob("*"):
        if item.is_symlink():
            raise ValueError("Symlinks are not supported in PAK input: " + str(item))
        if item.is_file():
            name = item.relative_to(directory).as_posix()
            result[name] = {"bytes": item.stat().st_size, "sha256": sha(item.read_bytes())}
        elif not item.is_dir():
            raise ValueError("Unsupported PAK input entry: " + str(item))
    return result

def verify_pak_tree(source_dir, unpacked_dir):
    """Verify all paths and bytes; allow only JSON serialization changes to _metadata."""
    source, unpacked = tree_inventory(source_dir), tree_inventory(unpacked_dir)
    if set(source) != set(unpacked):
        missing, added = sorted(set(source) - set(unpacked)), sorted(set(unpacked) - set(source))
        raise ValueError(f"PAK path mismatch (missing={missing[:5]}, added={added[:5]})")
    metadata_name = "_metadata"
    if metadata_name not in source:
        raise ValueError("PAK input is missing _metadata")
    for name in sorted(source):
        if name != metadata_name and source[name] != unpacked[name]:
            raise ValueError("PAK content SHA-256 mismatch: " + name)
    source_metadata = (Path(source_dir) / metadata_name).read_bytes()
    unpacked_metadata = (Path(unpacked_dir) / metadata_name).read_bytes()
    source_canonical, unpacked_canonical = canonical_json(source_metadata), canonical_json(unpacked_metadata)
    if source_canonical != unpacked_canonical:
        raise ValueError("PAK _metadata JSON structure/value/type changed")
    return {
        "relative_paths_match": True,
        "file_count": len(source),
        "non_metadata_raw_sha256_match": True,
        "metadata_json_deep_equal": True,
        "metadata_canonical_sha256": sha(source_canonical),
        "metadata_raw_sha256": {"pak_input": sha(source_metadata), "unpacked": sha(unpacked_metadata),
                                "equal": source_metadata == unpacked_metadata},
        "all_raw_bytes_equal": all(source[name] == unpacked[name] for name in source),
    }

def _build_verified_pak(files, source_prefix, packed_folder, tools_dir, work_dir):
    packed_files = {name[len(source_prefix):]: data for name, data in files.items()
                    if name.startswith(source_prefix)}
    if not packed_files or "_metadata" not in packed_files:
        raise ValueError("Validated public files are missing PAK input: " + source_prefix)
    if any(not safe_public_path(name) for name in packed_files):
        raise ValueError("Unsafe relative path in PAK input: " + source_prefix)
    tools_dir = Path(tools_dir).resolve()
    packer, unpacker = tools_dir / "asset_packer.exe", tools_dir / "asset_unpacker.exe"
    for tool in (packer, unpacker):
        if not tool.is_file():
            raise ValueError("Official Starbound packing tool is missing: " + str(tool))
    with tempfile.TemporaryDirectory(prefix=".pak-verify-", dir=work_dir) as temporary:
        temporary = Path(temporary)
        source = temporary / "input" / packed_folder
        source.mkdir(parents=True)
        for name, data in packed_files.items():
            destination = source.joinpath(*PurePosixPath(name).parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
        pak = temporary / (packed_folder + ".pak")
        unpacked = temporary / "unpacked"
        subprocess.run([str(packer), str(source), str(pak)], check=True, capture_output=True, text=True)
        if not pak.is_file():
            raise ValueError("Official asset_packer did not produce a PAK")
        subprocess.run([str(unpacker), str(pak), str(unpacked)], check=True, capture_output=True, text=True)
        verification = verify_pak_tree(source, unpacked)
        return pak.read_bytes(), verification

def build_verified_pak(files, tools_dir, work_dir):
    """Pack only the validated mods/FU_Japanese allowlist and verify its round trip."""
    return _build_verified_pak(files, "mods/FU_Japanese/", "FU_Japanese", tools_dir, work_dir)

def build_verified_font_pak(files, tools_dir, work_dir):
    """Pack the exact optional font allowlist as its own verified Starbound mod."""
    font_files = {name[len(FONT_PREFIX):] for name in files if name.startswith(FONT_PREFIX)}
    if not font_files:
        return None, None
    if font_files != FONT_FILE_ALLOWLIST:
        raise ValueError("Optional font file set differs from the explicit allowlist")
    return _build_verified_pak(files, FONT_PREFIX, "FU_Japanese_Font", tools_dir, work_dir)

def _relocate_license_links(files):
    """Copy notices' referenced license text outside the game PAKs and repair archive links."""
    selected = install_files(files)
    for name in tuple(selected):
        if name.startswith(("mods/FU_Japanese/", FONT_PREFIX)):
            del selected[name]
    for source, destination in LICENSE_COPY_PATHS.items():
        if source in files:
            selected[destination] = files[source]
    for document in ("LICENSE.md", "THIRD_PARTY_NOTICES.md"):
        if document not in selected:
            continue
        content = selected[document]
        for source, destination in LICENSE_LINK_REWRITES.items():
            content = content.replace(source.encode("utf-8"), destination.encode("utf-8"))
        selected[document] = content
    for document in ("LICENSE.md", "THIRD_PARTY_NOTICES.md"):
        if document not in selected:
            continue
        for target in re.findall(rb"\]\(([^)]+)\)", selected[document]):
            link = target.decode("utf-8")
            if link.startswith(("http://", "https://", "mailto:")) or link.startswith("#"):
                continue
            local_path = posixpath.normpath(link.split("#", 1)[0])
            if local_path not in selected:
                raise ValueError(f"Broken packaged license link in {document}: {link}")
    return selected

def pak_install_files(files, pak_data, font_pak_data=None):
    """Create a PAK-only install payload, including separate PAKs for each game mod."""
    font_files = {name[len(FONT_PREFIX):] for name in files if name.startswith(FONT_PREFIX)}
    if font_files and font_pak_data is None:
        raise ValueError("Optional font assets require their verified PAK")
    if font_pak_data is not None and font_files != FONT_FILE_ALLOWLIST:
        raise ValueError("Optional font PAK does not match the explicit file allowlist")
    selected = _relocate_license_links(files)
    selected["mods/FU_Japanese.pak"] = pak_data
    if font_pak_data is not None:
        selected["optional/FU_Japanese_Font.pak"] = font_pak_data
    return selected

def package(root, output_dir, release_id=RELEASE_ID, pak_tools_dir=None, pak_release_id=None):
    root, output_dir = Path(root).resolve(), Path(output_dir).resolve()
    if pak_tools_dir is None:
        raise ValueError("Official Starbound --pak-tools-dir is required; folder fallback is disabled")
    if not re.fullmatch(r"\d+\.\d+\.\d+-public\.\d+", release_id):
        raise ValueError("Use a distinct public repack identifier, e.g. 0.2.3-public.1")
    if output_dir == root or not output_dir.is_relative_to(root):
        raise ValueError("Output must be a separate directory inside the repository")
    files = load_public_files(root)
    version = validate_release(files)
    if version.split("-fu")[0] != release_id.split("-public.")[0]:
        raise ValueError("Repack identifier does not match the MOD version")
    pak_release_id = pak_release_id or (release_id + "-pak.1")
    expected_pak_base = release_id + "-pak."
    if not re.fullmatch(re.escape(expected_pak_base) + r"\d+", pak_release_id):
        raise ValueError("PAK release identifier must be distinct and based on this release, e.g. " + expected_pak_base + "1")
    pak_prefix = "FU_Japanese_" + pak_release_id
    archive_path = output_dir / f"{pak_prefix}-install.zip"
    verification_path = output_dir / f"{pak_prefix}-verification.json"
    checksums = output_dir / f"SHA256SUMS-{release_id}.txt"
    manifest_path = output_dir / f"release-artifacts-{release_id}.json"
    collisions = [path.name for path in (archive_path, verification_path, checksums, manifest_path) if path.exists()]
    if collisions:
        raise FileExistsError("Release outputs already exist; choose a new release ID: " + ", ".join(collisions))
    output_dir.mkdir(parents=True, exist_ok=True)

    # All official-tool operations finish before any archive is written.
    main_pak, main_verification = build_verified_pak(files, pak_tools_dir, output_dir)
    font_pak, font_verification = build_verified_font_pak(files, pak_tools_dir, output_dir)
    pak_report = {
        "release_id": pak_release_id,
        "mod_version": version,
        "packer": str((Path(pak_tools_dir) / "asset_packer.exe").resolve()),
        "unpacker": str((Path(pak_tools_dir) / "asset_unpacker.exe").resolve()),
        "packages": [{"path": "mods/FU_Japanese.pak", "pak_sha256": sha(main_pak),
                      "pak_bytes": len(main_pak), "verification": main_verification}],
    }
    if font_pak is not None:
        pak_report["packages"].append({
            "path": "optional/FU_Japanese_Font.pak", "pak_sha256": sha(font_pak),
            "pak_bytes": len(font_pak), "verification": font_verification,
        })
    pak_payload = pak_install_files(files, main_pak, font_pak)
    artifact = write_zip(archive_path, pak_prefix, pak_payload)
    artifacts = [artifact]
    verification_path.write_text(json.dumps(pak_report, indent=2) + "\n", encoding="utf-8", newline="\n")
    checksums.write_bytes("".join(f"{row['sha256']}  {row['file']}\n" for row in artifacts).encode())
    report = {"release_id": release_id, "mod_version": version, "prerelease": True,
              "native_game_executed": False, "artifacts": artifacts,
              "upload_allowlist": [archive_path.name],
              "pak_distribution": pak_report,
              "checksum_file": checksums.name,
              "verification_report": verification_path.name,
              "reproducibility": "Fixed names, order, timestamps, permissions and compression level. ZIP byte identity is tested with the same Python/zlib runtime."}
    manifest_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(report, indent=2))
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    parser.add_argument("--release-id", default=RELEASE_ID)
    parser.add_argument("--pak-tools-dir", type=Path, required=True,
                        help="Win32 directory containing the official asset_packer.exe and asset_unpacker.exe")
    parser.add_argument("--pak-release-id", help="Distinct PAK distribution identifier; defaults to <release-id>-pak.1")
    args = parser.parse_args()
    package(args.root, args.output_dir, args.release_id, args.pak_tools_dir, args.pak_release_id)
