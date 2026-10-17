"""Publish only the reviewed signed game channel; never change client assets."""
import base64, hashlib, json, os, subprocess, sys
from pathlib import Path
from urllib.parse import urlsplit, unquote

PUBLIC = Path('/opt/nightcap/deploy/production/data/public')

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text())
def decode(p): return json.loads(base64.b64decode(load(p)['manifest']))
def services():
    result = {}
    for name in ('db','game','gateway','web','tunnel'):
        cid = subprocess.check_output(['docker','compose','ps','-q',name],cwd=PUBLIC.parent.parent,text=True).strip()
        d = json.loads(subprocess.check_output(['docker','inspect',cid],text=True))[0];s=d['State']
        result[name]={'id':cid,'image_id':d['Image'],'started_at':s['StartedAt'],'restarts':d['RestartCount'],
                      'running':s['Running'],'health':s.get('Health',{}).get('Status'),'oom_killed':s.get('OOMKilled',False)}
    return result

def validate(stage):
    baseline=load(stage/'baseline.json');receipt=load(stage/'signed-receipt.json')
    assert set(baseline['public'])=={'channel.json','launcher-channel.json','nightcap-friends.zip','guide.html'},'Incomplete public baseline'
    assert sha(stage/'channel.json')==receipt['channel_sha256']
    old=baseline['public']['channel.json']['signed'];new=decode(stage/'channel.json')
    assert old['release']==2026101501 and new['release']==2026101701
    assert new['patch_notes'][0]['release']==new['release'] and new['patch_notes'][1:]==old['patch_notes']
    assert {k:v for k,v in old.items() if k not in ('release','patch_notes')}=={k:v for k,v in new.items() if k not in ('release','patch_notes')}
    assert len(new['files'])==106
    for name,expected in baseline['public'].items():
        allowed={expected['sha256']}
        if name=='channel.json':allowed.add(receipt['channel_sha256'])
        assert sha(PUBLIC/name) in allowed,'Public drift: '+name
    for f in new['files']:
        u=urlsplit(f['url']);assert u.scheme=='https' and u.netloc=='play.nightcapgame.org' and not u.query and not u.fragment
        p=PUBLIC/unquote(u.path).lstrip('/')
        assert p.resolve().is_relative_to(PUBLIC.resolve()) and not p.is_symlink()
        assert p.stat().st_size==f['size'] and sha(p)==f['sha256'],'Asset drift: '+f['path']
    current=services();assert current==baseline['services'],'Service drift'
    assert all(s['running'] and not s['oom_killed'] for s in current.values())
    assert all(current[n]['health']=='healthy' for n in ('game','db'))
    return baseline,receipt

def sync_directory(p):
    fd=os.open(p,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)

def publish(stage):
    baseline,receipt=validate(stage)
    backup=stage/'previous-channel.json'
    if not backup.exists():
        assert sha(PUBLIC/'channel.json')==baseline['public']['channel.json']['sha256']
        with backup.open('xb') as f:f.write((PUBLIC/'channel.json').read_bytes());f.flush();os.fsync(f.fileno())
        sync_directory(stage)
    assert sha(backup)==baseline['public']['channel.json']['sha256']
    target=PUBLIC/'channel.json';assert not target.is_symlink()
    pending=PUBLIC/('.dungeon-notes-'+str(os.getpid())+'.pending')
    with pending.open('xb') as f:f.write((stage/'channel.json').read_bytes());f.flush();os.fsync(f.fileno())
    pending.chmod(0o644);assert sha(pending)==receipt['channel_sha256']
    validate(stage);os.replace(pending,target);sync_directory(PUBLIC);validate(stage)
    result={'release':2026101701,'channel_sha256':receipt['channel_sha256'],'assets_preserved':106,
            'services_unchanged':True,'desktop_starter_guide_unchanged':True,'patch_history_preserved':True}
    (stage/'published.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)

if __name__=='__main__':
    import fcntl
    assert __debug__
    stage=Path(sys.argv[1]);assert stage.resolve()==Path('/opt/nightcap/releases/dungeon-patcher-20261017')
    with (PUBLIC.parent.parent/'.deployment.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if sys.argv[2]=='stage':validate(stage);print('Notes stage verified; production unchanged',flush=True)
        elif sys.argv[2]=='publish':publish(stage)
        else:raise ValueError('stage or publish required')
