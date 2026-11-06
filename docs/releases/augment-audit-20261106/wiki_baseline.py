"""Reproduce the actual public wiki baseline before preparing its scoped update."""
import json
from pathlib import Path
import shutil
import subprocess
from probe import SSH

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
DEST=ROOT/'artifacts/augment-audit-release/wiki-source'
SOURCE=Path('E:/EQ_Local_Dev/_worktrees/wiki-hunt-rates-live')
code='''from pathlib import Path
import hashlib,json
root=Path('/opt/nightcap/deploy/production');pointer=root/'data/public/wiki/current'
assert pointer.is_symlink();release=pointer.readlink().name
print(json.dumps({'release':release,'manifest':json.loads((root/'website-history'/release/'manifest.json').read_text()),'config_sha256':hashlib.sha256((root/'nginx.conf').read_bytes()).hexdigest()}))
'''
p=subprocess.run(SSH+['sudo -n python3 -'],input=code,text=True,capture_output=True,timeout=40)
if p.returncode:raise RuntimeError(p.stderr[-2000:])
baseline=json.loads(p.stdout)
(HERE/'wiki-baseline.json').write_text(json.dumps(baseline,indent=2)+'\n')
assert not DEST.exists()
shutil.copytree(SOURCE/'wiki',DEST/'wiki',ignore=shutil.ignore_patterns('dist','__pycache__','*.tar.gz','*.tar.json'))
(DEST/'config').mkdir();shutil.copy2(SOURCE/'config/zone-hunt-rates.json',DEST/'config/zone-hunt-rates.json')
subprocess.run(['python',str(DEST/'wiki/build.py')],check=True)
import hashlib
actual={p.relative_to(DEST/'wiki/dist').as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (DEST/'wiki/dist').rglob('*') if p.is_file()}
assert actual==baseline['manifest'],('Wiki baseline differs',len(actual),len(baseline['manifest']),[n for n in set(actual)|set(baseline['manifest']) if actual.get(n)!=baseline['manifest'].get(n)][:15])
print(json.dumps({'status':'exact public baseline reproduced','release':baseline['release'],'files':len(actual),'source':str(DEST)}))
