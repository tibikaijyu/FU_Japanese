# FU Japanese machine-translation build dependency

This directory is a build workspace, not a Starbound mod folder. The model,
virtual environment and benchmark downloads must not be bundled in a release.

## Translation model and attribution

- Original translation model: FuguMT, `staka/fugumt-en-ja`, by S-Taka.
  <https://huggingface.co/staka/fugumt-en-ja>
  <https://github.com/s-taka/fugumt>
- CTranslate2 conversion: `jkawamoto/fugumt-en-ja-ct2`, by jkawamoto.
  <https://huggingface.co/jkawamoto/fugumt-en-ja-ct2>
- Pinned model revision: `5bdad25200fcf251bbf019a6ee613002df52869b`.
- Both model cards state CC BY-SA 4.0 for the model weights/conversion.
  Model weights are an external build dependency and are not redistributed
  with the generated localization mod.
- FuguMT is based on Marian-NMT. Runtime inference uses CTranslate2.
  <https://github.com/OpenNMT/CTranslate2>
- Source game text belongs to Frackin' Universe contributors. FU's upstream
  `LICENSE.txt` states CC BY 4.0; translated assets require upstream attribution.
  Keep model licensing distinct from the license of the original game text,
  translation files, and build code. Do not describe the model as Apache or MIT.

## Reproduce / resume

```sh
python -m venv venv
venv/bin/pip install -r requirements.txt
python download_model.py
venv/bin/python -u translate_catalog.py \
  --catalog /absolute/path/to/source/catalog.jsonl \
  --glossary /absolute/path/to/source/glossary.json
```

The input is UTF-8 JSONL with at least `source` and `category` fields. Other
fields such as IDs and JSON pointers are not required by this build step.
`machine_translations.json` is an exact English-source-to-Japanese mapping.
Apply manual review and glossary overrides after this step.

The SQLite cache is committed after each source batch. Re-running the same
command after a source catalog update translates only uncached strings.
`translation_progress.json` records current progress. The JSON mapping is
atomically replaced approximately every 960 source strings and once at exit.
Do not read the temporary `.tmp` file as a completed artifact.

## Structure protection

The engine preserves Starbound color directives, angle/brace placeholders,
FU `[(pause)...]` / `[(data)...]` / `[(scramble)...]` / `[(function)...]` /
`[(playername)]` / `[(instant)...]` commands, literal digits and signs/percent,
printf placeholders, newlines, private-use glyphs and Unicode symbols.
Known names can be represented as temporary reserved markers. All markers
must survive once each. Numeric, tag, printf and symbol order is checked.

If a marker is lost, the engine translates the surrounding text fragments
separately and records `fallback_split`. If a final structural check still
fails, the original English is retained and flagged. English number words
that the model renders with digits are changed to Japanese kanji digits;
literal source digits remain unchanged.

`machine_review_flags.jsonl` lists flagged strings. It must be reviewed;
passing structural validation does not prove semantic correctness.

## Quality and limitations

This is machine translation, not human-reviewed complete localization.
FuguMT handles basic English well but mistranslates invented game terms,
idioms, dialogue jokes and some long clauses. For example, `beam down` can
be translated as firing or launching. Sentence splitting reduces whole-
sentence omissions but cannot guarantee complete semantic coverage.
Some proper names and unknown terms remain in English. Color-tag boundaries
can still lead to awkward Japanese word order even when all tags are valid.
The pipeline does not test rendering, clipping, gameplay, or game loading.

A benchmark on 192 unique research strings used 6.34 seconds on the available
8-thread CPU setup before the final custom-command and glossary additions;
real completion times depend on text length, CPU sharing and fallback rate.

## Non-selected routes

The public Google translation endpoint returned HTTP 429 on the initial
request and was not used or retried. No private credentials, paid translation
API, or external account was used. An unrelated third-party model claiming
to be OPUS English-to-Japanese produced unrelated output and was rejected;
none of its output is in the selected versioned cache.
