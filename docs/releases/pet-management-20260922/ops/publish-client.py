"""Publish the signed pet client channel after its matching server activation."""
import argparse,hashlib,json,os,shutil,subprocess
from pathlib import Path,PurePosixPath
STAGE=Path('/opt/nightcap/releases/pet-client-2026092201')
PUBLIC=Path('/opt/nightcap/deploy/production/data/public')
ACTIVATION=Path('/opt/nightcap/releases/pet-management-evidence-20260922/activated.json')
OLD={'channel.json':'6e5d2b95d3ac9be29949bb839153aeb0040d43e6013c56ad3e069c8216f0e23d',
'launcher-channel.json':'b81f97154e1b78f890b6cab3af95cbf59679ff8633ea1e8db2055baea2ab3963',
'nightcap-friends.zip':'bad2fd8d91c74c41e3be84c8e3a985159c1b2eb980c4fddce47780b2a310f452',
'guide.html':'c6160072c279b82c420f1c14122cb9bce2d9e5c6edb772db8d8d534ed3b4f675'}
RELEASE='release/2026092201'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def inventory():
    m=json.loads((STAGE/'publication-files.json').read_text())
    assert len(m)==24 and set(m)-{'channel.json'}=={RELEASE+'/'+f['path'] for f in json.loads((STAGE/'release-audit.json').read_text())['files']}
    for n,e in m.items():
        relative=PurePosixPath(n)
        assert not relative.is_absolute() and '..' not in relative.parts and '\\' not in n and relative.as_posix()==n,'Unsafe publication path'
        p=STAGE/n
        assert p.resolve().is_relative_to(STAGE.resolve()) and p.is_file()
        assert p.stat().st_size==e['size'] and sha(p)==e['sha256'],n
    assert sha(STAGE/'channel.json')==json.loads((STAGE/'release-audit.json').read_text())['channel_sha256']
    return m

def live_server(activation):
    root=PUBLIC.parent.parent
    def state(service):
        cid=subprocess.check_output(['docker','compose','ps','-aq',service],cwd=root,text=True,timeout=30).strip()
        assert cid,'Missing live '+service
        return json.loads(subprocess.check_output(['docker','inspect',cid],cwd=root,text=True,timeout=30))[0]
    game=state('game');current=game['State']
    assert game['Image']==activation['image_id'] and game['RestartCount']==0,'Matching server image is no longer active'
    assert current['Running'] and not current.get('OOMKilled',False) and current['Health']['Status']=='healthy','Matching server is unhealthy'
    assert current['StartedAt']==activation['started_at'],'Server restarted after native validation'
    assert state('gateway')['State']['Running'],'Gateway is closed'

def public_unchanged(m):
    for n,h in OLD.items():
        allowed=(h,m[n]['sha256']) if n=='channel.json' else (h,)
        assert sha(PUBLIC/n) in allowed,'Public drift: '+n

def copy_verified(source,target,digest):
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists() and sha(target)==digest:return
    temp=target.with_name(target.name+'.pet-partial')
    shutil.copyfile(source,temp)
    assert sha(temp)==digest
    with temp.open('r+b') as f:os.fsync(f.fileno())
    temp.chmod(0o644);os.replace(temp,target)

def publish():
    m=inventory()
    activation=json.loads(ACTIVATION.read_text())
    assert activation['native_processes']==15 and activation['restart_count']==0 and not any(activation['errors'].values())
    live_server(activation);public_unchanged(m)
    backup=STAGE/'previous-channel.json'
    if not backup.exists():
        assert sha(PUBLIC/'channel.json')==OLD['channel.json']
        with backup.open('xb') as f:f.write((PUBLIC/'channel.json').read_bytes());f.flush();os.fsync(f.fileno())
    assert sha(backup)==OLD['channel.json']
    target=PUBLIC/RELEASE
    entries={n[len(RELEASE)+1:]:e for n,e in m.items() if n.startswith(RELEASE+'/')}
    if not target.exists():
        pending=target.with_name('.'+target.name+'.pet-pending');pending.mkdir(parents=True,exist_ok=True)
        for n,e in entries.items():copy_verified(STAGE/RELEASE/n,pending/n,e['sha256'])
        assert {p.relative_to(pending).as_posix() for p in pending.rglob('*') if p.is_file()}==set(entries)
        for p in [pending,*pending.rglob('*')]:p.chmod(0o755 if p.is_dir() else 0o644)
        os.replace(pending,target)
    assert {p.relative_to(target).as_posix() for p in target.rglob('*') if p.is_file()}==set(entries)
    for n,e in entries.items():assert sha(target/n)==e['sha256']
    # The only public mutable pointer changes after all immutable assets verify.
    live_server(activation);public_unchanged(m)
    copy_verified(STAGE/'channel.json',PUBLIC/'channel.json',m['channel.json']['sha256'])
    for n,e in m.items():assert sha(PUBLIC/n)==e['sha256']
    for n,h in OLD.items():
        if n!='channel.json':assert sha(PUBLIC/n)==h
    result={'release':2026092201,'verified_files':23,'channel_sha256':m['channel.json']['sha256'],'launcher_unchanged':True}
    (STAGE/'published.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':
    if not __debug__:raise RuntimeError('Assertions required')
    p=argparse.ArgumentParser();p.add_argument('action',choices=['stage','publish']);a=p.parse_args()
    if a.action=='stage':print(json.dumps({'staged_files':len(inventory()),'production_unchanged':True}))
    else:publish()
