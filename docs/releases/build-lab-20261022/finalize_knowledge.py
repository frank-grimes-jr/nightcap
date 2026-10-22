"""Close reviewed provenance/ledger pins and the superseded October18 rule pin."""
import argparse
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
TARGET=Path('C:/Users/verre/.codex/skills/nightcap-development/references/sources.json')
STAGE=HERE/'knowledge'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def prepare():
    old=TARGET.read_text(encoding='utf-8');data=json.loads(old)
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    reviewed={'tools/build_lab_data.py','docs/build-lab/data-provenance.json','wiki/content-review.json'}
    for topic in ['wiki','balance']:
        for e in data['topics'][topic]:
            if e['path'] in reviewed:
                e.update(root=ROOT.as_posix(),revision=revision+' + reviewed ledger closeout',sha256=sha(ROOT/e['path']))
    # Compared old reviewed revision8e8d71d with current HEAD: the only header
    # delta is NightcapTHJBehaviors, already documented/deployed October19.
    # Old worktree and current header are byte-identical after EOL normalization.
    for e in data['topics']['balance']:
        if e['path']=='server-mods/code/common/ruletypes.h':
            e.update(root=ROOT.as_posix(),revision=revision,sha256=sha(ROOT/e['path']),role='Reviewed 750 caps and October19 THJ behavior rule; current header replaces superseded October18 pin')
    new=json.dumps(data,ensure_ascii=False,indent=2)+'\n'
    (STAGE/'final-sources.json').write_text(new,encoding='utf-8')
    (STAGE/'final-preimage.txt').write_text(sha(TARGET))
    (STAGE/'final-sources.patch').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/references/sources.json',tofile='b/references/sources.json')),encoding='utf-8')
    print('Prepared reviewed source-ledger closeout')


def apply():
    assert sha(TARGET)==(STAGE/'final-preimage.txt').read_text(),'Concurrent knowledge update'
    TARGET.write_bytes((STAGE/'final-sources.json').read_bytes())
    print('Applied reviewed source-ledger closeout')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true')
    apply() if parser.parse_args().apply else prepare()
