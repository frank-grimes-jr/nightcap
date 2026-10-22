"""Scoped Hate Keeper activation. Run only after main/live approval.

Retains audited runtime, backup, startup-expiry and market reconciliation helpers.
Never restores player snapshots. Failure holds the game and gateway for recovery.
"""
import argparse,fcntl,hashlib,importlib.util,json,os,shutil,sys,time
from pathlib import Path
ROOT=Path('/opt/nightcap/deploy/production')
STAGE=Path('/opt/nightcap/releases/hate-keeper-commonlands-20261022')
PRIOR=Path('/opt/nightcap/releases/classic-dungeons-rewards-20261022/rollout.py')
EVIDENCE=STAGE/'evidence'
sys.path.insert(0,str(STAGE/'tools'))
import hate_keeper

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(name):return json.loads((EVIDENCE/name).read_text())
def manifest():
    m=json.loads((STAGE/'manifest.json').read_text())
    assert sha(PRIOR)==m['prior_operator_sha256']
    for name,digest in m['files'].items():
        path=STAGE/name
        assert path.resolve().is_relative_to(STAGE) and not path.is_symlink() and sha(path)==digest,name
    return m
def initialize():
    global old,r,sql,save
    manifest()
    spec=importlib.util.spec_from_file_location('retained_keeper_ops',PRIOR)
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    old.initialize() # Validates the retained release and helper before reuse.
    r=old.r;sql=old.sql
    old.STAGE=r.STAGE=STAGE;old.EVIDENCE=r.EVIDENCE=EVIDENCE
    save=old.save
def normalized(snapshot):return {t:sorted(json.dumps(row,sort_keys=True) for row in rows) for t,rows in snapshot['rows'].items()}
def legacy_guard():
    assert sql("SELECT COUNT(*) FROM instance_list WHERE zone=76 AND COALESCE(notes,'') NOT LIKE 'nc-dungeon:%';").strip()=='0','Legacy Hate instance needs explicit migration'
def capture():return hate_keeper.capture(sql)
def binaries(candidate=True):
    m=manifest();out={n:m['base_hashes']['bin/'+n] for n in old.NAMES}
    if candidate:out['zone']=m['zone_sha256']
    return out
def contract():
    result={}
    for family,checks in json.loads((STAGE/'runtime-contract.json').read_text()).items():
        values=sql(';\n'.join(c['sql'] for c in checks)+';').splitlines()
        assert len(values)==len(checks)
        failures=[c['label'] for c,v in zip(checks,values) if v!=c['expected']]
        assert not failures,(family,failures)
        result[family]=len(checks)
    assert result=={'schema':39,'content':499}
    return result
def unaffected():
    # Full checksums on all other public tables, exact row hashes outside each
    # changed table's owned scope. Do not ignore an entire spawn/zone table.
    changed=('spawn2','zone','nightcap_dungeon_spawns')
    result=old.hashes(old.PUBLIC-set(changed))
    for table in changed:
        columns=[s.split('\t')[0] for s in sql('SHOW COLUMNS FROM `'+table+'`;').splitlines()]
        fields=','.join('`'+c+'`' for c in columns)
        rows=sql('SELECT SHA2(JSON_ARRAY('+fields+'),256) FROM `'+table+'` WHERE NOT ('+hate_keeper.SCOPES[table]+');').splitlines()
        result[table]=old.row_fingerprint(sorted(rows))
    return result
def caches():return {name:sha(ROOT/'data/server/shared'/name) for name in ('items','spells')}
def untouched(p):
    for service in ('db','web','tunnel'):assert r.compact(service)==p['services'][service],service
    assert r.runtime()==p['runtime'] and r.public()==p['public']
    assert caches()==p['caches'] and unaffected()==p['unaffected']
    assert sql('SELECT revision,enabled FROM nightcap_dungeon_state;').strip()=='2026101601\t1'
def preflight():
    m=manifest();assert not EVIDENCE.exists(),'Never replay an existing attempt'
    services={s:r.compact(s) for s in ('game','gateway','db','web','tunnel')}
    assert all(v['running'] and not v['oom_killed'] for v in services.values())
    assert services['game']['image_id']==m['base_image_id'] and services['db']['health']=='healthy'
    assert r.image_hashes(m['base_image_id'])==m['base_hashes']
    r.running(m['base_image_id'],binaries(False),services['game']['restarts'])
    old.health();old.startup_guards();legacy_guard();r.closed_ports()
    before=capture();hate_keeper.desired(before)
    expected=json.loads((STAGE/'preimages.json').read_text())
    assert {t:v for t,v in normalized(before).items() if t!='zone_state_spawns'}=={t:v for t,v in normalized(expected).items() if t!='zone_state_spawns'}
    assert shutil.disk_usage(ROOT).free>=1500*1024**2
    p={'manifest_sha256':sha(STAGE/'manifest.json'),'services':services,'runtime':r.runtime(),'public':r.public(),'caches':caches(),'unaffected':unaffected(),'target':{t:v for t,v in normalized(before).items() if t!='zone_state_spawns'}}
    base='nightcap-game:hate-keeper-commonlands-20261022-base';target='nightcap-game:hate-keeper-commonlands-20261022'
    r.call('docker','tag',m['base_image_id'],base)
    (STAGE/'Dockerfile').write_text('FROM '+base+'\nCOPY bin/zone /opt/nightcap/bin/zone\n')
    (STAGE/'.dockerignore').write_text('*\n!Dockerfile\n!.dockerignore\n!bin\n!bin/zone\n')
    r.call('docker','build','--pull=false','--network','none','-t',target,str(STAGE))
    p['image']=r.out('docker','image','inspect','--format','{{.Id}}',target).strip()
    assert r.image_hashes(p['image'])=={**m['base_hashes'],'bin/zone':m['zone_sha256']}
    layers=lambda image:json.loads(r.out('docker','image','inspect',image))[0]['RootFS']['Layers']
    assert layers(p['image'])[:-1]==layers(m['base_image_id'])
    assert 'not found' not in r.out('docker','run','--rm','--network','none','--entrypoint','ldd',p['image'],'/opt/nightcap/bin/zone')
    r.call('docker','run','--rm','--network','none','--entrypoint','python3',p['image'],'-c','import sys;sys.path.insert(0,"/opt/nightcap");import start;start.validate_native()')
    untouched(p);assert all(r.compact(s)==v for s,v in services.items())
    EVIDENCE.mkdir(mode=0o700);save('preflight.json',p)
    print('Preflight passed; live gameplay unchanged.',flush=True)
def activate():
    p=read('preflight.json');assert p['manifest_sha256']==sha(STAGE/'manifest.json')
    assert not (EVIDENCE/'activation-started.json').exists()
    untouched(p);legacy_guard();old.startup_guards()
    assert all(r.compact(s)==v for s,v in p['services'].items())
    save('activation-started.json',{'main_and_live_approval_required':True})
    try:
        r.compose('stop','gateway');r.compose('stop','-t','90','game')
        state=r.state('game')['State'];assert not state['Running'] and state['ExitCode']==0 and not state['OOMKilled']
        assert not r.state('gateway')['State']['Running']
        legacy_guard();old.startup_guards();untouched(p)
        before=capture();after=hate_keeper.desired(before)
        assert {t:v for t,v in normalized(before).items() if t!='zone_state_spawns'}==p['target']
        data=old.saved_state();save('stopped-state.json',data);save('market-before.json',old.market())
        retained=old.row_fingerprint(old.zone_rows('WHERE NOT ('+hate_keeper.SCOPES['zone_state_spawns']+')'))
        save('fresh-preimages.json',before);save('backup.json',r.database_backup())
        assert old.saved_state()==data
        patch=hate_keeper.patch_sql(before,after)
        (EVIDENCE/'fresh-forward.sql').write_text(patch)
        sql(patch);save('content-committed.json',{'sha256':sha(EVIDENCE/'fresh-forward.sql')})
        assert normalized(capture())==normalized(after)
        expected={**data,'zone_state_spawns':retained}
        assert old.saved_state()==expected
        checks=contract();untouched(p)
        expected=old.boot_state(expected)
        r.select(p['image']);r.compose('up','-d','--wait','--wait-timeout','240','game')
        first=r.running(p['image'],binaries());old.health();time.sleep(8)
        current=r.running(p['image'],binaries());assert first['started_at']==current['started_at']
        market=old.verify_market(read('market-before.json'),current['started_at'])
        assert old.saved_state()==expected
        contract();untouched(p);r.closed_ports()
        save('verified-closed.json',{'runtime':current,'checks':checks,'market':market,'state_tables':len(data),'caches':caches()})
        r.compose('up','-d','--wait','--wait-timeout','60','gateway')
        result=r.running(p['image'],binaries());old.health();r.closed_ports();untouched(p)
        assert result['started_at']==current['started_at'] and r.state('gateway')['State']['Running']
        save('deployed.json',{'runtime':result,'gateway_open':True,'database_restored':False,'owner_gameplay_accepted':False,'checks':checks})
        print('Hate Keeper moved; runtime verified and access open.',flush=True)
    except BaseException:
        old.hold();raise
if __name__=='__main__':
    assert __debug__;os.umask(0o077);initialize()
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('preflight','activate'))
    action=parser.parse_args().action
    with (ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (ROOT/'private/gm-maintenance.json').exists()
        assert sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1'
        {'preflight':preflight,'activate':activate}[action]()
