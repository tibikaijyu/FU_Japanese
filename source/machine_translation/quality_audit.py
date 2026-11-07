"""Read-only heuristic review report; flags are not proof of mistranslation."""
from collections import Counter
import argparse
import json
from pathlib import Path
import re
import sqlite3

from translate_catalog import VERSION, TAG_RE

ROOT=Path(__file__).resolve().parent
parser=argparse.ArgumentParser()
parser.add_argument('--catalog',type=Path)
parser.add_argument('--manual-dir',type=Path)
args=parser.parse_args()
db=sqlite3.connect('file:'+str(ROOT/'translation_cache.sqlite3')+'?mode=ro',uri=True)


def clean(text):
    return re.sub(r'\s+',' ',TAG_RE.sub('',text)).strip()


suspect=[]
for source,target,flags in db.execute('SELECT source,target,flags FROM segments WHERE version=?',(VERSION,)):
    s=clean(source);t=clean(target)
    ratio=len(t)/max(1,len(s))
    reasons=[]
    if len(s)>=160 and len(re.findall(r'[A-Za-z]+',s))>=25 and ratio<0.32:
        reasons.append('long_sentence_short_translation')
    if len(s)>=80 and len(re.findall(r'[A-Za-z]',t))>=0.65*max(1,len(t)):
        reasons.append('mostly_english')
    if reasons:
        suspect.append({'source_segment':source,'machine_translation':target,'source_chars':len(s),
                        'target_chars':len(t),'length_ratio':round(ratio,3),'reasons':reasons,'engine_flags':json.loads(flags)})
suspect.sort(key=lambda d:(0 if 'long_sentence_short_translation' in d['reasons'] else 1,d['length_ratio']))
out=ROOT/'semantic_review_candidates.jsonl'
out.write_text(''.join(json.dumps(d,ensure_ascii=False)+'\n' for d in suspect),encoding='utf-8')
print(json.dumps({'review_candidates':len(suspect),'reasons':dict(Counter(r for s in suspect for r in s['reasons'])),'output':str(out)},ensure_ascii=False))
if args.catalog:
    manual={}
    if args.manual_dir:
        for path in args.manual_dir.glob('manual_*.json'):
            manual.update(json.loads(path.read_text(encoding='utf-8')))
    mapping=json.loads((ROOT/'machine_translations.json').read_text(encoding='utf-8'))
    rows=[json.loads(line) for line in args.catalog.read_text(encoding='utf-8').splitlines()]
    unique={}
    for row in rows:unique.setdefault(row['source'],row)
    remaining=[];covered=0
    for source,row in unique.items():
        matching=[item for item in suspect if item['source_segment'] in source]
        if not matching:continue
        if source in manual:
            covered+=1;continue
        remaining.append({'source':source,'machine_translation':mapping.get(source),
            'category':row['category'],'asset':row['asset'],'path':row['path'],
            'suspect_segments':matching})
    order={'research':0,'radio':1,'quests':2,'interface':3,'items':4,'dialogue':5,'codex':6}
    remaining.sort(key=lambda d:(order.get(d['category'],7),min(x['length_ratio'] for x in d['suspect_segments'])))
    full=ROOT/'remaining_semantic_sources.jsonl'
    full.write_text(''.join(json.dumps(d,ensure_ascii=False)+'\n' for d in remaining),encoding='utf-8')
    print(json.dumps({'full_sources_remaining':len(remaining),'sources_covered_by_manual':covered,
        'categories':dict(Counter(d['category'] for d in remaining)),'output':str(full)},ensure_ascii=False))
    for item in remaining[:10]:
        print(json.dumps({'category':item['category'],'asset':item['asset'],'source_preview':item['source'][:180]},ensure_ascii=False))
else:
    for record in suspect[:8]:print(json.dumps(record,ensure_ascii=False))
