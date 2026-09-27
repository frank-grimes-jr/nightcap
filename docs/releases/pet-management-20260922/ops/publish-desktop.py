"""Publish only a verified automatic desktop update; preserve game and starter files."""
import hashlib,json,os,shutil
from pathlib import Path
STAGE=Path('/opt/nightcap/releases/pet-desktop-2026092701')
PUBLIC=Path('/opt/nightcap/deploy/production/data/public')
REL='launcher/2026092701'
OLD={'launcher-channel.json':'b81f97154e1b78f890b6cab3af95cbf59679ff8633ea1e8db2055baea2ab3963',
'channel.json':'48adafb8c2658e06b40cfdedef264e02f21733e001f2bddceb316d6599fe6250',
'nightcap-friends.zip':'bad2fd8d91c74c41e3be84c8e3a985159c1b2eb980c4fddce47780b2a310f452',
'guide.html':'c6160072c279b82c420f1c14122cb9bce2d9e5c6edb772db8d8d534ed3b4f675'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def inventory():
    m=json.loads((STAGE/'publication-files.json').read_text())
    assert set(m)=={'launcher-channel.json',REL+'/nightcap-desktop.exe'}
    for n,e in m.items():
        p=STAGE/n
        assert p.resolve().is_relative_to(STAGE.resolve()) and p.is_file()
        assert p.stat().st_size==e['size'] and sha(p)==e['sha256'],n
    return m

def unchanged(m):
    for n,h in OLD.items():
        allowed=(h,m[n]['sha256']) if n=='launcher-channel.json' else (h,)
        assert sha(PUBLIC/n) in allowed,'Public drift: '+n

def copy_verified(source,target,digest):
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.exists() and sha(target)==digest:return
    pending=target.with_name(target.name+'.pet-desktop-partial')
    shutil.copyfile(source,pending)
    assert sha(pending)==digest
    with pending.open('r+b') as f:os.fsync(f.fileno())
    pending.chmod(0o644);os.replace(pending,target)

def publish():
    m=inventory();unchanged(m)
    backup=STAGE/'previous-launcher-channel.json'
    if not backup.exists():
        assert sha(PUBLIC/'launcher-channel.json')==OLD['launcher-channel.json']
        with backup.open('xb') as f:
            f.write((PUBLIC/'launcher-channel.json').read_bytes());f.flush();os.fsync(f.fileno())
    assert sha(backup)==OLD['launcher-channel.json']
    digest=m[REL+'/nightcap-desktop.exe']['sha256'];target=PUBLIC/REL
    if not target.exists():
        pending=target.with_name('.'+target.name+'.pet-desktop-pending')
        pending.mkdir(parents=True,exist_ok=True)
        copy_verified(STAGE/REL/'nightcap-desktop.exe',pending/'nightcap-desktop.exe',digest)
        assert {p.name for p in pending.iterdir()}=={'nightcap-desktop.exe'}
        pending.chmod(0o755);os.replace(pending,target)
    assert {p.name for p in target.iterdir()}=={'nightcap-desktop.exe'}
    assert sha(target/'nightcap-desktop.exe')==digest
    unchanged(m)
    copy_verified(STAGE/'launcher-channel.json',PUBLIC/'launcher-channel.json',m['launcher-channel.json']['sha256'])
    unchanged(m)
    for n,e in m.items():assert sha(PUBLIC/n)==e['sha256']
    result={'launcher_release':2026092701,'version':'0.3.1','desktop_sha256':digest,
            'channel_sha256':m['launcher-channel.json']['sha256'],'game_starter_guide_unchanged':True}
    (STAGE/'published.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
    return result

if __name__=='__main__':
    if not __debug__:raise RuntimeError('Assertions required')
    publish()