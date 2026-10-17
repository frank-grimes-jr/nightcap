"""Prepare immutable client assets; capture publication baseline only during paired maintenance."""
import argparse,base64,hashlib,json,shutil,sys
from pathlib import Path,PurePosixPath
from urllib.parse import urlsplit

STAGE=Path('/opt/nightcap/releases/october-17-2026/client')
PUBLIC=Path('/opt/nightcap/deploy/production/data/public')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main(action):
    old_raw=(STAGE/'previous-channel.json').read_bytes();new_raw=(STAGE/'channel.json').read_bytes()
    old=json.loads(base64.b64decode(json.loads(old_raw)['manifest']));new=json.loads(base64.b64decode(json.loads(new_raw)['manifest']))
    assert old['release']==2026101701 and new['release']==2026101702 and len(old['files'])==len(new['files'])==106
    assert new['patch_notes'][1:]==old['patch_notes'] and new['minimum_launcher']==old['minimum_launcher']=='0.6.0'
    assert new['tombstones']==old['tombstones']
    changed={'dinput8.dll','nightcap-patch-sites.json','uifiles/nightcap/equi_aawindow.xml'}
    entries={};previous={f['path']:f for f in old['files']}
    if action=='assets':
        assert sha(PUBLIC/'channel.json')==hashlib.sha256(old_raw).hexdigest()
        for f in new['files']:
            n=f['path'];rel=PurePosixPath(n);assert not rel.is_absolute() and '..' not in rel.parts and '\\' not in n
            prior=previous[n];assert f['required']==prior['required'] and f['url']=='https://play.nightcapgame.org/release/2026101702/'+n
            if n in changed:source=STAGE/'assets'/n
            else:
                assert {k:f[k] for k in ('sha256','size')}=={k:prior[k] for k in ('sha256','size')}
                url=urlsplit(prior['url']);assert url.scheme=='https' and url.netloc=='play.nightcapgame.org'
                relative=PurePosixPath(url.path.lstrip('/'));assert '..' not in relative.parts and relative.parts[0]=='release'
                source=PUBLIC/relative
            assert source.is_file() and not source.is_symlink() and source.stat().st_size==f['size'] and sha(source)==f['sha256'],n
            dest=STAGE/'release/2026101702'/n;dest.parent.mkdir(parents=True,exist_ok=True);assert not dest.exists();shutil.copyfile(source,dest)
            entries['release/2026101702/'+n]={k:f[k] for k in ('size','sha256')}
        entries['channel.json']={'size':len(new_raw),'sha256':hashlib.sha256(new_raw).hexdigest()}
        (STAGE/'publication-files.json').write_text(json.dumps(entries,indent=2)+'\n')
        (STAGE/'release-audit.json').write_text(json.dumps({'release':new['release'],'files':new['files'],'channel_sha256':entries['channel.json']['sha256'],'changed_assets':sorted(changed)},indent=2)+'\n')
        print('106 staged assets verified; channel unchanged.');return
    sys.path.insert(0,'/opt/nightcap/releases/zone-hunt-20261009');import runtime_ops as r
    closed=json.loads((STAGE.parent/'evidence/activated-closed.json').read_text())
    assert r.compact('game')==closed['game'] and not r.compact('gateway')['running']
    assert sha(PUBLIC/'channel.json')==hashlib.sha256(old_raw).hexdigest()
    public={n:{'sha256':h} for n,h in r.public().items()};public['channel.json']['signed']={'release':old['release']}
    baseline={'public':public,'services':{s:r.compact(s) for s in ('game','gateway','db','web','tunnel')},'paired_maintenance':True}
    with (STAGE/'baseline.json').open('x') as f:json.dump(baseline,f,indent=2)
    print('Closed-access paired publication baseline captured.')
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['assets','baseline']);main(p.parse_args().action)
