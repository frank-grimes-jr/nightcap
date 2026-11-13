"""Publish the validated raid catalog following native activation and public predecessor verification."""
import hashlib
import json
import subprocess
from pathlib import Path
from probe import remote, SSH, HERE, ROOT
from wiki_release import ART, PREVIOUS, RELEASE

def main():
    paths=[ART/(RELEASE+'.tar.gz'),ART/(RELEASE+'.tar.json')]
    paths.extend(ART/'wiki-source/wiki'/n for n in ('deploy.py','update.py','test_deploy.py','test_update.py','nginx.conf'))
    pins={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    ssh=SSH[:-1]
    upload='/home/ubuntu/wiki-'+RELEASE
    subprocess.run(ssh+['mkdir -m 700 '+upload],check=True)
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*ssh[1:-1],*map(str,paths),ssh[-1]+':'+upload+'/'],check=True,timeout=300)
    from wiki_release import ORIGIN
    expected=json.loads((ORIGIN/(PREVIOUS+'.tar.json')).read_bytes())
    values=dict(UP=upload,REL=RELEASE,PRE=PREVIOUS,PINS=pins,BASE=expected)
    script="""
import fcntl,hashlib,importlib.util,json,os,shutil,subprocess
from pathlib import Path
os.umask(0o077)
root=Path('/opt/nightcap/deploy/production');up=Path(UP);dest=Path('/opt/nightcap/releases')/('wiki-'+REL)
live=json.loads(Path('/opt/nightcap/releases/classic-raid-augments-20261112-v2/evidence/activation/deployed.json').read_text());assert live['gateway_open'] and live['items']==16
assert {p.name for p in up.iterdir()}==set(PINS);dest.mkdir(mode=0o700)
for name,pin in PINS.items():
 path=up/name
 assert path.is_file() and not path.is_symlink() and hashlib.sha256(path.read_bytes()).hexdigest()==pin
 shutil.copyfile(path,dest/name)
tests=subprocess.run(['python3','-B','-m','unittest','test_deploy','test_update'],cwd=dest,capture_output=True,text=True,timeout=180)
assert tests.returncode==0,tests.stderr[-1000:]
spec=importlib.util.spec_from_file_location('deploy',dest/'deploy.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
with (root/'.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 pointer=root/'data/public/wiki/current';assert str(pointer.readlink())=='releases/'+PRE
 assert json.loads((root/'website-history'/PRE/'manifest.json').read_text())==BASE
 before=m.services(); config=root/'nginx.conf';channel=root/'data/public/channel.json'
 pin=m.sha(config.read_bytes());inode=config.stat().st_ino;client=m.sha(channel.read_bytes())
 m.verify(BASE)
 result=json.loads(subprocess.check_output(['python3',str(dest/'update.py'),str(dest/(REL+'.tar.gz')),str(dest/(REL+'.tar.json')),REL,PRE,pin],timeout=420))
 after=json.loads((dest/(REL+'.tar.json')).read_text());m.verify(after)
 assert str(pointer.readlink())=='releases/'+REL and m.services()==before and m.sha(channel.read_bytes())==client and config.stat().st_ino==inode and m.sha(config.read_bytes())==pin
 result.update(files_verified=len(after),client_preserved=True,services_preserved=True,configuration_preserved=True)
 (dest/'publication.json').write_text(json.dumps(result,indent=2))
 print(json.dumps(result))
"""
    result=json.loads(remote('\n'.join(k+'='+repr(v) for k,v in values.items())+'\n'+script,timeout=1100))
    (HERE/'wiki-publication.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(result)
if __name__=='__main__':main()
