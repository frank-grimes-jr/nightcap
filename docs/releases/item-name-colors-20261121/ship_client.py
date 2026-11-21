"""Stage then publish the exact approved client color delta under the deployment lock."""
import argparse
import base64
import hashlib
import json
from support import ART,HERE,RELEASE,STAGE,remote,save


def main(action):
    signed=ART/'signed'
    receipt=json.loads((signed/'verification.json').read_bytes())
    assert receipt['release']==RELEASE and receipt['changed_assets']==2
    files={name:(signed/name).read_bytes() for name in
           ('channel.json','previous-channel.json','dinput8.dll','nightcap-patch-sites.json')}
    for name in ('publish.py','test_publish.py'):files[name]=(HERE/name).read_bytes()
    pins={name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()}
    baseline=json.loads((HERE/'baseline.json').read_bytes())
    assert pins['channel.json']==receipt['channel_sha256']
    assert pins['previous-channel.json']==baseline['channel_sha256']
    if action=='stage':
        encoded={name:base64.b64encode(raw).decode() for name,raw in files.items()}
        result=remote(f"""from pathlib import Path
import base64,hashlib,json,os,shutil,subprocess
stage=Path({STAGE!r});assert not stage.exists()
assert shutil.disk_usage('/opt/nightcap').free>2*{sum(map(len,files.values()))}+350*1024**2
os.umask(0o077);stage.mkdir(mode=0o700);files={encoded!r};pins={pins!r}
for name,raw in files.items():
 data=base64.b64decode(raw,validate=True);assert hashlib.sha256(data).hexdigest()==pins[name]
 (stage/name).parent.mkdir(parents=True,exist_ok=True)
 with (stage/name).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
tests=subprocess.run(['python3','-B','-m','unittest','test_publish'],cwd=stage,capture_output=True,text=True,timeout=90)
assert tests.returncode==0,tests.stderr[-2200:]
print(json.dumps(dict(status='staged_not_published',pins=pins,linux_tests=tests.stderr.strip())))
""")
    else:
        result=remote(f"""from pathlib import Path
import fcntl,hashlib,importlib.util,json
stage=Path({STAGE!r});pins={pins!r}
for name,pin in pins.items():assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==pin
root=Path('/opt/nightcap/deploy/production')
spec=importlib.util.spec_from_file_location('publisher',stage/'publish.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
with (root/'.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert p.services()=={baseline['services']!r},'Service identity changed since capture'
 result=p.publish(stage,root/'data/public')
 assert p.services()=={baseline['services']!r},'Service identity changed during publication'
 p.replace((json.dumps(result,indent=2)+chr(10)).encode(),stage/'published.json')
print(json.dumps(result))
""")
    save(HERE/('client-staged.json' if action=='stage' else 'client-published.json'),result)
    print(json.dumps(dict(action=action,release=RELEASE,status=result.get('status','published'))))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('stage','publish'))
    main(parser.parse_args().action)
