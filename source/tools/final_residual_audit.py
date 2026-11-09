#!/usr/bin/env python3
"""Audit the selected translations without mutating the built MOD.

Uses the same dictionary precedence as build.py. The manifest explains every
currently untranslated whole display field; a separate heuristic lists English
clauses embedded in otherwise Japanese text. Latin names/abbreviations inside
Japanese are not proof of an untranslated sentence or proof of perfect coverage.
"""
import collections
import hashlib
import json
import re
from pathlib import Path

from build import load_mapping, term_translation, check_translation
from common import PROTECTED

PROJECT=Path(__file__).resolve().parents[1]
WORKSPACE=PROJECT.parent
JP=re.compile(r'[\u3040-\u30ff\u3400-\u9fff]')
FUNCTION_WORDS=re.compile(r"\b(?:the|is|are|have|has|will|can|would|could|should|may|and|with|without|from|for|to|of|your|you|we|they|it|its|this|that|our|be|been|was|were|but|not)\b",re.I)
RUNS=re.compile(r"(?:[A-Za-z][A-Za-z'’-]*[ \t,;:.!?()/\-]+){4,}[A-Za-z][A-Za-z'’-]*")


def audit():
    from followup_022 import context_overrides
    contextual=context_overrides(PROJECT)
    machine_path=WORKSPACE/'translation-work/machine_translations.json'
    if not machine_path.exists():
        machine_path=PROJECT/'machine_translation/machine_translations.json'
    machine=load_mapping(machine_path)
    partial={};manual={};decisions={}
    for path in sorted((PROJECT/'source').glob('partial_*.json')):partial.update(load_mapping(path))
    for path in sorted((PROJECT/'source').glob('manual_*.json')):manual.update(load_mapping(path))
    glossary={k.casefold():v for k,v in load_mapping(PROJECT/'source/glossary.json').items()}
    for name in ['remaining_review.json','expanded_remaining_review.json']:
        report=json.loads((PROJECT/'reports'/name).read_text(encoding='utf-8'))
        for decision in report.get('retained_decisions',[]):decisions[decision['source']]=decision['reason']
    report=json.loads((PROJECT/'reports/remaining_mixed_review.json').read_text(encoding='utf-8'))
    for row in report['restored_fictional_language']:
        decisions[row['source']]='fictional_language'
    lua=load_mapping(PROJECT/'source/lua_translations.json')
    def select(s,kind):
        target=machine.get(s);method='machine'
        if isinstance(target,dict):target=target.get('translation',target.get('ja'))
        if kind=='lua':
            if s in lua:target=lua[s];method='lua_reviewed'
            return target,method
        if s in partial:target=partial[s];method='machine_repaired'
        term=term_translation(s,glossary)
        if term is not None:target=term;method='glossary'
        if s in manual:target=manual[s];method='manual'
        return target,method
    preserved=[];unclassified=[];missing=[];errors=[];clauses={};catalog_counts={}
    for kind,name in [('json','catalog.jsonl'),('append','append_catalog.jsonl'),('embedded','embedded_catalog.jsonl'),('lua','lua_catalog.jsonl')]:
        path=PROJECT/'source'/name
        if not path.exists():continue
        rows=[json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
        catalog_counts[kind]=len(rows)
        for row in rows:
            source=row['source'];target,method=select(source,kind)
            key=(row['asset'], row['path'], source)
            if kind=='json' and key in contextual:
                target,method=contextual[key],'manual'
            field={k:row[k] for k in ('id','asset','path','source')}
            field.update({'catalog':kind,'method':method,'translation':target})
            if target is None:
                missing.append(field);continue
            if kind!='lua':
                issues=check_translation(source,target)
                if issues:errors.append({**field,'issues':issues});continue
            plain=PROTECTED.sub('',target) if kind!='lua' else target
            # The Lua page connector is intentionally neutral punctuation.
            if kind=='lua' and source==' of ' and target==' / ':
                preserved.append({**field,'decision':'localized_numeric_page_separator'});continue
            if target==source or not JP.search(plain):
                reason=('chemical_or_species_formula' if kind=='json' and key in contextual and source==target=='Ne' else decisions.get(source))
                if reason:
                    preserved.append({**field,'decision':reason})
                else:
                    unclassified.append(field)
                continue
            scan=re.sub(r'https?://\S+',' ',plain)
            scan=re.sub(r'`[^`\n]*`',' ',scan)
            runs=[m.group().strip() for m in RUNS.finditer(scan)
                  if len(FUNCTION_WORDS.findall(m.group()))>=2]
            if runs:
                clauses[(source,target)]={'source':source,'translation':target,'runs':runs,
                                         'sample_field':{k:field[k] for k in ('catalog','asset','path')}}
    result={'catalog_fields':catalog_counts,
            'all_catalog_fields':sum(catalog_counts.values()),
            'whole_fields_preserved_with_decision':len(preserved),
            'preserved_unique_sources':len({r['source'] for r in preserved}),
            'preserved_by_decision':dict(collections.Counter(r['decision'] for r in preserved)),
            'unclassified_whole_fields':len(unclassified),
            'unclassified_unique_sources':len({r['source'] for r in unclassified}),
            'missing_translation_fields':len(missing),'structural_errors':len(errors),
            'mixed_english_clause_unique_sources':len(clauses),
            'limits':['This manifest covers the selected catalog fields only.',
                      'The English-clause scan is a heuristic; terminology or transliterated names can still occur in Japanese text.',
                      'It is not a semantic review of every machine translation or an in-game runtime test.'],
            'preserved':preserved,'unclassified':unclassified,'missing':missing,'errors':errors,
            'mixed_english_clauses':list(clauses.values())}
    result['input_sha256']={name:hashlib.sha256((PROJECT/'source'/name).read_bytes()).hexdigest()
                           for name in ['catalog.jsonl','translated_catalog.jsonl','append_catalog.jsonl','append_translated_catalog.jsonl']}
    (PROJECT/'reports/final_residual_decisions.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:v for k,v in result.items() if k not in {'preserved','unclassified','missing','errors','mixed_english_clauses','input_sha256','limits'}},ensure_ascii=False,indent=2))
    for label,rows in [('unclassified',unclassified),('errors',errors)]:
        unique={r['source']:r for r in rows}
        for row in unique.values():print(label,json.dumps(row,ensure_ascii=False))
    for row in clauses.values():print('mixed_clause',row['sample_field'],row['runs'])


if __name__=='__main__':audit()
