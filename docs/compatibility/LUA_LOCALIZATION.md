# Lua display localization

This part of FU Japanese localizes the text that Frackin' Universe constructs in
Lua. It is pinned to FU commit
`17868d86c9bb7bc00f92038fb78b48cebd1b41b8` (6.5.8). JSON asset patches, NPC
status append entries, the SBVN renderer, and `zb_textTyper.lua` are maintained
separately.

Data and report paths below are relative to the build project, `source/` at
the repository root. Shell commands are run from the repository root.

## Coverage

The inventory examines the 1,668 Lua files in this FU checkout. After excluding
the separately maintained renderers and nonruntime directories, 1,625 files
contain 34,242 string literals. An intentionally broad display candidate scan
finds 1,705 candidates; manual review also adds 16 short fragments missed by
that scan. The approved manifest contains **694 literal occurrences, 468 unique
source strings, and 126 FU scripts**. Every approved source string has an
individual Japanese translation in `source/lua_translations.json`.

The literal changes include research and quest controls, SAIL settings,
equipment descriptions, bee examination and genome displays, GPS instructions
and calendar labels, crafting routers, fuel and mech interfaces, storage,
colony facilities, pet interfaces, machine scan descriptions, wells, and
hardcoded creature names. Color codes, format substitutions, numerical values,
and intentional line breaks are retained.

There are additionally **44 explicit display-boundary replacements in 20
scripts**. These cover fuel type captions, station button captions, bee subtype
names, crew species names, sapling descriptions, pet names and cached moods,
condenser rarity captions, elemental display placeholders, weapon category
captions, and questline headings drawn above bitmap text. Their helpers contain
163 static display aliases. At build time the dictionary also inherits the
already validated monster mood translations from the main JSON catalog.
For the current catalog this yields 494 dictionary entries, including 331
monster mood fields.

The resulting overlay contains **130 Lua files**: 129 modified FU scripts and
one new helper. It also contains `fujp/lua_display.config`.

## Data and behavior preservation

Do not translate `beeData.config` subtype `name` values, mech fuel type values,
weapon category IDs, damage type IDs, station command payloads, or sapling
asset identifiers directly. FU uses these values for gameplay lookups. This
overlay translates only the copy passed to a display operation. Unknown
third-party values pass through unchanged, and user-assigned pet names are
retained.

`source/lua_manifest.json` records each selected literal's exact offsets and
the upstream file's SHA-256. The builder rejects a changed upstream file or
literal. It reconstructs the original source to verify that the literal pass
changed no unselected token or intervening code. It verifies the color tags,
Lua format placeholders, and newline counts. Both original and translated
scripts are parsed by Lua.

`source/lua_dynamic_hooks.json` independently pins the small display-boundary
edits by file hash, exact source snippet, and expected occurrence count. It
does not intercept global game APIs, change saved state, or replace callback
identifiers. The questline overlay requires the matching widgets in the main
`zb/questList/questList.config.patch`: `fuJapaneseBannerTitle`,
`fuJapaneseBannerCover`, `fuJapaneseQuestlineTitle`, and
`fuJapaneseQuestlineCover`. The last two are hidden initially and when returning
to the questline list.

## Build and integration

Run this after the main JSON translation build so that cached pet mood display
aliases use the current validated translations:

```sh
python source/tools/lua_localization.py build \
  --upstream upstream/FrackinUniverse --project source \
  --output source/lua-build

python source/compat/test_lua_localization.py \
  --upstream upstream/FrackinUniverse --mod source/lua-build
```

Copy the complete contents of `source/lua-build/` into the finished MOD directory,
preserving relative paths. Do not copy the inventory or translation manifests
into the game asset directory. This layer does not alter `_metadata`.

The `inventory` subcommand can regenerate the raw lexer inventory. The
`curate_lua_selection.py`, `curated_lua_translations.py`, and
`curate_lua_hooks.py` scripts reproduce the reviewed data for this specific FU
revision. They are not permission to automatically apply a heuristic
translation to a future FU revision. `lua_unique_sources.json` is a frozen
curation input whose ordering must be retained.

## Verification and limits

`reports/lua_validation.json` records all output hashes and the literal,
placeholder, syntax, and display-boundary checks. The current build has zero
untranslated selected literals and zero syntax errors.

`reports/lua_behavior_tests.json` records **20 executed cases and 773
assertions**. These load real upstream and localized Lua functions with small
Starbound API fixtures. They compare station command payloads, questline IDs,
quest completion state, navigation, fuel IDs and colors, tree asset paths,
bee genomes and stats, armor tags and stats, weapon IDs and numbers, food
aging, well item output and stored water, GPS numerical dates and times, pet
selection and portrait IDs, condenser rarity keys, and format argument types.
The tests also exercise unknown-value fallback and every bee subtype alias.

These tests execute Lua but do not launch Starbound or verify rendered font
sizes and screen layout. `runtime_tested: false` in the build report refers to
that missing in-game verification. Behavior tests and static coverage cannot
prove that every dynamically assembled string in every third-party mod is
translated.

`reports/lua_selection_audit.json` retains every excluded broad candidate and
its reason. The 1,027 exclusions consist of 648 internal/non-display contexts,
227 log/debug diagnostics, 59 command/state identifiers, 58 color literals,
33 internal keys/modes, and 2 logger/code selectors. A remaining English word
in Lua therefore does not by itself indicate visible untranslated text.
Future reports should identify the screen and source context before adding
another manifest entry.

The modified FU scripts retain their upstream authorship and the project's
existing FU license and attribution. The build reports identify the exact
original and modified files.
