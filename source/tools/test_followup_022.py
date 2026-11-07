#!/usr/bin/env python3
"""Exercise the release overlay's rebuild and rejection behavior."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from followup_022 import apply, read_manifest


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(project, mod):
    project,mod=Path(project),Path(mod)
    manifest=read_manifest(project)
    def content_state():
        paths=[mod/r['asset'] for r in manifest['files']]
        paths += [project/'source/translated_catalog.jsonl', project/'reports/retained.json']
        return {str(p):sha(p) for p in paths}
    before=content_state()
    apply(project,mod)
    assert content_state()==before, 'Reapplying the reviewed overlay must be idempotent'
    translated=[json.loads(s) for s in (project/'source/translated_catalog.jsonl').read_text().splitlines()]
    retained=json.loads((project/'reports/retained.json').read_text())
    ne={r['id'] for r in manifest['field_overrides'] if r['source']==r['translation']=='Ne'}
    assert len(ne)==4 and not (ne & {r['id'] for r in translated})
    assert ne <= {r['id'] for r in retained if r.get('decision')=='chemical_or_species_formula'}
    with tempfile.TemporaryDirectory(prefix='fu022-rebuild-') as d:
        temp=Path(d)
        for r in manifest['files']:
            dest=temp/r['asset'];dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(mod/r['asset'],dest)
        changed=temp/manifest['files'][0]['asset']
        changed.write_bytes(changed.read_bytes()+b'\n')
        before_temp={str(p):sha(p) for p in temp.rglob('*') if p.is_file()}
        try:
            apply(project,temp)
        except ValueError as error:
            assert 'Base display asset changed' in str(error)
        else:
            raise AssertionError('Unknown prior edits must stop the overlay')
        assert before_temp=={str(p):sha(p) for p in temp.rglob('*') if p.is_file()}
        assert content_state()==before
    report={'passed':True,'tests_run':3,'runtime_tested':False,
            'cases':['Idempotent overlay, including repeated catalog updates',
                     'Four retained Ne symbols remain outside translation counts',
                     'Unknown generated file changes rejected before writing any file']}
    (project/'reports/followup_022_regression.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--project',required=True);p.add_argument('--mod',required=True)
    a=p.parse_args();run(a.project,a.mod)
