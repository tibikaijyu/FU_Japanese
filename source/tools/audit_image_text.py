"""Read-only OCR inventory of FU UI textures; no output game assets are edited."""
import concurrent.futures
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'fu-upstream'
paths = []
seen = set()
for folder in ('interface', 'fu_metagui', 'zb', 'frackinship'):
    for path in (SOURCE/folder).rglob('*.png'):
        with Image.open(path) as image:
            w, h = image.size
            if not (w >= 80 and h >= 12 or w >= 35 and h >= 10 and w/h >= 1.6):
                continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest in seen:
            continue
        seen.add(digest)
        paths.append(path)


def inspect(path):
    with Image.open(path).convert('RGBA') as image:
        size = image.size
        backdrop = Image.new('RGBA', size, (30, 30, 30, 255))
        backdrop.alpha_composite(image)
        enlarged = backdrop.convert('RGB').resize((size[0]*4, size[1]*4), Image.Resampling.NEAREST)
        buffer = io.BytesIO()
        enlarged.save(buffer, format='PNG')
    result = subprocess.run(['tesseract', 'stdin', 'stdout', '--psm', '11', 'tsv'],
                            input=buffer.getvalue(), stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, env={**os.environ, 'OMP_THREAD_LIMIT':'1'})
    words = []
    for line in result.stdout.decode(errors='replace').splitlines()[1:]:
        cells = line.split('\t')
        if len(cells) != 12 or cells[0] != '5':
            continue
        if float(cells[10]) >= 35 and re.search(r'[A-Za-z]{3}', cells[11]):
            words.append({'text':cells[11], 'confidence':float(cells[10]),
                          'box':[int(cells[i])/4 for i in range(6,10)]})
    return {'asset':path.relative_to(SOURCE).as_posix(), 'size':list(size), 'words':words}


if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        rows = list(executor.map(inspect, paths))
    out = ROOT/'fu-japanese/reports/image_text_inventory.json'
    report = {'candidate_textures_scanned':len(rows), 'textures_with_ocr_candidates':sum(bool(r['words']) for r in rows),
              'method':'OCR for inspection only. Candidate words require visual/contextual review; not a proof of text absence.',
              'candidates':[r for r in rows if r['words']]}
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='candidates'}))
