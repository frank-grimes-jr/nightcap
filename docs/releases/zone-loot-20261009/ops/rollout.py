"""Owner-authorized first installation. Preserve players; reopen only after verification."""
import argparse,fcntl,hashlib,json,os,re,subprocess,time
from pathlib import Path
import runtime_ops as r

r.STAGE=Path('/opt/nightcap/releases/zone-hunt-20261009')
r.EVIDENCE=r.STAGE/'evidence'
ROOT,STAGE,EVIDENCE=r.ROOT,r.STAGE,r.EVIDENCE
REVISION=2026100901

def sql(q):
    p=subprocess.run(['docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','--skip-column-names','peq'],cwd=ROOT,input=q,text=True,capture_output=True,timeout=900)
    if p.returncode:raise RuntimeError('Database operation failed: '+p.stderr[-600:])
    return p.stdout
r.sql=sql

def manifest():
    m=json.loads((STAGE/'manifest.json').read_text())
    for n,h in m['files'].items():
        p=STAGE/n
        assert p.resolve().is_relative_to(STAGE) and not p.is_symlink() and r.sha(p)==h,n
    assert set(m['binaries'])=={'world','zone','ucs','loginserver','shared_memory'}
    return m

def data(name):return json.loads((STAGE/'generated'/name).read_text())
def item_ids():return {x['id'] for x in data('items.json')}
def literal(value):
    if isinstance(value,str):return "X'"+value.encode().hex()+"'"
    return str(int(value))

def content():
    # Hash every pre-existing item column, normalizing ONLY the twelve socket
    # columns on the reviewed 2,290 edits. socket_check separately proves each.
    patched=','.join(str(x['id']) for x in data('socket-preimages.json'))
    columns=[x.split('\t')[0] for x in sql('SHOW COLUMNS FROM items;').splitlines()]
    assert all(re.fullmatch('[A-Za-z0-9_]+',c) for c in columns)
    cells=[]
    for c in columns:
        expr='`'+c+'`'
        if re.fullmatch('augslot[1-6](type|visible)',c):expr=f'IF(id IN ({patched}),NULL,{expr})'
        cells.append(f"IFNULL(HEX({expr}),'NULL')")
    rows=sql("SELECT SHA2(CONCAT_WS('|',"+','.join(cells)+"),256) FROM items WHERE id NOT BETWEEN 940000 AND 940999 ORDER BY id;")
    checks=sql('CHECKSUM TABLE spells_new,npc_types,spawn2,spawnentry,loottable,loottable_entries,lootdrop,lootdrop_entries,merchantlist,zone,variables EXTENDED;')
    assert len(checks.splitlines())==11 and all(x.split('\t')[-1].isdigit() for x in checks.splitlines())
    return {'original_item_rows':len(rows.splitlines()),'original_items_sha256':hashlib.sha256(rows.encode()).hexdigest(),'other_content':checks}

def socket_check(installed):
    cols=list(data('socket-preimages.json')[0]['before'])
    ids=','.join(str(x['id']) for x in data('socket-preimages.json'))
    rows={int(a[0]):dict(zip(cols,a)) for line in sql('SELECT '+','.join('`'+c+'`' for c in cols)+' FROM items WHERE id IN ('+ids+');').splitlines() if (a:=line.split('\t'))}
    assert len(rows)==2290
    for x in data('socket-preimages.json'):
        expected=dict(x['before'])
        if installed:expected.update({f"augslot{x['socket']}type":'22',f"augslot{x['socket']}visible":'1'})
        assert rows[x['id']]==expected,('socket drift',x['id'])

def installed_check(enabled):
    assert sql('SELECT id,revision,enabled FROM nightcap_zone_hunt_state;').strip()==f'1\t{REVISION}\t{enabled}'
    assert {int(x) for x in sql('SELECT id FROM items WHERE id BETWEEN 940000 AND 940999;').splitlines()}==item_ids()
    # Validate every explicitly generated value, including heroics, slots and resale.
    clauses=[]
    for x in data('items.json'):
        clauses.append('(id='+str(x['id'])+' AND '+' AND '.join(('BINARY ' if isinstance(v,str) else '')+'`'+k+'`='+literal(v) for k,v in x['values'].items())+')')
    assert sql('SELECT COUNT(*) FROM items WHERE '+' OR '.join(clauses)+';').strip()=='448'
    expected_sources=sorted(tuple(x[k] for k in ('zone_id','spawn_id','npc_id')) for x in data('sources.json'))
    actual_sources=sorted(tuple(map(int,line.split('\t'))) for line in sql('SELECT zone_id,spawn_id,npc_id FROM nightcap_zone_hunt_sources;').splitlines())
    assert actual_sources==expected_sources
    # Native zone config must be byte-for-byte the SQL rows that were reviewed.
    install=(STAGE/'generated/install.sql').read_text()
    zones=[tuple(map(int,re.search(r'VALUES \(([^)]+)\)',line).group(1).split(','))) for line in install.splitlines() if line.startswith('INSERT INTO nightcap_zone_hunt_zones ')]
    actual=[tuple(map(int,line.split('\t'))) for line in sql('SELECT zone_id,augment_base,gear_base,min_level,night_only,enabled FROM nightcap_zone_hunt_zones;').splitlines()]
    assert sorted(zones)==sorted(actual) and sum(z[-1] for z in actual)==48
    socket_check(True)

def early_undo(before,baseline):
    # Only before gateway reopening, after stopping all writers, and while all
    # player/corpse/receipt rows are EXACTLY their captured pre-install state.
    assert not r.state('gateway')['State']['Running'] and not r.state('game')['State']['Running']
    assert r.player_data()==before and content()==baseline
    installed_check(int(sql('SELECT enabled FROM nightcap_zone_hunt_state WHERE id=1;').strip()))
    assert sql('SELECT COUNT(*) FROM nightcap_zone_hunt_forges;').strip()=='0'
    statements=['DELIMITER //','CREATE PROCEDURE zone_hunt_initial_undo() BEGIN DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END; START TRANSACTION;']
    for x in data('socket-preimages.json'):
        n=x['socket'];old=x['before']
        statements.append(f"UPDATE items SET augslot{n}type={int(old[f'augslot{n}type'])},augslot{n}visible={int(old[f'augslot{n}visible'])} WHERE id={x['id']} AND augslot{n}type=22 AND augslot{n}visible=1;")
        statements.append("IF ROW_COUNT()<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Initial undo socket drift'; END IF;")
    statements+=['DELETE FROM items WHERE id IN ('+','.join(map(str,sorted(item_ids())))+');',"IF ROW_COUNT()<>448 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Initial undo item drift'; END IF;",'DELETE FROM nightcap_zone_hunt_sources; DELETE FROM nightcap_zone_hunt_zones; DELETE FROM nightcap_zone_hunt_state; COMMIT; END//','DELIMITER ;','CALL zone_hunt_initial_undo();','DROP PROCEDURE zone_hunt_initial_undo;']
    sql('\n'.join(statements));socket_check(False);assert content()==baseline

def verify_cache():
    # Reuse the full-catalog ABI/free-trade verifier with only reward resale
    # overridden, matching SharedDatabase::LoadItems. No struct layout changed.
    result=r.verify_cache(item_ids());result['zero_resale_reward_definitions']=len(item_ids());return result

def build_image(m):
    # Dockerfile FROM needs a local image name; both tag guards and the complete
    # layer ancestry check bind that name to the captured immutable base.
    def identity():return r.out('docker','image','inspect','--format','{{.Id}}',m['old_image']).strip()
    assert identity()==m['old_image_id'],'Base image tag drift'
    r.call('docker','build','--network','none','-t',m['new_image'],str(STAGE))
    assert identity()==m['old_image_id'],'Base image tag drift during build'
    image=r.out('docker','image','inspect','--format','{{.Id}}',m['new_image']).strip()
    layers=lambda i:json.loads(r.out('docker','image','inspect',i))[0]['RootFS']['Layers']
    old,new=layers(m['old_image_id']),layers(image)
    assert new[:len(old)]==old and len(new)==len(old)+1,'Unexpected image ancestry'
    return image

def preflight():
    m=manifest();assert not EVIDENCE.exists();r.closed_ports()
    old=r.compact('game');assert old['image_id']==m['old_image_id']
    old_hashes=r.image_hashes(m['old_image_id']);r.running(m['old_image_id'],{n:old_hashes['bin/'+n] for n in m['binaries']},expected_restarts=old['restarts'])
    assert sql("SELECT COUNT(*) FROM items WHERE id BETWEEN 940000 AND 940999; SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='peq' AND TABLE_NAME LIKE 'nightcap_zone_hunt%';").strip()=='0\n0'
    assert sql("SELECT rule_value FROM rule_values WHERE ruleset_id=1 AND rule_name='Expansion:CurrentExpansion';").strip()=='0'
    socket_check(False)
    image=build_image(m)
    expected={**old_hashes,**{'bin/'+n:h for n,h in m['binaries'].items()}}
    assert r.image_hashes(image)==expected
    r.call('docker','run','--rm','--network','none','--entrypoint','python3',image,'-c',"import sys;sys.path.insert(0,'/opt/nightcap');import start;start.validate_native()")
    r.call('docker','run','--rm','--network','none','--entrypoint','/opt/nightcap/bin/loginserver',image,'--nightcap-crypto-self-test')
    EVIDENCE.mkdir(mode=0o700)
    backup=r.database_backup()
    snapshot={'manifest_sha256':r.sha(STAGE/'manifest.json'),'new_image_id':image,'old_hashes':old_hashes,'services':{s:r.compact(s) for s in ('game','gateway','db','web','tunnel')},'runtime':r.runtime(),'public':r.public(),'content':content(),'backup':backup}
    r.save('preflight.json',snapshot);print(json.dumps({'status':'preflight_passed','backup_verified':True,'image_id':image}),flush=True)

def activate():
    m=manifest();p=r.load('preflight.json');assert p['manifest_sha256']==r.sha(STAGE/'manifest.json')
    expected={**p['old_hashes'],**{'bin/'+n:h for n,h in m['binaries'].items()}}
    assert r.image_hashes(p['new_image_id'])==expected, 'Verified immutable candidate changed'
    for s in ('game','gateway'):assert r.compact(s)==p['services'][s]
    r.untouched(p);r.closed_ports();assert content()==p['content'];socket_check(False)
    before=None;installed=False;opened=False
    try:
        r.compose('stop','gateway');r.compose('stop','-t','90','game')
        assert not r.state('gateway')['State']['Running']
        stopped=r.state('game')['State'];assert not stopped['Running'] and stopped['ExitCode']==0 and not stopped.get('OOMKilled')
        before=r.player_data();r.save('player-before.json',before)
        assert content()==p['content'];socket_check(False)
        sql((STAGE/'generated/install.sql').read_text());installed=True
        installed_check(0);assert r.player_data()==before and content()==p['content']
        sql((STAGE/'generated/activate.sql').read_text());installed_check(1)
        r.select(p['new_image_id']);r.compose('up','-d','--wait','--wait-timeout','240','game')
        cache=verify_cache();first=r.running(p['new_image_id'],m['binaries']);time.sleep(5)
        result=r.running(p['new_image_id'],m['binaries']);assert first['started_at']==result['started_at']
        assert r.player_data()==before and content()==p['content'];installed_check(1)
        assert sql('SELECT COUNT(*) FROM nightcap_zone_hunt_forges;').strip()=='0'
        r.untouched(p);r.save('verified-closed.json',{'runtime':result,'player_tables_preserved':len(before),'content':p['content'],'cache':cache})
        opened=True  # A lost startup acknowledgement may still allow players in.
        r.compose('up','-d','--wait','--wait-timeout','60','gateway')
        assert r.state('gateway')['State']['Running'];r.closed_ports();r.running(p['new_image_id'],m['binaries']);r.untouched(p)
        r.save('activated.json',{'runtime':result,'player_tables_preserved':len(before),'quest_files_preserved':len(p['runtime']),'cache':cache,'gateway_open':True,'database_restored':False,'backup':p['backup']})
        print(json.dumps({'status':'activated','player_tables_preserved':len(before),'gateway_open':True,'cache':cache}),flush=True)
    except BaseException:
        try:
            r.compose('stop','gateway');r.compose('stop','-t','90','game')
            # After players could connect, retain all earned content and stay
            # closed for recovery; never run the pre-opening inverse migration.
            if opened:
                sql((STAGE/'generated/rollback.sql').read_text());raise RuntimeError('Post-opening fault: acquisition disabled; preserve rewards and investigate')
            if installed:early_undo(before,p['content'])
            elif before is not None:
                assert r.player_data()==before and content()==p['content'];socket_check(False)
                assert sql('SELECT COUNT(*) FROM items WHERE id BETWEEN 940000 AND 940999;').strip()=='0'
            assert r.image_hashes(m['old_image_id'])==p['old_hashes']
            r.select(m['old_image_id']);r.compose('up','-d','--wait','--wait-timeout','240','game')
            r.running(m['old_image_id'],{n:p['old_hashes']['bin/'+n] for n in m['binaries']})
            if before is not None:assert r.player_data()==before
            assert content()==p['content'];r.verify_cache();r.untouched(p)
            r.compose('up','-d','--wait','--wait-timeout','60','gateway');r.closed_ports()
            r.save('rolled-back.json',{'gateway_open':True,'database_restored':False,'initial_install_reversed':installed})
        except BaseException:
            r.compose('stop','gateway');r.save('held-closed.json',{'gateway_running':r.state('gateway')['State']['Running'],'database_restored':False});raise
        raise

def report():
    m=manifest();p=r.load('preflight.json');result=r.running(p['new_image_id'],m['binaries']);r.closed_ports()
    assert r.state('gateway')['State']['Running'];installed_check(1);r.untouched(p)
    print(json.dumps({'runtime':result,'deployment':r.load('activated.json'),'cache':verify_cache(),'gate':'active','zones':48,'sources':6056,'items':448}))

if __name__=='__main__':
    os.umask(0o077);p=argparse.ArgumentParser();p.add_argument('action',choices=['preflight','activate','report']);a=p.parse_args()
    with (ROOT/'.deployment.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);globals()[a.action]()
