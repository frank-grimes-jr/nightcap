"""Approved data-only layout rollout; retain runtime and subsequent player data."""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

STAGE=Path(__file__).resolve().parent
sys.path.insert(0,str(STAGE/'tools'))
import tunnel_cozy as content
import runtime_ops as r
r.STAGE=STAGE
r.EVIDENCE=STAGE/'evidence'
ROOT=r.ROOT
REHEARSAL='nightcap-cozy-rehearsal-20261013'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(name,value):
    with (r.EVIDENCE/name).open('x') as handle:json.dump(value,handle,indent=2);handle.write('\n')
def load(name):return json.loads((r.EVIDENCE/name).read_text())
def manifest():
    if not __debug__:raise RuntimeError('Assertions must be enabled')
    m=json.loads((STAGE/'manifest.json').read_text())
    for name,digest in m['files'].items():
        path=STAGE/name
        assert path.resolve().is_relative_to(STAGE) and not path.is_symlink() and sha(path)==digest,name
    return m
def exact(expected,query=r.sql,saved=True):
    actual=content.capture(query)
    for table in content.KEYS:
        if table=='zone_state_spawns' and not saved:continue
        assert content.normalize(actual['rows'][table])==content.normalize(expected['rows'][table]),'Content drift: '+table
    return actual
def preservation(query=r.sql):
    names=query("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND (TABLE_NAME LIKE 'character\\_%' OR TABLE_NAME LIKE 'nightcap\\_%' OR TABLE_NAME IN ('account','inventory','quest_globals','rule_values','items','spells_new','merchantlist','object_contents')) ORDER BY TABLE_NAME;").splitlines()
    names=[n for n in names if n not in ('nightcap_market_state','nightcap_market_offers')]
    assert {'inventory','character_advloot_claims','character_multiclass','merchantlist'}<=set(names)
    result={}
    for name in names:
        assert re.fullmatch('[a-z0-9_]+',name)
        checksum=query('CHECKSUM TABLE `'+name+'` EXTENDED;').strip().split('\t')[-1]
        assert checksum.isdigit(),name
        result[name]=checksum
    for table in content.KEYS:
        if table=='zone_state_spawns':continue
        result['outside:'+table]=hashlib.sha256('\n'.join(sorted(query('SELECT * FROM `'+table+'` WHERE NOT ('+content.SCOPES[table]+');').splitlines())).encode()).hexdigest()
    return result
def preserved_states(current,expected):
    topology=content.topology(expected['rows'])
    keep=lambda rows:[s for s in rows if not content.relocated_state(s,topology)]
    assert content.normalize(keep(current['rows']['zone_state_spawns']))==content.normalize(keep(expected['rows']['zone_state_spawns'])),'Unrelated scoped saved-state drift'
def outside_states(query=r.sql):
    rows=query('SELECT * FROM zone_state_spawns WHERE NOT ('+content.SCOPES['zone_state_spawns']+');').splitlines()
    return hashlib.sha256('\n'.join(sorted(rows)).encode()).hexdigest()
def market(query=r.sql):
    rows=query("SELECT JSON_OBJECT('id',id,'enabled',enabled,'epoch',epoch,'expansion',expansion,'loot_multiplier',loot_multiplier,'buy_cost_mod',CAST(buy_cost_mod AS CHAR),'rotated_at',CAST(rotated_at AS CHAR)) FROM nightcap_market_state;").splitlines()
    assert len(rows)==1
    state=json.loads(rows[0]);assert state['id']==1
    checksum=query('CHECKSUM TABLE nightcap_market_offers EXTENDED;').strip().split('\t')[-1]
    assert checksum.isdigit()
    return dict(state=state,offers_checksum=checksum)
def market_policy(current,previous):
    stable=lambda value:{k:v for k,v in value['state'].items() if k not in ('epoch','rotated_at')}
    assert stable(current)==stable(previous),'Market policy drift'
def market_boot(previous,query=r.sql):
    current=market(query);market_policy(current,previous)
    old=previous['state'];new=current['state']
    if old['enabled']!=1:
        assert current==previous,'Disabled market changed'
        return current
    assert new['epoch']==old['epoch']+1 and new['rotated_at'],'Unexpected market boot rotation'
    invalid=query("SELECT COUNT(*) FROM nightcap_market_offers o LEFT JOIN nightcap_market_actors a ON a.npc_id=o.npc_id LEFT JOIN nightcap_market_catalog c ON c.item_id=o.item_id JOIN nightcap_market_state s ON s.id=1 WHERE a.npc_id IS NULL OR c.item_id IS NULL OR o.epoch<>s.epoch OR o.zone_id<>a.zone_id OR o.kind<>a.kind OR o.remaining<>1 OR c.pool<>IF(o.kind='find','find','tunnel') OR c.min_expansion>s.expansion OR (c.max_expansion>=0 AND c.max_expansion<s.expansion) OR o.price_cp<>CASE o.kind WHEN 'find' THEN c.find_cp WHEN 'sell' THEN c.sell_cp ELSE c.buy_cp END;").strip()
    assert invalid=='0','Invalid rotated market offers'
    return current
def precise_character_positions(query=r.sql):
    # mysqldump emits FLOAT's display precision, which can lose binary bits.
    # Promote to DOUBLE for round-trip text; this sidecar is for backup restore
    # only. Never apply old player coordinates to the live database.
    rows=query('SELECT id,y+0e0,x+0e0,z+0e0,heading+0e0 FROM character_data ORDER BY id;').splitlines()
    statements=[]
    for row in rows:
        ident,*values=row.split('\t')
        assert ident.isdigit() and len(values)==4
        assert all(re.fullmatch(r'-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?',v) for v in values)
        assignments=','.join('`'+key+'`='+value for key,value in zip(('y','x','z','heading'),values))
        statements.append('UPDATE character_data SET '+assignments+' WHERE id='+ident+';')
    return 'START TRANSACTION;\n'+'\n'.join(statements)+'\nCOMMIT;\n'
def health(p):
    game=p['services']['game']
    return r.running(game['image_id'],p['binaries'],expected_restarts=game['restarts'])
def guard(p):
    assert sha(ROOT/'data/server/maps/base/ecommons.map')==p['map_sha256'],'Map drift'
    assert r.image_hashes(p['services']['game']['image_id'])==p['image_hashes'],'Image drift'
    r.untouched(p);r.closed_ports()
def stop():
    r.compose('stop','gateway');r.compose('stop','-t','90','game')
    state=r.state('game')['State']
    assert not r.state('gateway')['State']['Running'] and not state['Running']
    assert state['ExitCode']==0 and not state.get('OOMKilled'),'Unclean shutdown'
def start_game(p):
    r.call('docker','start',p['services']['game']['id'])
    for _ in range(120):
        if r.compact('game')['health']=='healthy':break
        time.sleep(1)
    else:raise RuntimeError('Game startup timeout')
    return health(p)
def open_gateway(p):
    r.call('docker','start',p['services']['gateway']['id'])
    assert r.compact('gateway')['running']
    r.closed_ports()
def restore_rehearsal(before,after,backup):
    assert not r.out('docker','ps','-aq','--filter','name=^/'+REHEARSAL+'$').strip()
    image=r.state('db')['Image']
    r.call('docker','run','-d','--rm','--name',REHEARSAL,'--label','nightcap.release=tunnel-cozy-20261013','--network','none','--memory','1536m','-e','MARIADB_ALLOW_EMPTY_ROOT_PASSWORD=1',image)
    try:
        for _ in range(90):
            ready=subprocess.run(['docker','exec',REHEARSAL,'mariadb-admin','-uroot','ping'],capture_output=True)
            daemon=subprocess.run(['docker','exec',REHEARSAL,'cat','/proc/1/comm'],capture_output=True,text=True)
            if ready.returncode==0 and daemon.stdout.strip()=='mariadbd':break
            time.sleep(1)
        else:raise RuntimeError('Rehearsal startup timeout')
        r.call('docker','exec',REHEARSAL,'mariadb','-uroot','-e','CREATE DATABASE peq;')
        r.call('docker','cp',backup['path'],REHEARSAL+':/tmp/backup.sql.gz')
        with (r.EVIDENCE/'restore-private.log').open('xb') as errors:
            result=subprocess.run(['docker','exec',REHEARSAL,'bash','-o','pipefail','-c','gzip -dc /tmp/backup.sql.gz | mariadb -uroot peq'],stdout=errors,stderr=errors,timeout=360)
        assert result.returncode==0,'Full backup restore failed'
        def query(sql):
            result=subprocess.run(['docker','exec','-i',REHEARSAL,'mariadb','-uroot','--batch','--raw','--skip-column-names','peq'],input=sql,text=True,capture_output=True,timeout=180)
            assert result.returncode==0,'Isolated SQL failed'
            return result.stdout
        sidecar=Path(backup['position_precision']['path'])
        assert sha(sidecar)==backup['position_precision']['sha256']
        query(sidecar.read_text())
        baseline=load('preservation-before.json');states=load('outside-states-before.json');market_before=load('market-before.json')
        exact(before,query);assert preservation(query)==baseline and outside_states(query)==states and market(query)==market_before
        query(content.patch_sql(before,after));exact(after,query)
        assert preservation(query)==baseline and outside_states(query)==states and market(query)==market_before
        rollback=content.rollback_target(before,after,after)
        query(content.patch_sql(after,rollback));exact(rollback,query)
        assert preservation(query)==baseline and outside_states(query)==states and market(query)==market_before
        save('rehearsal.json',dict(full_backup_restored=True,exact_forward=True,exact_rollback=True,preserved_fingerprints=len(baseline)))
        print('Full backup restore and exact forward/rollback rehearsal passed.',flush=True)
    finally:
        actual=json.loads(r.out('docker','inspect',REHEARSAL))[0]
        assert actual['Config']['Labels'].get('nightcap.release')=='tunnel-cozy-20261013'
        r.call('docker','stop',REHEARSAL)
def preflight():
    m=manifest();assert not r.EVIDENCE.exists()
    assert shutil.disk_usage(ROOT).free>8_000_000_000
    services={n:r.compact(n) for n in ('game','gateway','db','web','tunnel')}
    assert services['game']['running'] and services['gateway']['running']
    hashes=r.image_hashes(services['game']['image_id'])
    p=dict(services=services,image_hashes=hashes,binaries={n:hashes['bin/'+n] for n in ('world','zone','ucs','loginserver')},
           runtime=r.runtime(),public=r.public(),map_sha256=m['map_sha256'],manifest_sha256=sha(STAGE/'manifest.json'))
    health(p);guard(p)
    reviewed=json.loads((STAGE/'reviewed-before.json').read_text())
    current=exact(reviewed,saved=False);content.desired(current)
    r.EVIDENCE.mkdir(mode=0o700);save('preflight.json',p)
    print(json.dumps(dict(preflight='passed',image_id=services['game']['image_id'])),flush=True)
def activate():
    manifest();p=load('preflight.json')
    assert p['manifest_sha256']==sha(STAGE/'manifest.json')
    assert r.compact('game')==p['services']['game'] and r.compact('gateway')==p['services']['gateway']
    guard(p);reviewed=json.loads((STAGE/'reviewed-before.json').read_text());exact(reviewed,saved=False)
    before=after=baseline=states=market_before=None
    access_may_have_opened=False
    boot_attempted=False
    try:
        stop()
        before=exact(reviewed,saved=False);after=content.desired(before)
        baseline=preservation();states=outside_states();market_before=market()
        save('before-content.json',before);save('after-content.json',after)
        save('preservation-before.json',baseline);save('outside-states-before.json',states)
        save('market-before.json',market_before)
        backup=r.database_backup()
        sidecar=Path(backup['path']).with_name('character-position-precision.sql')
        with sidecar.open('x') as handle:handle.write(precise_character_positions())
        backup['position_precision']=dict(path=str(sidecar),sha256=sha(sidecar))
        save('backup.json',backup)
        (r.EVIDENCE/'forward.sql').write_text(content.patch_sql(before,after))
        restore_rehearsal(before,after,backup)
        exact(before);assert preservation()==baseline and outside_states()==states and market()==market_before;guard(p)
        save('apply-started.json',dict(utc=time.time()))
        r.sql((r.EVIDENCE/'forward.sql').read_text());exact(after)
        assert preservation()==baseline and outside_states()==states and market()==market_before
        boot_attempted=True
        result=start_game(p)
        save('market-after-boot.json',market_boot(market_before))
        current=exact(after,saved=False);preserved_states(current,after)
        assert preservation()==baseline and outside_states()==states,'Preservation drift while closed'
        guard(p);save('verified-closed.json',result)
        access_may_have_opened=True
        open_gateway(p)
        save('activated.json',dict(runtime=result,gateway_open=True,source_commit=manifest()['source_commit'],
             preserved_fingerprints=len(baseline),backup=backup,client_update=False,changed_npcs=25,changed_stations=6,ornaments=3))
        print(json.dumps(dict(status='activated',gateway_open=True,changed_npcs=25)),flush=True)
    except BaseException:
        try:
            recover(p,before,after,baseline,states,market_before,access_may_have_opened,boot_attempted)
        except BaseException:
            r.compose('stop','gateway')
            raise
        raise
def recover(p,before,after,baseline,states,market_before,access_may_have_opened,boot_attempted):
    stop()
    assert before is not None and baseline is not None and states is not None and market_before is not None,'No verified recovery baseline; hold closed'
    state_boundary=before
    if access_may_have_opened:
        baseline=preservation();states=outside_states()
        state_boundary=content.capture(r.sql)
    recovery_market=market();market_policy(recovery_market,market_before)
    if not access_may_have_opened and recovery_market!=market_before:
        assert boot_attempted,'Market drift before any boot; hold closed'
        market_boot(market_before)
    if before is not None:
        current=content.capture(r.sql)
        matches=lambda expected:all(content.normalize(current['rows'][t])==content.normalize(expected['rows'][t]) for t in content.KEYS if t!='zone_state_spawns')
        if not matches(before):
            assert after is not None and matches(after),'Unexpected content during recovery; hold closed'
            target=content.rollback_target(before,current,after)
            sql=content.patch_sql(current,target)
            (r.EVIDENCE/'recovery.sql').write_text(sql);r.sql(sql);exact(target)
            assert market()==recovery_market,'Market changed during rollback'
    guard(p)
    if baseline is not None:
        assert preservation()==baseline and outside_states()==states,'Persistent data drift; hold closed'
    if state_boundary is not None:preserved_states(content.capture(r.sql),state_boundary)
    result=start_game(p)
    market_boot(recovery_market)
    if before is not None:exact(before,saved=False)
    if baseline is not None:
        assert preservation()==baseline and outside_states()==states,'Recovery boot data drift; hold closed'
    if state_boundary is not None:preserved_states(content.capture(r.sql),state_boundary)
    guard(p);open_gateway(p)
    save('recovered.json',dict(runtime=result,gateway_open=True,full_database_restored=False))
def report():
    manifest();p=load('preflight.json');activated=load('activated.json')
    result=health(p);assert result['started_at']==activated['runtime']['started_at']
    guard(p);assert r.compact('gateway')['running']
    exact(load('after-content.json'),saved=False)
    report=dict(activated=activated,current=result,static_afterimages=True,gateway_open=True)
    (r.EVIDENCE/('report-'+str(time.time_ns())+'.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report),flush=True)

if __name__=='__main__':
    os.umask(0o077)
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['preflight','activate','report']);args=parser.parse_args()
    with (ROOT/'.deployment.lock').open('a') as lock, open('/var/lock/nightcap-gm.lock','a') as gm:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (ROOT/'private/gm-maintenance.json').exists(),'GM maintenance active'
        assert r.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1','GM SQL in flight'
        globals()[args.action]()
