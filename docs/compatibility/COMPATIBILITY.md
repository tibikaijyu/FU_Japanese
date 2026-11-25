# FU text typer UTF-8 compatibility

`zb/zb_textTyper.lua` is adapted from the FU 6.5.8 source at commit
`17868d86c9bb7bc00f92038fb78b48cebd1b41b8`.
The original author credited in the script is **zimberzimber**; the FU project
is maintained by sayter and contributors. The source and this adaptation are
distributed under **Creative Commons Attribution 4.0 International**.

Source: https://github.com/sayterdarkwynd/FrackinUniverse/blob/17868d86c9bb7bc00f92038fb78b48cebd1b41b8/zb/zb_textTyper.lua

License: https://creativecommons.org/licenses/by/4.0/

## Why this file is necessary

FU's custom S.A.I.L., BYOS ship selection, and space station text boxes use this
typewriter script. The original splits strings into individual bytes, then
replaces bytes above 127 and removes following bytes. Japanese UTF-8 text loses
characters through that code path.

The adaptation queues complete UTF-8 characters, including inserted player
names and data values. Color markup and existing pause, instant, data,
playername, function, and scramble commands retain their syntax. Scramble and
callback positions use the eventual output's byte length so a Japanese
character cannot be divided by an offset. This also corrects the old offset
count in cases with preceding color, instant, or pause commands. The script's
update, skip, sound, and other behavior remains unchanged.

The translation builder should copy **only** `zb/zb_textTyper.lua` from
`source/compat/` into the installed mod's matching asset path. Keep this note and
the FU license with the distribution's documentation. The test files belong
with the source/build tools.

## Verification

Run `python source/compat/test_compat.py /path/to/FrackinUniverse` from the repository
root. The test uses a Lua 5.3/5.4 shared library and stubs the game's widget,
sound, and player APIs. It compares normal ASCII rendering and control tags
against the upstream file, checks every intermediate Japanese output is valid
UTF-8, and exercises player names, data insertion, color tags, pauses, instant
text, callbacks, scrambling, and skipping.

This is a script-level check. Starbound was not launched in this environment.
The file replaces one FU Lua asset, so FU updates to that asset require a
fresh review. It does not modify inventory, quests, research unlocks, or save
data. Pandora's `.sbvn` renderer has a separate byte-slicing issue and is not
covered by this fix; `.sbvn` dialogue remains outside this release's scope.

## Text particles (2026-11-25)

`stats/typer_particle.lua` is a separate adaptation of the installed FU 6.5.8
writer, maintained by sayter and the Frackin' Universe contributors under
CC BY 4.0. Original source:
https://github.com/sayterdarkwynd/FrackinUniverse/blob/master/stats/typer_particle.lua
The exact reviewed input has SHA-256
`43a453cc4ad1e325c4cbcf57d07e28f392b5795d0f8d07a3e4932e91d64644ab`.

The original emits `string.sub(text, index, index)` as a text particle and
increments the byte index by one. Japanese insanity-effect translations then
produce invalid UTF-8 particles. The adaptation uses `utf8.offset` to emit a
complete character and advance to the next character's byte offset. ASCII
output, newline placement, particle properties, effect controllers, timing,
selection, and the original init/update chain are preserved.

The translation builder copies the adaptation from `source/compat/stats/` to
`mods/FU_Japanese/stats/`. Run `python source/compat/test_typer_particle.py`
for Lua 5.3/5.4 regression checks. Optional `--upstream`, `--corpus`, and
`--report` arguments verify the original failure and all effective translated
effect texts. The 2026-11-25 check covers 8 installed effects and 166 real texts,
plus 6 fixtures, on both Lua versions. Starbound rendering was not executed.
