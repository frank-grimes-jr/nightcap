"""Privately stage the reviewed paired payload and run Linux fault tests."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
from inventory_release_support import ROOT,HERE,ART,SSH,STAGE,AUTHORIZATION,remote,save


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    proof=json.loads((ART/'native-build.json').read_text());baseline=json.loads((ART/'release-baseline.json').read_text())
    assert proof['status']=='PASS' and proof['baseline_reproduced']
    assert proof['binary_sha256']['baseline']==baseline['base_hashes']['bin/zone']
    payload=ART/'payload-v1';payload.mkdir();(payload/'bin').mkdir();(payload/'client').mkdir()
    shutil.copyfile(ART/'candidate-zone',payload/'bin/zone')
    assert sha(payload/'bin/zone')==proof['binary_sha256']['candidate']
    for name in ('rollout.py','test_rollout.py','native-build.json','release-checks.json','review.json'):
        shutil.copyfile(HERE/name,payload/name)
    for name in ('channel.json','previous-channel.json','verification.json','dinput8.dll','nightcap-patch-sites.json','uifiles/nightcap/equi_inventory.xml'):
        target=payload/'client'/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(ART/'signed'/name,target)
    for name in ('publish.py','test_publish.py'):shutil.copyfile(HERE/'client'/name,payload/'client'/name)
    prior=(ROOT/'docs/releases/quick-buff-20261112/hotkey-fix/rollout.py').read_text(encoding='utf-8')
    (payload/'prior_rollout.py').write_text(prior,encoding='utf-8',newline='\n')
    tests=(ROOT/'tools/tests/test_quick_buff_hotkey_rollout.py').read_text(encoding='utf-8')
    old="ROOT/'docs/releases/quick-buff-20261112/hotkey-fix/rollout.py'"
    assert old in tests
    tests=tests.replace(old,"Path(__file__).with_name('prior_rollout.py')")
    (payload/'test_prior_rollout.py').write_text(tests,encoding='utf-8',newline='\n')
    for name in proof['source_delta']:
        target=payload/'source'/name;target.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run(['docker','cp','akk-stack-eqemu-server-1:/tmp/nightcap-inventory-build-20261112-v4/source/'+name,str(target)],check=True,capture_output=True)
        assert sha(target)==proof['source_sha256'][name]
    files={p.relative_to(payload).as_posix():sha(p) for p in payload.rglob('*') if p.is_file()}
    manifest={'owner_authorization':AUTHORIZATION,'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        'base_image_id':baseline['base_image_id'],'base_hashes':baseline['base_hashes'],
        'prior_operator_sha256':baseline['prior_operator_sha256'],'binaries':{'zone':proof['binary_sha256']['candidate']},
        'client_release':2026111202,'client_channel_sha256':baseline['client_channel_sha256'],
        'source_hashes':{n:proof['source_sha256'][n] for n in proof['source_delta']},'files':files}
    save(payload/'manifest.json',manifest)
    archive=ART/'inventory-combat-release-v1.tar.gz'
    with tarfile.open(archive,'x:gz') as handle:
        for p in sorted(payload.rglob('*')):
            if not p.is_file():continue
            info=handle.gettarinfo(str(p),p.relative_to(payload).as_posix());info.mode=0o755 if p.parent.name=='bin' else 0o600
            with p.open('rb') as source:handle.addfile(info,source)
    upload='/home/ubuntu/inventory-combat-release-20261112-v1.tar.gz'
    subprocess.run(['C:/Windows/System32/OpenSSH/scp.exe',*SSH[1:-1],str(archive),SSH[-1]+':'+upload],check=True,timeout=600)
    result=remote('stage_name='+repr(STAGE)+'\nupload_name='+repr(upload)+'\narchive_pin='+repr(sha(archive))+'\nexpected='+repr(files)+'''\nfrom pathlib import Path
import hashlib,json,os,shutil,subprocess,tarfile
os.umask(0o077);stage=Path(stage_name);upload=Path(upload_name)
assert not stage.exists(),'Existing stage: inspect receipts before any retry'
assert hashlib.sha256(upload.read_bytes()).hexdigest()==archive_pin
assert shutil.disk_usage('/opt/nightcap').free>4*1024**3+2*upload.stat().st_size
stage.mkdir(mode=0o700)
with tarfile.open(upload) as archive:
 entries=archive.getmembers();assert len({e.name for e in entries})==len(entries)
 assert {e.name for e in entries}==set(expected)|{'manifest.json'}
 for member in entries:
  target=stage/member.name
  assert member.isfile() and not member.issym() and not member.islnk() and target.resolve().is_relative_to(stage) and not target.exists()
  target.parent.mkdir(mode=0o700,parents=True,exist_ok=True)
  data=archive.extractfile(member).read()
  if member.name in expected:assert hashlib.sha256(data).hexdigest()==expected[member.name]
  with target.open('xb') as output:output.write(data);output.flush();os.fsync(output.fileno())
  target.chmod(0o755 if member.name.startswith('bin/') else 0o600)
checks={}
for label,args in [('rollout',['-m','unittest','test_rollout','test_prior_rollout']),('client_publisher',['-m','unittest','discover','-s','client','-p','test_publish.py'])]:
 p=subprocess.run(['python3','-B',*args],cwd=stage,capture_output=True,text=True,timeout=180)
 (stage/(label+'-linux.log')).write_text(p.stdout+'\\n'+p.stderr)
 assert p.returncode==0,p.stderr[-2500:]
 checks[label]=p.stderr.strip().splitlines()[-1]
out={'status':'STAGED_LINUX_TESTS_PASS','manifest_sha256':hashlib.sha256((stage/'manifest.json').read_bytes()).hexdigest(),'checks':checks,'runtime_changed':False}
(stage/'linux-tests.json').write_text(json.dumps(out,indent=2)+'\\n')
print(json.dumps(out))
''',timeout=400)
    save(HERE/'staged.json',result);print(json.dumps(result,indent=2))


if __name__=='__main__':main()
