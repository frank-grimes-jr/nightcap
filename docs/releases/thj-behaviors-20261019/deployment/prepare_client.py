"""Assemble immutable signed client assets; capture baseline only with access closed."""
import argparse
import base64
import hashlib
import json
import shutil
import sys
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

STAGE = Path('/opt/nightcap/releases/thj-behaviors-live-20261019/client')
PUBLIC = Path('/opt/nightcap/deploy/production/data/public')


def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def main(action):
    old_raw = (STAGE/'previous-channel.json').read_bytes()
    new_raw = (STAGE/'channel.json').read_bytes()
    old = json.loads(base64.b64decode(json.loads(old_raw)['manifest']))
    new = json.loads(base64.b64decode(json.loads(new_raw)['manifest']))
    assert old['release'] == 2026101901 and new['release'] == 2026101902
    assert len(old['files']) == len(new['files']) == 138
    assert new['patch_notes'][1:] == old['patch_notes']
    assert new['minimum_launcher'] == old['minimum_launcher'] == '0.6.0'
    assert new['tombstones'] == old['tombstones']
    changed = {'spells_us.txt','dbstr_us.txt'}
    previous = {f['path']:f for f in old['files']}
    assert set(previous) == {f['path'] for f in new['files']}
    assert sha(PUBLIC/'channel.json') == hashlib.sha256(old_raw).hexdigest()
    if action == 'assets':
        entries = {}
        for f in new['files']:
            name = f['path']; relative = PurePosixPath(name)
            assert not relative.is_absolute() and '..' not in relative.parts and '\\' not in name
            prior = previous[name]
            assert f['required'] == prior['required']
            assert f['url'] == 'https://play.nightcapgame.org/release/2026101902/'+name
            if name in changed:
                source = STAGE/'assets'/name
            else:
                assert all(f[k] == prior[k] for k in ('sha256','size'))
                url = urlsplit(prior['url'])
                assert url.scheme == 'https' and url.netloc == 'play.nightcapgame.org'
                part = PurePosixPath(url.path.lstrip('/'))
                assert '..' not in part.parts and part.parts[0] == 'release'
                source = PUBLIC/part
            assert source.is_file() and not source.is_symlink()
            assert source.stat().st_size == f['size'] and sha(source) == f['sha256'], name
            dest = STAGE/'release/2026101902'/name
            dest.parent.mkdir(parents=True,exist_ok=True); assert not dest.exists()
            shutil.copyfile(source,dest)
            entries['release/2026101902/'+name] = {k:f[k] for k in ('size','sha256')}
        entries['channel.json'] = {'size':len(new_raw),'sha256':hashlib.sha256(new_raw).hexdigest()}
        (STAGE/'publication-files.json').write_text(json.dumps(entries,indent=2)+'\n')
        (STAGE/'release-audit.json').write_text(json.dumps({'release':new['release'],'files':new['files'],
            'channel_sha256':entries['channel.json']['sha256'],'changed_assets':sorted(changed)},indent=2)+'\n')
        print('138 staged client assets verified; public channel unchanged.')
        return
    sys.path.insert(0,'/opt/nightcap/releases/zone-hunt-20261009')
    import runtime_ops as r
    closed = json.loads((STAGE.parent/'evidence/activated-closed.json').read_text())
    assert r.compact('game') == closed['game'] and not r.compact('gateway')['running']
    public = {p.name:{'sha256':sha(p)} for p in PUBLIC.iterdir() if p.is_file() and not p.is_symlink()}
    public['channel.json']['signed'] = {'release':old['release']}
    baseline = {'public':public,'services':{s:r.compact(s) for s in ('game','gateway','db','web','tunnel')},'paired_maintenance':True}
    with (STAGE/'baseline.json').open('x') as f:
        json.dump(baseline,f,indent=2)
    print('Closed-access publication baseline captured.')


if __name__ == '__main__':
    import fcntl
    parser = argparse.ArgumentParser(); parser.add_argument('action',choices=['assets','baseline'])
    args = parser.parse_args()
    with (PUBLIC.parent.parent/'.deployment.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB); main(args.action)
