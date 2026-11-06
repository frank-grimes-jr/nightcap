"""Prove main plus reviewed LF overrides regenerates the complete published wiki."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
DEST=ROOT/'artifacts/dungeon-readiness/reproduced-v2'
inputs=json.loads((HERE/'published-source-inputs.json').read_text())['inputs']
assert not DEST.exists()
shutil.copytree(ROOT/'wiki',DEST/'wiki',ignore=shutil.ignore_patterns('dist','__pycache__'))
shutil.copytree(ROOT/'config',DEST/'config')
for record in inputs:
    path=DEST/'wiki'/record['path']
    if path.exists() and path.suffix in ('.json','.py','.css','.js','.cjs','.html','.conf','.svg','.md','.txt'):
        path.write_text(path.read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
subprocess.run(['git','apply','--directory=artifacts/dungeon-readiness/reproduced-v2',str(HERE/'published-source-overrides.patch')],cwd=ROOT,check=True)
for record in inputs:
    path=DEST/'wiki'/record['path']
    assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==record['sha256'],record['path']
subprocess.run(['python',str(DEST/'wiki/build.py')],check=True)
actual={p.relative_to(DEST/'wiki/dist').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (DEST/'wiki/dist').rglob('*') if p.is_file()}
expected=json.loads((ROOT/'artifacts/dungeon-readiness/20261106-dungeon-readiness-v1.tar.json').read_text())
assert actual==expected
report=dict(status='PASS',source_inputs=len(inputs),files=len(actual),
            method='Actual main source plus reviewed LF-normalized overrides reproduces every published output; unrelated previews excluded')
(HERE/'public-source-reproduction.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
