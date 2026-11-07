"""Offline, resumable FU English-to-Japanese translation with token validation.

The model is a separate build dependency; it is never copied into the mod.
Raw machine output and fallback flags remain reviewable in SQLite and JSONL.
"""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import time
import unicodedata

import ctranslate2
import pysbd
import sentencepiece as spm

ROOT = Path(__file__).resolve().parent
VERSION = 'fugumt-5bdad252-beam2-protected-v3'
PRIORITY = {'research':0, 'radio':1, 'quests':2, 'interface':3, 'status':4,
            'items':5, 'dialogue':6, 'codex':7}
GLOSSARY = {
    'Personal Tricorder': '個人用トライコーダー',
    'Matter Manipulator': 'マターマニピュレーター',
    'Science Outpost': '科学前哨基地',
    'Matter Assembler': '物質組立機',
    'Machining Table': '加工作業台',
    'Extraction Lab': '抽出ラボ',
    'Armor and Weapons': '武器と防具',
    'Mining Laser': '採掘レーザー',
    'Tricorder': 'トライコーダー',
    'Research': '研究',
    'Chemistry': '化学',
    'Agriculture': '農業',
    'Engineering': '工学',
    'Craftsmanship': '工芸',
    'Madness': '狂気',
    'Tier': 'ティア',
}
GENERIC_TERMS={'research','chemistry','agriculture','engineering','craftsmanship','madness'}
TERM_RE = re.compile(r'(?<![A-Za-z])(?:' + '|'.join(
    re.escape(k) for k in sorted(GLOSSARY, key=len, reverse=True)) + r')(?![A-Za-z])', re.I)
TERM_LOOKUP = {k.casefold(): v for k,v in GLOSSARY.items()}
CUSTOM_PATTERN=r'%%[^\r\n]*?%%|\[\((?:pause|data|scramble|function|playername|instant)\)[^\]\r\n]*\]'
TAG_RE = re.compile(CUSTOM_PATTERN+r'|\^[^;\r\n]*;|<[^<>\r\n]+>|\{[^{}\r\n]+\}')
NUMBER_RE = re.compile(r'[+-]?(?:\d+(?:[.,]\d+)*|\.\d+)(?:%)?')
FORMAT_RE = re.compile(r'%(?:\d+\$)?[-+#0]*(?:\d+|\*)?(?:\.(?:\d+|\*))?[sdifgouxXeEcrqaA%]')
BASE_RE = re.compile(
    CUSTOM_PATTERN+r'|https?://[^\s<>]+'  # URLs remain byte-for-byte strings.
    r'|\^[^;\r\n]*;'
    r'|<[^<>\r\n]+>'
    r'|\{[^{}\r\n]+\}'
    r'|\\[nrt]'
    r'|[+-](?=(?:[ \t]|\^[^;\r\n]*;)*(?:\d|[<{]))'
    r'|%(?:\d+\$)?[-+#0]*(?:\d+|\*)?(?:\.(?:\d+|\*))?[sdifgouxXeEcrqaA%]'
    r'|[+-]?(?:\d+(?:[.,]\d+)*|\.\d+)(?:%)?'
    r'|%'
)
MARKER_RE = re.compile(r'__PH\d+__')
JAPANESE_RE = re.compile(r'[\u3040-\u30ff\u3400-\u9fff]')
ENGLISH_RE = re.compile(r'[A-Za-z]')
SENTENCER = pysbd.Segmenter(language='en', clean=False)
NUMBER_WORD_RE=re.compile(r'\b(?:zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|half|dozen|hundred|thousand|million)\b',re.I)
DIGIT_KANJI=str.maketrans('0123456789','〇一二三四五六七八九')


def clean_model_output(source, output):
    # Normalize harmless underscore duplication around the reserved marker only.
    output=re.sub(r'_{1,5}PH\s*(\d+)_{1,5}',lambda m:'__PH'+m.group(1)+'__',output)
    if NUMBER_WORD_RE.search(source):
        # Literal source digits are masked. Digits outside markers can legitimately
        # come from English number words ("second" -> "2つ目"); use kanji there.
        parts=MARKER_RE.split(output)
        marks=MARKER_RE.findall(output)
        output=''.join(p.translate(DIGIT_KANJI)+(marks[i] if i<len(marks) else '') for i,p in enumerate(parts))
    if re.search(r'\bresearch\b',source,re.I):
        output=output.replace('調査','研究').replace('リサーチ','研究')
    return output


def is_symbol(char):
    return unicodedata.category(char) == 'Co' or (ord(char)>127 and unicodedata.category(char).startswith('S'))


def symbols(text):
    return [c for c in text if is_symbol(c)]


def validation_errors(source, target):
    errors=[]
    if TAG_RE.findall(source) != TAG_RE.findall(target): errors.append('tag_sequence')
    # Ignore numeric characters inside markup/URLs: the complete token is already protected.
    clean_source=TAG_RE.sub('', source)
    clean_target=TAG_RE.sub('', target)
    if NUMBER_RE.findall(clean_source) != NUMBER_RE.findall(clean_target):
        errors.append('numbers')
    if source.count('%') != target.count('%'): errors.append('percent')
    if FORMAT_RE.findall(source) != FORMAT_RE.findall(target): errors.append('format')
    if symbols(source) != symbols(target): errors.append('symbols')
    if re.findall(r'\r\n|\r|\n', source) != re.findall(r'\r\n|\r|\n', target): errors.append('newlines')
    if '\u2047' in target and '\u2047' not in source: errors.append('unknown_glyph')
    return errors


def protected_spans(text):
    candidates=[(m.start(),m.end(),m.group(),False) for m in BASE_RE.finditer(text)]
    candidates += [(m.start(),m.end(),TERM_LOOKUP[m.group().casefold()],True) for m in TERM_RE.finditer(text)
                   if m.group().casefold() not in GENERIC_TERMS]
    candidates += [(i,i+1,c,False) for i,c in enumerate(text) if is_symbol(c)]
    candidates.sort(key=lambda x:(x[0], -(x[1]-x[0])))
    accepted=[]
    end=-1
    for candidate in candidates:
        if candidate[0]>=end:
            accepted.append(candidate)
            end=candidate[1]
    # Combine adjacent protected atoms: colored glossary terms can be one marker.
    combined=[]
    for start,end,value,term in accepted:
        if combined and start==combined[-1][1]:
            a,b,v,t=combined[-1]
            combined[-1]=(a,end,v+value,t or term)
        else:
            combined.append((start,end,value,term))
    return combined


def protect(text):
    spans=protected_spans(text)
    pieces=[]; values=[]; cursor=0
    for start,end,value,_ in spans:
        pieces.append(text[cursor:start])
        pieces.append(f' __PH{len(values)}__ ')
        values.append(value)
        cursor=end
    pieces.append(text[cursor:])
    return re.sub(r'[ \t]+',' ',''.join(pieces)).strip(),values


def unprotect(text,values):
    expected=[f'__PH{i}__' for i in range(len(values))]
    if Counter(MARKER_RE.findall(text)) != Counter(expected):
        return None
    for i,value in enumerate(values):
        text=text.replace(f'__PH{i}__',value)
    # Spacing added around markers is not meaningful in Japanese UI text.
    text=re.sub(r'(?<=[\u3040-\u30ff\u3400-\u9fff]) +(?=[\u3040-\u30ff\u3400-\u9fff])','',text)
    return text.strip()


def chunks(text, max_chars=550):
    """Preserve every newline and all sentence-boundary whitespace."""
    pieces=[]
    for line in re.split(r'(\r\n|\r|\n)',text):
        if not line: continue
        if line in ('\r','\n','\r\n'):
            pieces.append(('literal',line));continue
        sentences=SENTENCER.segment(line)
        if ''.join(sentences)!=line: sentences=[line]
        for sentence in sentences:
            # Long single sentences are chunked at whitespace, never truncated.
            while len(sentence)>max_chars:
                cut=sentence.rfind(' ',0,max_chars)
                if cut<100: break
                pieces.append(('text',sentence[:cut+1]))
                sentence=sentence[cut+1:]
            if sentence: pieces.append(('text',sentence))
    return pieces


@dataclass
class Work:
    source: str
    masked: str
    values: list[str]


class Engine:
    def __init__(self,model_path,cache_path,threads=8,glossary=None):
        self.exact={**TERM_LOOKUP, **{k.casefold():v for k,v in (glossary or {}).items()}}
        self.source_sp=spm.SentencePieceProcessor(model_file=str(model_path/'source.spm'))
        self.target_sp=spm.SentencePieceProcessor(model_file=str(model_path/'target.spm'))
        self.translator=ctranslate2.Translator(str(model_path),device='cpu',compute_type='int8',intra_threads=threads,inter_threads=1)
        self.db=sqlite3.connect(cache_path)
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('CREATE TABLE IF NOT EXISTS segments(version TEXT,source TEXT,target TEXT,flags TEXT,PRIMARY KEY(version,source))')
        self.db.execute('CREATE TABLE IF NOT EXISTS translations(version TEXT,source TEXT,target TEXT,flags TEXT,PRIMARY KEY(version,source))')
        self.segments={s:(t,json.loads(f)) for s,t,f in self.db.execute('SELECT source,target,flags FROM segments WHERE version=?',(VERSION,))}
        self.finished={s:(t,json.loads(f)) for s,t,f in self.db.execute('SELECT source,target,flags FROM translations WHERE version=?',(VERSION,))}
        self.model_calls=0

    def _raw(self,texts):
        if not texts:return []
        encoded=[self.source_sp.encode(t,out_type=str)+['</s>'] for t in texts]
        results=self.translator.translate_batch(encoded,beam_size=2,max_input_length=0,
            max_decoding_length=512,batch_type='tokens',max_batch_size=1536,
            replace_unknowns=True,disable_unk=True)
        self.model_calls+=len(texts)
        output=[]
        for result in results:
            output.append(self.target_sp.decode(result.hypotheses[0]))
        return output

    def _put_segment(self,source,target,flags):
        self.segments[source]=(target,flags)
        self.db.execute('INSERT OR REPLACE INTO segments VALUES(?,?,?,?)',(VERSION,source,target,json.dumps(flags)))

    def translate_segments(self,segments):
        todo=list(dict.fromkeys(s for s in segments if s not in self.segments))
        work=[]
        for source in todo:
            if source.casefold() in self.exact:
                self._put_segment(source,self.exact[source.casefold()],[])
                continue
            masked,values=protect(source)
            if not ENGLISH_RE.search(MARKER_RE.sub('',masked)):
                direct=unprotect(masked,values)
                self._put_segment(source,direct,[])
            else:
                work.append(Work(source,masked,values))
        raw=self._raw([w.masked for w in work])
        fallback=[]
        for w,result in zip(work,raw):
            result=clean_model_output(w.source,result)
            restored=unprotect(result,w.values)
            errors=validation_errors(w.source,restored) if restored is not None else ['markers']
            if not restored:errors.append('empty')
            if errors:
                fallback.append((w.source,errors))
            else:
                self._put_segment(w.source,restored,[])
        if fallback:
            self._fallback(fallback)
        self.db.commit()

    def _fallback(self,failed):
        """Translate unprotected fragments; preserve exact structural atoms."""
        plans={}; fragments=[]
        for source,errors in failed:
            parts=[];cursor=0
            for start,end,value,_ in protected_spans(source):
                if start>cursor:parts.append(('text',source[cursor:start]))
                parts.append(('literal',value));cursor=end
            if cursor<len(source):parts.append(('text',source[cursor:]))
            if not parts:parts=[('text',source)]
            plans[source]=(parts,errors)
            for kind,text in parts:
                if kind=='text' and ENGLISH_RE.search(text):fragments.append(text.strip())
        unique=list(dict.fromkeys(fragments))
        raw=self._raw(unique)
        mapping=dict(zip(unique,raw))
        for source,(parts,errors) in plans.items():
            out=[]
            for kind,text in parts:
                if kind=='literal' or not ENGLISH_RE.search(text):out.append(text);continue
                translated=clean_model_output(text.strip(),mapping[text.strip()]).strip()
                # A hallucinated statistic or symbol must not reach a tooltip.
                if validation_errors(text.strip(),translated):translated=text.strip()
                leading=re.match(r'^\s*',text).group()
                trailing=re.search(r'\s*$',text).group()
                out.append(leading+translated+trailing)
            target=''.join(out).strip()
            flags=['fallback_split']+errors
            final_errors=validation_errors(source,target)
            if final_errors:
                target=source
                flags+=['retained_english']+final_errors
            self._put_segment(source,target,list(dict.fromkeys(flags)))

    def translate_sources(self,sources):
        plans={};segments=[]
        for source in sources:
            if source in self.finished:continue
            plan=chunks(source)
            plans[source]=plan
            segments += [text.strip() for kind,text in plan if kind=='text' and text.strip()]
        self.translate_segments(segments)
        for source,plan in plans.items():
            out=[];flags=[]
            for kind,text in plan:
                if kind=='literal' or not text.strip():out.append(text);continue
                target,segment_flags=self.segments[text.strip()]
                leading=re.match(r'^\s*',text).group()
                trailing=re.search(r'\s*$',text).group()
                out.append(leading+target+trailing)
                flags.extend(segment_flags)
            target=''.join(out)
            errors=validation_errors(source,target)
            if errors:
                # Sentence boundaries cannot alter any protected token.
                target=source;flags += ['retained_english','final_validation']+errors
            flags=list(dict.fromkeys(flags))
            if target==source and ENGLISH_RE.search(source):flags.append('unchanged')
            if re.search(r'\b[A-Za-z]{3,}(?:[ ,]+[A-Za-z]{3,}){4,}\b',TAG_RE.sub('',target)):
                flags.append('untranslated_span')
            self.finished[source]=(target,flags)
            self.db.execute('INSERT OR REPLACE INTO translations VALUES(?,?,?,?)',(VERSION,source,target,json.dumps(flags)))
        self.db.commit()

    def export(self,output,review_path):
        temp=output.with_suffix(output.suffix+'.tmp')
        temp.write_text(json.dumps({s:t for s,(t,f) in self.finished.items()},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        temp.replace(output)
        with review_path.open('w',encoding='utf-8') as f:
            for source,(target,flags) in self.finished.items():
                if flags:
                    f.write(json.dumps({'source':source,'translation':target,'flags':flags},ensure_ascii=False)+'\n')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--catalog',type=Path,required=True)
    parser.add_argument('--model',type=Path,default=ROOT/'fugumt-model')
    parser.add_argument('--cache',type=Path,default=ROOT/'translation_cache.sqlite3')
    parser.add_argument('--output',type=Path,default=ROOT/'machine_translations.json')
    parser.add_argument('--limit',type=int,default=0)
    parser.add_argument('--threads',type=int,default=8)
    parser.add_argument('--glossary',type=Path)
    parser.add_argument('--batch',type=int,default=192)
    args=parser.parse_args()
    rows=[json.loads(line) for line in args.catalog.read_text(encoding='utf-8').splitlines()]
    rows.sort(key=lambda row:PRIORITY.get(row.get('category'),8))
    sources=list(dict.fromkeys(row['source'] for row in rows))
    if args.limit:sources=sources[:args.limit]
    glossary=json.loads(args.glossary.read_text(encoding='utf-8')) if args.glossary else None
    engine=Engine(args.model,args.cache,args.threads,glossary)
    todo=[s for s in sources if s not in engine.finished]
    start=time.monotonic();initial=len(engine.finished)
    print(json.dumps({'version':VERSION,'sources':len(sources),'cached':initial,'todo':len(todo)},ensure_ascii=False),flush=True)
    review_path=args.output.with_name('machine_review_flags.jsonl')
    progress_path=args.output.with_name('translation_progress.json')
    for offset in range(0,len(todo),args.batch):
        engine.translate_sources(todo[offset:offset+args.batch])
        elapsed=time.monotonic()-start
        done=len(engine.finished)-initial
        stats=Counter(flag for _,flags in engine.finished.values() for flag in flags)
        progress={'completed':len(engine.finished),'total':len(sources),'session_completed':done,'elapsed_seconds':round(elapsed,2),
            'strings_per_second':round(done/elapsed,2),'eta_seconds':round((len(todo)-done)*elapsed/done,1),
            'model_calls':engine.model_calls,'flags':dict(stats)}
        progress_path.write_text(json.dumps(progress,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        print(json.dumps(progress,ensure_ascii=False),flush=True)
        if offset%(args.batch*5)==0:engine.export(args.output,review_path)
    engine.export(args.output,review_path)
    print('COMPLETE '+str(args.output),flush=True)


if __name__=='__main__':main()
