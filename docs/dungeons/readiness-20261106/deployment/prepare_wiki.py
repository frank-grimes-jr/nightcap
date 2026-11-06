"""Reproduce the exact published source, then prepare the scoped Keeper guide/note."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
SOURCE=Path('E:/EQ_Local_Dev/_worktrees/character-stats-shield-block/artifacts/character-stats-shield-block/wiki-source')
ART=ROOT/'artifacts/dungeon-readiness'
TARGET=ART/'wiki-source'
RELEASE='20261106-dungeon-readiness-v1'


def hashes(folder):
    return {p.relative_to(folder).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.rglob('*') if p.is_file()}


def main():
    prior=SOURCE.parents[0]/'20261106-character-stats-shield-block-v1.tar.json'
    baseline=json.loads(prior.read_text())
    assert len(baseline)==510 and hashes(SOURCE/'wiki/dist')==baseline
    assert not TARGET.exists()
    shutil.copytree(SOURCE/'wiki',TARGET/'wiki',ignore=shutil.ignore_patterns('dist','__pycache__'))
    shutil.copytree(SOURCE/'config',TARGET/'config')
    subprocess.run(['python',str(TARGET/'wiki/build.py')],check=True)
    assert hashes(TARGET/'wiki/dist')==baseline,'Public source reproduction failed'
    body=('<h2 id="keeper-readiness-20261106">November6: Instance Keeper entry repaired — live QA</h2>'
          '<p>Raid and Grind entry now accepts the current expedition augment release. '
          'Existing runs, progress and earned rewards are preserved. No client update or run reset is needed. '
          'Entry, complete-run and balance checks remain open for player testing.</p>')
    for slug in ('recent-changes','dungeon-modes'):
        path=TARGET/'wiki/articles'/(slug+'.json');article=json.loads(path.read_text(encoding='utf-8'))
        if slug=='recent-changes':article['body']=body+article['body']
        else:
            anchor='The creator chooses the mode.'
            assert article['body'].count(anchor)==1
            article['body']=article['body'].replace(anchor,anchor+' Use Enter to resume an existing run after an entry error; resetting is unnecessary.')
        path.write_text(json.dumps(article,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
    archive=ART/(RELEASE+'.tar.gz')
    subprocess.run(['python',str(TARGET/'wiki/build.py'),'--package',str(archive)],check=True)
    after=json.loads(archive.with_suffix('.json').read_text())
    assert after.keys()==baseline.keys()
    changed=sorted(name for name in after if after[name]!=baseline[name])
    assert changed==['dungeon-modes.html','recent-changes.html','search-index.json'],changed
    source_record=dict(status='PASS',previous_release='20261106-character-stats-shield-block-v1',files=510,
        changed=changed,preserved_files=507,source=str(SOURCE),target=str(TARGET),
        method='Exact public-source reproduction before scoped two-article edit; no unrelated main previews',
        home_features_commands_catalog='No mechanics, command, item/stat/drop/acquisition or eligibility change; all public values retained',
        publication='prepared only; activation receipt and guarded pointer switch required')
    (HERE/'wiki-source-review.json').write_text(json.dumps(source_record,indent=2)+'\n')
    (HERE/'wiki-baseline-manifest.json').write_text(json.dumps(baseline,indent=2)+'\n')
    print(json.dumps(source_record,indent=2))


if __name__=='__main__':main()
