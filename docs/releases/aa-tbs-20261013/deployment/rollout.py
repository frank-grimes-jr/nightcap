"""Owner-authorized zone-only release; retain all data and prior immutable image."""
import argparse,fcntl,hashlib,json,os,sys,time
from pathlib import Path

STAGE=Path('/opt/nightcap/releases/aa-tbs-20261013')
sys.path.insert(0,'/opt/nightcap/releases/zone-hunt-20261009')
import runtime_ops as r
import aa_preflight
r.STAGE=STAGE
r.EVIDENCE=STAGE/'evidence'
ROOT=r.ROOT

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,value):
    with (r.EVIDENCE/name).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
def load(name):return json.loads((r.EVIDENCE/name).read_text())
def manifest():
    m=json.loads((STAGE/'manifest.json').read_text())
    assert sha(Path(r.__file__))==m['runtime_helper_sha256'],'Runtime helper drift'
    for n,h in m['files'].items():
        p=STAGE/n
        assert p.resolve().is_relative_to(STAGE) and not p.is_symlink() and sha(p)==h,n
    return m
def policies():
    return r.sql("SELECT ruleset_id,rule_name,rule_value FROM rule_values ORDER BY ruleset_id,rule_name;")
def extras():
    tables=r.sql("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA='peq' AND TABLE_NAME LIKE 'nightcap\\_%' AND TABLE_NAME NOT IN ('nightcap_market_offers','nightcap_market_state') ORDER BY TABLE_NAME;").splitlines()
    assert all(n.replace('_','').isalnum() for n in tables)
    result={n:r.sql('CHECKSUM TABLE `'+n+'` EXTENDED;').strip().split('\t')[-1] for n in tables}
    assert all(v.isdigit() for v in result.values())
    return result
def select(image):
    p=ROOT/'.env';raw=p.read_text();lines=raw.splitlines()
    assert sum(x.startswith('NIGHTCAP_GAME_IMAGE=') for x in lines)==1
    data='\n'.join('NIGHTCAP_GAME_IMAGE='+image if x.startswith('NIGHTCAP_GAME_IMAGE=') else x for x in lines)+'\n'
    temp=p.with_name('.env.aa-tbs-'+str(time.time_ns()));st=p.stat()
    with temp.open('x') as f:f.write(data);f.flush();os.fsync(f.fileno())
    os.chmod(temp,st.st_mode & 0o777);os.chown(temp,st.st_uid,st.st_gid);os.replace(temp,p)
def validate_image(image):
    libraries=r.out('docker','run','--rm','--network','none','--entrypoint','ldd',image,'/opt/nightcap/bin/zone')
    assert 'not found' not in libraries,'Missing zone runtime library'
    r.call('docker','run','--rm','--network','none','--entrypoint','python3',image,'-c',"import sys;sys.path.insert(0,'/opt/nightcap');import start;start.validate_native()")
    r.call('docker','run','--rm','--network','none','--entrypoint','/opt/nightcap/bin/loginserver',image,'--nightcap-crypto-self-test')
def preflight():
    m=manifest();assert not r.EVIDENCE.exists()
    aa=aa_preflight.check(r.sql)
    old=r.compact('game');assert old['running'] and old['health']=='healthy'
    hashes=r.image_hashes(old['image_id'])
    assert {n:hashes['bin/'+n] for n in m['base_binaries']}==m['base_binaries'],'Deployed baseline differs'
    r.running(old['image_id'],m['base_binaries'],expected_restarts=old['restarts'])
    services={n:r.compact(n) for n in ('game','gateway','db','web','tunnel')}
    assert services['gateway']['running']
    r.closed_ports()
    tag='nightcap-game:aa-tbs-base-20261013'
    r.call('docker','tag',old['image_id'],tag)
    assert r.out('docker','image','inspect','--format','{{.Id}}',tag).strip()==old['image_id']
    (STAGE/'Dockerfile').write_text('FROM '+tag+'\nCOPY zone /opt/nightcap/bin/zone\n')
    r.call('docker','build','--network','none','-t','nightcap-game:aa-tbs-20261013',str(STAGE))
    new=r.out('docker','image','inspect','--format','{{.Id}}','nightcap-game:aa-tbs-20261013').strip()
    expected={**hashes,'bin/zone':m['binaries']['zone']}
    assert r.image_hashes(new)==expected
    layers=lambda image:json.loads(r.out('docker','image','inspect',image))[0]['RootFS']['Layers']
    before,after=layers(old['image_id']),layers(new)
    assert after[:len(before)]==before and len(after)==len(before)+1
    validate_image(new);validate_image(old['image_id'])
    r.EVIDENCE.mkdir(mode=0o700)
    backup=r.database_backup()
    snapshot={'manifest_sha256':sha(STAGE/'manifest.json'),'old_image_id':old['image_id'],'new_image_id':new,
              'old_hashes':hashes,'services':services,'runtime':r.runtime(),'public':r.public(),
              'content':r.content_data(),'policies':policies(),'backup':backup,'aa_preflight':aa}
    save('preflight.json',snapshot)
    print(json.dumps({'status':'preflight_passed','new_image_id':new,'old_image_id':old['image_id'],'backup_verified':True}),flush=True)
def activate():
    m=manifest();p=load('preflight.json')
    assert p['manifest_sha256']==sha(STAGE/'manifest.json')
    assert r.compact('game')==p['services']['game'] and r.compact('gateway')==p['services']['gateway']
    assert r.image_hashes(p['new_image_id'])=={**p['old_hashes'],'bin/zone':m['binaries']['zone']}
    r.untouched(p);r.closed_ports();assert policies()==p['policies'] and r.content_data()==p['content']
    assert aa_preflight.check(r.sql)['catalog_sha256']==p['aa_preflight']['catalog_sha256']
    player=None;custom=None;access_may_have_opened=False
    try:
        r.compose('stop','gateway');r.compose('stop','-t','90','game')
        old=r.state('game')['State']
        assert not r.state('gateway')['State']['Running'] and not old['Running'] and old['ExitCode']==0 and not old.get('OOMKilled')
        player=r.player_data();custom=extras();save('stopped-data.json',{'player':player,'custom':custom})
        select(p['new_image_id']);r.compose('up','-d','--wait','--wait-timeout','240','game')
        first=r.running(p['new_image_id'],m['binaries']);time.sleep(5)
        result=r.running(p['new_image_id'],m['binaries'])
        assert result['started_at']==first['started_at']
        assert r.player_data()==player and extras()==custom,'Persisted data drift while gateway closed'
        assert aa_preflight.check(r.sql)['catalog_sha256']==p['aa_preflight']['catalog_sha256']
        assert policies()==p['policies'] and r.content_data()==p['content'];r.untouched(p)
        save('verified-closed.json',result)
        access_may_have_opened=True
        r.compose('up','-d','--wait','--wait-timeout','60','gateway')
        assert r.state('gateway')['State']['Running'];r.closed_ports()
        result=r.running(p['new_image_id'],m['binaries']);r.untouched(p)
        save('activated.json',{'runtime':result,'gateway_open':True,'player_tables_preserved':len(player),
                               'custom_tables_preserved':len(custom),'database_restored':False,'backup':p['backup']})
        print(json.dumps({'status':'activated','zone_sha256':m['binaries']['zone'],'zones':12,'gateway_open':True}),flush=True)
    except BaseException:
        r.compose('stop','gateway');r.compose('stop','-t','90','game')
        assert not r.state('gateway')['State']['Running'] and not r.state('game')['State']['Running']
        assert r.image_hashes(p['old_image_id'])==p['old_hashes']
        select(p['old_image_id']);r.compose('up','-d','--wait','--wait-timeout','240','game')
        r.running(p['old_image_id'],m['base_binaries'])
        # Keep all current character, loot receipt and world state. Never restore SQL.
        if player is not None and not access_may_have_opened:
            if r.player_data()!=player or extras()!=custom:
                save('recovery-held.json',{'old_image_id':p['old_image_id'],'database_restored':False,'gateway_open':False,'reason':'Persisted data drift remains after image rollback'})
                raise RuntimeError('Persisted data drift remains; gateway held closed')
        assert policies()==p['policies'] and r.content_data()==p['content'];r.untouched(p)
        assert aa_preflight.check(r.sql)['catalog_sha256']==p['aa_preflight']['catalog_sha256']
        r.compose('up','-d','--wait','--wait-timeout','60','gateway')
        save('rolled-back.json',{'old_image_id':p['old_image_id'],'database_restored':False,'gateway_open':True})
        raise
def report():
    m=manifest();p=load('preflight.json');a=load('activated.json')
    result=r.running(p['new_image_id'],m['binaries'])
    assert result['started_at']==a['runtime']['started_at']
    assert r.compact('gateway')['running'] and policies()==p['policies'];r.untouched(p);r.closed_ports()
    assert aa_preflight.check(r.sql)['catalog_sha256']==p['aa_preflight']['catalog_sha256']
    print(json.dumps({'status':'healthy','runtime':result,'gateway_open':True,'player_tables_preserved':a['player_tables_preserved'],
                     'custom_tables_preserved':a['custom_tables_preserved']}),flush=True)
def require_no_gm_work():
    assert not (ROOT/'private/gm-maintenance.json').exists(),'GM maintenance is active'
    assert r.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1','GM SQL action in flight'

if __name__=='__main__':
    os.umask(0o077)
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['preflight','activate','report']);args=parser.parse_args()
    with (ROOT/'.deployment.lock').open('a') as lock, open('/var/lock/nightcap-gm.lock','a') as gm_lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        fcntl.flock(gm_lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        require_no_gm_work()
        globals()[args.action]()
