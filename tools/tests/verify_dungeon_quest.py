"""Run the actual Keeper quest regression with the local Linux Perl runtime."""
import json
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]
files={p:(ROOT/p).read_text(encoding='utf-8') for p in
       ('tools/tests/instance_keeper_visuals.t','server-mods/quests/global/Instance_Keeper.pl')}
script='files='+repr(files)+'''\nfrom pathlib import Path
import subprocess,tempfile
with tempfile.TemporaryDirectory(prefix='nightcap-dungeon-quest-') as folder:
 root=Path(folder)
 for path,text in files.items():
  target=root/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(text)
 subprocess.run(['perl',str(root/'tools/tests/instance_keeper_visuals.t')],check=True)
'''
p=subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-'],input=script,text=True,capture_output=True)
print(p.stdout)
if p.returncode:raise RuntimeError(p.stderr)
assert '1..18' in p.stdout and 'not ok' not in p.stdout
(ROOT/'docs/dungeons/quest-verification.json').write_text(json.dumps(dict(status='passed',assertions=18,
 scope='Actual Perl Keeper with native API doubles; native binding is separately compiled',output=p.stdout),indent=2)+'\n')
