"""Stage or publish the exact signed one-asset release; no signing material leaves this host."""
from pathlib import Path
import argparse,base64,hashlib,importlib.util,json,subprocess
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('release_ship',HERE.parents[3]/'docs/items/paladin-weapon-grip/balance/release/ship.py');ship=importlib.util.module_from_spec(spec);spec.loader.exec_module(ship)
STAGE='/opt/nightcap/releases/cast-bar-client-2026103002'
SIGNED=HERE.parents[3]/'.local/cast-bar/release/signed'
NAMES=('channel.json', 'previous-channel.json', 'spells_us.txt')


def main(action):
    receipt=json.loads((SIGNED/'verification.json').read_text())
    assert receipt['release']==2026103002 and receipt['status']=='signed_candidate_not_published'
    files={n:(SIGNED/n).read_bytes() for n in NAMES}
    assert hashlib.sha256(files['channel.json']).hexdigest()==receipt['channel_sha256']
    assert hashlib.sha256(files['previous-channel.json']).hexdigest()==receipt['previous_channel_sha256']
    for n,h in receipt['archive_sha256'].items():assert hashlib.sha256(files[n]).hexdigest()==h
    files['publish.py']=(HERE/'publish.py').read_bytes()
    files['test_publish.py']=(HERE/'test_publish.py').read_bytes()
    pins={n:hashlib.sha256(b).hexdigest() for n,b in files.items()}
    if action=='stage':
        encoded={n:base64.b64encode(b).decode() for n,b in files.items()}
        result=ship.remote(f"""from pathlib import Path
import base64,hashlib,json,os,shutil
free_before=shutil.disk_usage('/opt/nightcap').free
assert free_before >= 2*{sum(len(b) for b in files.values())} + 350*1024**2,'Client staging disk reserve'
os.umask(0o077);stage=Path({STAGE!r});assert not stage.exists();stage.mkdir(mode=0o700)
files={encoded!r};pins={pins!r}
for name,value in files.items():
 path=stage/name;assert path.resolve().is_relative_to(stage);path.parent.mkdir(parents=True,exist_ok=True)
 data=base64.b64decode(value);assert hashlib.sha256(data).hexdigest()==pins[name]
 with path.open('xb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
import subprocess
r=subprocess.run(['python3','-m','unittest','-v','test_publish'],cwd=stage,capture_output=True,text=True)
assert r.returncode==0,(r.stdout+r.stderr)[-5000:]
free_after=shutil.disk_usage('/opt/nightcap').free
assert free_after >= {sum(len(b) for b in files.values())} + 350*1024**2,'Post-stage disk reserve'
print(json.dumps({{'stage':str(stage),'files':pins,'published':False,'linux_tests':r.stdout+r.stderr,'free_before':free_before,'free_after':free_after,'reserve_bytes':350*1024**2}}))
""")
    else:
        assert not (HERE/'published.json').exists(),'Inspect prior publication; never blindly replay'
        result=ship.remote(f"""from pathlib import Path
import hashlib,json,subprocess
stage=Path({STAGE!r});pins={pins!r}
for name,digest in pins.items():assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==digest
with (stage/'publication.log').open('x') as stream:p=subprocess.run(['python3',str(stage/'publish.py'),'--stage',str(stage),'--publish'],stdout=stream,stderr=subprocess.STDOUT)
assert p.returncode==0,(stage/'publication.log').read_text()[-5000:]
print((stage/'published.json').read_text())
""")
    (HERE/('staged.json' if action=='stage' else 'published.json')).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'action':action,'release':2026103002,'published':action=='publish','channel_sha256':receipt['channel_sha256']}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['stage','publish']);main(parser.parse_args().action)
