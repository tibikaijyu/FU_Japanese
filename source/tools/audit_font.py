"""Check optional-font glyph coverage of final displayed Japanese strings."""
import argparse
import collections
import hashlib
import json
from pathlib import Path

from fontTools.ttLib import TTFont


def values(tree):
    if isinstance(tree, dict):
        for value in tree.values():
            yield from values(value)
    elif isinstance(tree, list):
        for value in tree:
            yield from values(value)
    elif isinstance(tree, str):
        yield tree


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('project',type=Path)
    parser.add_argument('font',type=Path)
    args=parser.parse_args()
    texts=set()
    for name in ('translated_catalog.jsonl','append_translated_catalog.jsonl'):
        for line in (args.project/'source'/name).read_text(encoding='utf-8').splitlines():
            texts.add(json.loads(line)['translation'])
    for row in json.loads((args.project/'reports/embedded_manifest.json').read_text(encoding='utf-8')):
        texts.update(change['target'] for change in row['display_changes'])
    texts.update(values(json.loads((args.project/'source/lua_translations.json').read_text(encoding='utf-8'))))
    texts.update(values(json.loads((args.project/'source/lua_dynamic_translations.json').read_text(encoding='utf-8'))))
    for row in json.loads((args.project/'source/authored_adaptations.json').read_text(encoding='utf-8')):
        texts.add(row['translation'])
    ui=json.loads((args.project/'source/ui_image_labels.json').read_text(encoding='utf-8'))
    for row in ui['entries']:
        if row.get('text'): texts.add(row['text'])
        for label in row.get('labels',[]):
            if label.get('text'): texts.add(label['text'])
        if isinstance(row.get('replacement'),dict) and row['replacement'].get('value'):
            texts.add(row['replacement']['value'])
    texts.update(('はじめから','つづきから','おわり'))
    font=TTFont(args.font)
    cmap=font.getBestCmap()
    missing=collections.Counter(char for value in texts for char in value if ord(char)>127 and not char.isspace() and ord(char) not in cmap)
    report={
        'font':'Unmodified PixelMplus10 Regular',
        'font_sha256':hashlib.sha256(args.font.read_bytes()).hexdigest(),
        'unicode_characters_covered':len(cmap),
        'distinct_final_translation_values_checked':len(texts),
        'missing_non_ascii':{f'U+{ord(c):04X}':{'character':c,'occurrences':n} for c,n in sorted(missing.items())},
        'note':'Character-map test only; not a game rendering check. Starbound private-use/ancient glyphs are not included. Existing Japanese font can be retained.',
    }
    (args.project/'reports/font_coverage.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
