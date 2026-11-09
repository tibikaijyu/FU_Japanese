# FU_Japanese release and distribution policy

- Public user-facing releases contain the PAK-only install ZIP listed in that release's `release-artifacts-<release-id>.json` `upload_allowlist`. Never upload files by wildcard from `dist/`; old files may remain there for history.
- Do not attach a raw MOD folder install ZIP or a source ZIP. The repository on Git is the source distribution.
- Build the game MOD as `mods/FU_Japanese.pak` with the official Starbound Windows `asset_packer.exe`, then run the matching official `asset_unpacker.exe` and verify relative paths, raw SHA-256 for every non-`_metadata` file, and type-sensitive metadata structure plus canonical JSON SHA-256.
- Missing official tools, failed packing, failed unpacking, or any verification mismatch must stop release creation. Never fall back to a folder package.
- If `optional/FU_Japanese_Font` is present, pack its exact allowlisted files into `optional/FU_Japanese_Font.pak` and verify it with the same tools. Do not include its raw folder in a release ZIP.
- Keep attribution and license text outside the PAKs at the explicit `LICENSES/FU_Japanese/` and `LICENSES/FU_Japanese_Font/` paths. Packaged notices must link to those paths.
- Each release ZIP must contain only PAK game payloads, install guidance, required notices, and license materials. The artifact manifest allowlist must name only the PAK install ZIP; checksums and verification reports are sidecars, not wildcard upload candidates.
- Use a new release identifier for each packaging-policy or payload change. Never delete or overwrite historical release artifacts.
- CI uses mocked packer/unpacker programs for regression tests. Create real distributable archives only on a machine with the official Starbound tools.
