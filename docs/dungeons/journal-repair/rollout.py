"""Zone-only journal repair using the pinned deployed dungeon operator's guards.

No SQL/content/quest mutation. Failures hold access; never restore player data.
"""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import time

STAGE=Path('/opt/nightcap/releases/dungeon-journal-20261016')
PREVIOUS=Path('/opt/nightcap/releases/dungeons-20261016/rollout.py')
d=r=q=None


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def manifest():
    m=json.loads((STAGE/'manifest.json').read_text())
    assert set(m['binaries'])=={'zone'} and m['binaries']['zone']=='023cb1e991de849860b1387c0a0d8db5c596fb2744e791d5a92fb9e32b6b83cd'
    assert sha(PREVIOUS)==m['dungeon_operator_sha256']
    assert sha(Path(r.__file__))==m['runtime_helper_sha256']
    assert sha(Path(q.__file__))==m['previous_operator_sha256']
    assert sha(Path(q.c.__file__))==m['previous_cache_helper_sha256']
    for name,digest in m['files'].items():
        relative=PurePosixPath(name)
        assert not relative.is_absolute() and '..' not in relative.parts and '\\' not in name
        path=STAGE/name
        assert path.resolve().is_relative_to(STAGE.resolve()) and not path.is_symlink() and sha(path)==digest,name
    assert m['files']['bin/zone']==m['binaries']['zone']
    q.signed_client_receipt(m)
    return m


def custom():
    result=q.extras()
    for table in ('completed_tasks','instance_list','instance_list_player','respawn_times'):
        value=d.sql('CHECKSUM TABLE `'+table+'` EXTENDED;').strip().split('\t')[-1]
        assert value.isdigit(),table
        result[table]=value
    return result


def preflight():
    m=manifest()
    assert not r.EVIDENCE.exists(),'Existing evidence; do not replay'
    services={name:r.compact(name) for name in ('game','gateway','db','web','tunnel')}
    old=services['game']
    assert old['running'] and old['health']=='healthy' and old['restarts']==m['baseline_restarts']
    assert services['gateway']['running']
    hashes=r.image_hashes(old['image_id'])
    assert {name:hashes['bin/'+name] for name in d.NAMES}==m['base_binaries']
    r.running(old['image_id'],m['base_binaries'],expected_restarts=old['restarts'])
    d.challenge_health();q.verify_publication(m);r.closed_ports()
    assert d.sql('SELECT revision,enabled FROM nightcap_dungeon_state;').strip()=='2026101601\t1'
    cache_path=r.ROOT/'data/server/shared/items'
    assert sha(cache_path)==m['cache_sha256']
    snapshot={'manifest_sha256':sha(STAGE/'manifest.json'),'old_image_id':old['image_id'],
              'old_hashes':hashes,'services':services,'runtime':r.runtime(),'public':r.public(),
              'content':d.content(),'policies':d.policies(),'cache_sha256':sha(cache_path)}
    tag='nightcap-game:dungeon-journal-base-20261016'
    r.call('docker','tag',old['image_id'],tag)
    (STAGE/'Dockerfile').write_text('FROM '+tag+'\nCOPY bin/zone /opt/nightcap/bin/zone\n')
    r.call('docker','build','--network','none','-t','nightcap-game:dungeon-journal-20261016',str(STAGE))
    image=r.out('docker','image','inspect','--format','{{.Id}}','nightcap-game:dungeon-journal-20261016').strip()
    snapshot['new_image_id']=image
    assert r.image_hashes(image)==d.expected_image(snapshot),'Unrelated image change'
    layers=lambda x:json.loads(r.out('docker','image','inspect',x))[0]['RootFS']['Layers']
    before,after=layers(old['image_id']),layers(image)
    assert after[:len(before)]==before and len(after)==len(before)+1
    assert 'not found' not in r.out('docker','run','--rm','--network','none','--entrypoint','ldd',image,'/opt/nightcap/bin/zone')
    r.call('docker','run','--rm','--network','none','--entrypoint','python3',image,'-c',"import sys;sys.path.insert(0,'/opt/nightcap');import start;start.validate_native()")
    r.call('docker','run','--rm','--network','none','--entrypoint','/opt/nightcap/bin/loginserver',image,'--nightcap-crypto-self-test')
    d.unchanged(snapshot)
    assert r.compact('game')==services['game'] and r.compact('gateway')==services['gateway']
    r.EVIDENCE.mkdir(mode=0o700)
    d.save('preflight.json',snapshot)
    print('Journal preflight passed; game access remains unchanged.',flush=True)


def activate():
    m,p=manifest(),d.load('preflight.json')
    assert p['manifest_sha256']==sha(STAGE/'manifest.json')
    assert not (r.EVIDENCE/'activation-started.json').exists(),'Activation already attempted'
    assert r.compact('game')==p['services']['game'] and r.compact('gateway')==p['services']['gateway']
    d.unchanged(p)
    assert r.image_hashes(p['new_image_id'])==d.expected_image(p)
    d.save('activation-started.json',{'authorized':True,'database_restored':False})
    try:
        r.compose('stop','gateway')
        start=time.monotonic()
        r.compose('stop','-t','90','game');q.stopped()
        d.save('shutdown.json',{'duration_seconds':time.monotonic()-start,'native_flush_confirmed':False})
        data={'player':r.player_data(),'custom':d.custom()}
        d.save('stopped-data.json',data)
        backup=r.database_backup();d.save('backup.json',backup)
        q.select(p['new_image_id'])
        r.compose('up','-d','--wait','--wait-timeout','240','game')
        d.challenge_health()
        first=r.running(p['new_image_id'],d.binaries(p),expected_restarts=0)
        cache_path=r.ROOT/'data/server/shared/items'
        assert sha(cache_path)==p['cache_sha256'],'Regenerated cache differs from reviewed current-content pair'
        time.sleep(16);d.challenge_health()
        result=r.running(p['new_image_id'],d.binaries(p),expected_restarts=0)
        assert result['started_at']==first['started_at']
        assert d.sql('SELECT revision,enabled FROM nightcap_dungeon_state;').strip()=='2026101601\t1'
        d.preserved(data);d.unchanged(p,True);q.verify_publication(m)
        assert not r.state('gateway')['State']['Running']
        d.save('activated-closed.json',{'runtime':result,'game':r.compact('game'),
            'cache':{'all_bytes_preserved':True},'cache_sha256':sha(cache_path),'gateway_open':False,
            'backup':backup,'player_tables_preserved':len(data['player']),'custom_tables_preserved':len(data['custom'])})
        print('Journal candidate active; access held for final checks.',flush=True)
    except BaseException:
        d.hold('Journal activation failed; preserve current data and image for reconciliation')
        raise


def initialize():
    global d,r,q
    # Authenticate executable dependencies before importing them.
    m=json.loads((STAGE/'manifest.json').read_text())
    assert sha(PREVIOUS)==m['dungeon_operator_sha256']
    spec=importlib.util.spec_from_file_location('dungeon_previous',PREVIOUS)
    d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
    r,q=d.r,d.q
    d.STAGE=q.STAGE=r.STAGE=STAGE;r.EVIDENCE=STAGE/'evidence'
    d.manifest=manifest
    # The original additive release excluded its new tables; this repair must
    # preserve every current dungeon ledger/content row as well as old systems.
    d.custom=custom


if __name__=='__main__':
    assert __debug__
    os.umask(0o077);initialize()
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['preflight','activate','open','report'])
    action=parser.parse_args().action
    with (r.ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm_lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        q.require_no_gm_work()
        {'preflight':preflight,'activate':activate,'open':d.open_access,'report':d.report}[action]()
