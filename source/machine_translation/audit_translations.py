"""Validate one complete machine-output snapshot against the current catalog."""
from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path
import re

from translate_catalog import VERSION, validation_errors, JAPANESE_RE

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--catalog',type=Path,required=True)
parser.add_argument('--translations',type=Path,default=ROOT/'machine_translations.json')
parser.add_argument('--manual-dir',type=Path)
args=parser.parse_args()
rows=[json.loads(line) for line in args.catalog.read_text(encoding='utf-8').splitlines()]
sources=list(dict.fromkeys(row['source'] for row in rows))
mapping=json.loads(args.translations.read_text(encoding='utf-8'))
missing=[];failures=[]
for source in sources:
    if source not in mapping:
        missing.append(source);continue
    errors=validation_errors(source,mapping[source])
    if errors:failures.append({'source':source,'translation':mapping[source],'errors':errors})
present=[s for s in sources if s in mapping]
manual={}
if args.manual_dir:
    for path in sorted(args.manual_dir.glob('manual_*.json')):
        manual.update(json.loads(path.read_text(encoding='utf-8')))
manual_only=[s for s in missing if s in manual]
unresolved=[s for s in missing if s not in manual]
report={
    'engine_cache_version':VERSION,
    'catalog_entries':len(rows),
    'unique_source_strings':len(sources),
    'unique_translated_strings':len(present),
    'missing_strings':len(missing),
    'manual_only_strings':len(manual_only),
    'manual_only_sources':manual_only,
    'unresolved_sources':len(unresolved),
    'scope':'Raw machine output. Missing machine entries supplied by manual dictionaries are listed separately; final selected translation coverage is in final_residual_decisions.json.',
    'structural_failure_strings':len(failures),
    'failure_types':dict(Counter(reason for f in failures for reason in f['errors'])),
    'changed_strings':sum(mapping[s]!=s for s in present),
    'unchanged_strings':sum(mapping[s]==s for s in present),
    'strings_containing_japanese':sum(bool(JAPANESE_RE.search(mapping[s])) for s in present),
    'output_sha256':hashlib.sha256(args.translations.read_bytes()).hexdigest(),
    'translator_script_sha256':hashlib.sha256((ROOT/'translate_catalog.py').read_bytes()).hexdigest(),
    'semantic_verification':'Machine translations have not all been human-reviewed. Structural checks do not prove meaning or completeness.',
    'game_runtime_verification':False,
}
(ROOT/'translation_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
(ROOT/'structural_failures.jsonl').write_text(''.join(json.dumps(f,ensure_ascii=False)+'\n' for f in failures),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
if unresolved or failures:raise SystemExit(1)
