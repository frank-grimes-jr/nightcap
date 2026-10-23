"""Install the reviewed loot reader and narrow JSON route after owner approval.

Requires an exact nginx preimage and a healthy existing wiki. Uses its shared
publisher lock, rehearses the configuration inverse, and starts the timer last.
An interrupted/failed installation retains private receipts and generated data.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import time
import deploy
from loot_refresh import locked, read_payload

SOURCE=Path(__file__).resolve().parent
INSTALL=Path('/opt/nightcap/wiki-loot')
UNITS=Path('/etc/systemd/system')
SCRIPTS=['loot_capture.py','loot_model.py','loot_refresh.py']
NAMES=['nightcap-wiki-loot.service','nightcap-wiki-loot.timer']


def candidate_config(before, fragment):
    anchor=b'server_name wiki.nightcapgame.org;'
    if before.count(anchor)!=1 or b'/loot-data/' in before:
        raise ValueError('Expected one existing wiki host and no loot data route')
    if b'alias /srv/public/wiki-data/$1;' not in fragment:
        raise ValueError('Unexpected public data root')
    return before.replace(anchor,anchor+b'\n'+fragment,1)


def systemctl(*args):
    subprocess.run(['systemctl',*args],check=True,timeout=660,capture_output=True,text=True)


def require_absent_units():
    for directory in ['/etc/systemd/system','/run/systemd/system','/usr/local/lib/systemd/system','/usr/lib/systemd/system','/lib/systemd/system']:
        for name in NAMES:
            for path in [Path(directory)/name,Path(directory)/(name+'.d')]:
                if path.exists() or path.is_symlink():raise ValueError('Preexisting unit or overrides: '+str(path))
    state=deploy.command('systemctl','show','--property=LoadState,FragmentPath,DropInPaths,UnitFileState',*NAMES)
    lines=[line for line in state.splitlines() if line]
    if lines.count('LoadState=not-found')!=2 or any(line not in ['LoadState=not-found','FragmentPath=','DropInPaths=','UnitFileState='] for line in lines):
        raise ValueError('Effective systemd units already exist')


def verify_owned(owned):
    for name,digest in owned.items():
        path=Path(name)
        if path.is_symlink() or not path.is_file() or deploy.sha(path.read_bytes())!=digest:
            raise RuntimeError('Installed files changed; do not alter a later installation: '+name)
    for name in NAMES:
        if str(UNITS/name) not in owned:continue
        for directory in ['/etc/systemd/system','/run/systemd/system','/usr/local/lib/systemd/system','/usr/lib/systemd/system','/lib/systemd/system']:
            override=Path(directory)/(name+'.d')
            if override.exists() or override.is_symlink():raise RuntimeError('Later unit overrides require manual recovery')
        state=dict(line.split('=',1) for line in deploy.command('systemctl','show','--property=FragmentPath,DropInPaths',name).splitlines() if '=' in line)
        if state.get('DropInPaths')!='' or state.get('FragmentPath') not in ('',str(UNITS/name)):
            raise RuntimeError('Effective unit changed; do not alter a later installation')


def guard_config(expected):
    if (deploy.BASE/'nginx.conf').read_bytes()!=expected:
        raise RuntimeError('Web configuration changed; refusing to overwrite it')


def verify_data(index, enabled=True):
    expected=(200,deploy.sha(index)) if enabled else None
    for attempt in range(40):
        status,digest,headers=deploy.probe(deploy.HOST,'/loot-data/current/index.json')
        if ((status,digest)==expected if enabled else status==404):break
        time.sleep(.25)
    else:raise RuntimeError('Data route reload did not reach the expected state')
    if not enabled:
        if status!=404:raise RuntimeError('Data route rollback failed')
        return
    if status!=200 or digest!=deploy.sha(index):raise RuntimeError('Public data bytes differ')
    if headers.get('X-Content-Type-Options')!='nosniff':raise RuntimeError('Missing JSON security header')
    data=json.loads(index)
    name=f"{data['base_url']}item-{data['items'][0]['id']}.json"
    path=deploy.BASE/'data/public/wiki-data'/data['snapshot']/f"item-{data['items'][0]['id']}.json"
    if deploy.probe(deploy.HOST,name)[:2]!=(200,deploy.sha(read_payload(path))):
        raise RuntimeError('Item details do not match the index snapshot')
    for bad in ['/loot-data/current/item-1.json','/loot-data/current/.manifest.json',
                '/loot-data/current/content.json.gz','/loot-data/../nginx.conf']:
        if deploy.probe(deploy.HOST,bad)[0] not in (400,404):raise RuntimeError('Nonpublic path exposed')
    if deploy.probe(deploy.HOST,'/loot-data/current/index.json','POST')[0] not in (403,405):
        raise RuntimeError('Data route accepts writes')
    if deploy.probe('play.nightcapgame.org','/loot-data/current/index.json')[0]!=404:
        raise RuntimeError('Data route exposed on private host')


def cleanup_owned(owned):
    # Never delete changed files or directories from a later operator's install.
    for name,digest in owned.items():
        path=Path(name)
        if path.exists():
            if path.is_symlink() or deploy.sha(path.read_bytes())!=digest:
                raise RuntimeError('Installed file changed; manual recovery required: '+name)
            path.unlink()
    if INSTALL.exists() and not any(INSTALL.iterdir()):INSTALL.rmdir()
    systemctl('daemon-reload')


def install(args):
    config=deploy.BASE/'nginx.conf';before=config.read_bytes()
    if deploy.sha(before)!=args.expected_config_sha:raise ValueError('Stale nginx preimage')
    after=candidate_config(before,(SOURCE/'loot-nginx.conf').read_bytes())
    if INSTALL.exists() or INSTALL.is_symlink() or any((UNITS/name).exists() or (UNITS/name).is_symlink() for name in NAMES):
        raise ValueError('Reader already exists; use a reviewed update procedure')
    require_absent_units()
    manifest=json.loads(args.wiki_manifest.read_text());deploy.verify(manifest)
    services,protected=deploy.services(),deploy.protected()
    if len(services)!=5 or any(status!=200 for status,digest in protected.values()):
        raise RuntimeError('Production baseline is not healthy')
    receipt=deploy.BASE/'website-history'/args.receipt
    receipt.mkdir(exist_ok=False)
    (receipt/'nginx.before.conf').write_bytes(before);(receipt/'nginx.after.conf').write_bytes(after)
    (receipt/'baseline.json').write_text(json.dumps({'services':services,'protected':protected,'manifest':manifest},indent=2)+'\n')
    owned={};activated=False
    def preserved():
        if deploy.services()!=services or deploy.protected()!=protected:
            raise RuntimeError('Private resources or game service identities changed')
        deploy.verify(manifest)
    try:
        INSTALL.mkdir(mode=0o755)
        for name in SCRIPTS+NAMES:
            target=(INSTALL if name in SCRIPTS else UNITS)/name
            body=(SOURCE/name).read_bytes()
            with target.open('xb') as handle:handle.write(body)
            target.chmod(0o644);owned[str(target)]=deploy.sha(body)
            (receipt/'installed.json').write_text(json.dumps(owned,indent=2)+'\n')
        systemctl('daemon-reload')
        started=datetime.now(timezone.utc)
        systemctl('start',NAMES[0]) # verifies the actual unit sandbox and captures once
        index_path=deploy.BASE/'data/public/wiki-data/current/index.json'
        index=read_payload(index_path)
        if datetime.fromisoformat(json.loads(index)['captured_at'])<started:
            raise RuntimeError('Service did not produce a fresh capture')
        guard_config(before);config.write_bytes(after);activated=True;deploy.reload_web()
        verify_data(index);preserved()
        guard_config(after);config.write_bytes(before);deploy.reload_web()
        verify_data(index,False);preserved()
        guard_config(before);config.write_bytes(after);deploy.reload_web()
        verify_data(index);preserved()
        systemctl('enable','--now',NAMES[1])
        systemctl('is-active','--quiet',NAMES[1])
        result={'result':'PASS','config_sha256':deploy.sha(after),'snapshot':json.loads(index)['snapshot'],
            'rollback_rehearsed':True,'timer_minutes':15,'service_ids_preserved':True,'private_downloads_preserved':True}
        (receipt/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
        return result
    except BaseException as failure:
        try:
            # These unit names were proven absent before this install.
            verify_owned(owned)
            stop_errors=[]
            if str(UNITS/NAMES[1]) in owned:
                try:systemctl('disable','--now',NAMES[1])
                except Exception as error:stop_errors.append(str(error))
            if str(UNITS/NAMES[0]) in owned:
                try:systemctl('stop',NAMES[0])
                except Exception as error:stop_errors.append(str(error))
            current=config.read_bytes()
            if current==after:config.write_bytes(before);deploy.reload_web()
            elif current!=before:raise RuntimeError('Concurrent config preserved; manual inverse required')
            elif activated:deploy.reload_web()
            verify_data(b'',False)
            if not stop_errors:cleanup_owned(owned)
            preserved()
            if stop_errors:raise RuntimeError('Owned unit stop failed; files retained: '+'; '.join(stop_errors))
        except BaseException as recovery:
            raise RuntimeError('Installation failed; recovery needs attention: '+str(recovery)) from failure
        raise


def rollback(receipt):
    before=(receipt/'nginx.before.conf').read_bytes();after=(receipt/'nginx.after.conf').read_bytes()
    owned=json.loads((receipt/'installed.json').read_text())
    guard_config(after)
    verify_owned(owned)
    services,protected=deploy.services(),deploy.protected()
    systemctl('disable','--now',NAMES[1]);systemctl('stop',NAMES[0])
    guard_config(after);(deploy.BASE/'nginx.conf').write_bytes(before);deploy.reload_web()
    verify_data(b'',False)
    if deploy.services()!=services or deploy.protected()!=protected:raise RuntimeError('Recovery preservation failed')
    cleanup_owned(owned)
    return {'result':'ROLLED BACK','config_sha256':deploy.sha(before),'data_retained':True}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-config-sha')
    parser.add_argument('--wiki-manifest',type=Path)
    parser.add_argument('--receipt',default='20261022-wiki-loot-reader-v1')
    parser.add_argument('--rollback',type=Path)
    args=parser.parse_args()
    if '/' in args.receipt or '\\' in args.receipt or args.receipt in ('.','..'):parser.error('Invalid receipt name')
    if not args.rollback and (not args.expected_config_sha or not args.wiki_manifest):parser.error('Missing preimage or wiki manifest')
    with locked(deploy.BASE/'website-history/.lock'):
        print(json.dumps(rollback(args.rollback) if args.rollback else install(args),indent=2))
