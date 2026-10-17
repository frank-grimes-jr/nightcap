"""One-shot production content operation. Execute over SSH stdin, never import to apply."""
import copy
import datetime
import fcntl
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import struct
import sys
import time

ROOT = Path('/opt/nightcap/deploy/production')
OUT = Path('/opt/nightcap/backups/commonlands-services-20261016')
DB = ['docker', 'compose', 'exec', '-T', 'db', 'mariadb',
      '--defaults-extra-file=/run/secrets/db_backup_config', '--batch', '--raw',
      '--skip-column-names', 'peq']
SCOPES = {
    'items': 'id=16488',
    'merchantlist': 'merchantid=999603',
    'npc_types': "id IN (999600,999603,999821) OR name='Mira_Coinwell'",
    'spawngroup': 'id IN (999600,999821)',
    'spawnentry': 'spawngroupID IN (999600,999821) OR npcID=999821',
    'spawn2': 'id IN (999600,999821) OR spawngroupID=999821',
}
KEYS = {'items':['id'], 'merchantlist':['merchantid','slot'],
        'npc_types':['id'], 'spawngroup':['id'],
        'spawnentry':['spawngroupID','npcID'], 'spawn2':['id']}

def run(args, data=None, timeout=120):
    result = subprocess.run(args, cwd=ROOT, input=data, text=True,
                            capture_output=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr[-4000:])
    return result.stdout

def sql(query):
    return run(DB, query)

def value(v):
    return 'NULL' if v is None else "CONVERT(X'"+str(v).encode().hex()+"' USING utf8mb4)"

def predicate(row):
    return ' AND '.join(f'BINARY CAST(`{k}` AS CHAR) <=> BINARY {value(v)}' for k,v in row.items())

def capture(scopes=SCOPES):
    statements=['SET TRANSACTION ISOLATION LEVEL REPEATABLE READ; START TRANSACTION WITH CONSISTENT SNAPSHOT;']
    for table, scope in scopes.items():
        columns=[line.split('\t')[0] for line in sql(f'SHOW COLUMNS FROM `{table}`;').splitlines()]
        fields=','.join(value(c)+f',CAST(`{c}` AS CHAR)' for c in columns)
        statements.append(f'SELECT {value(table)},JSON_OBJECT({fields}) FROM `{table}` WHERE {scope};')
    statements.append('ROLLBACK;')
    rows={t:[] for t in scopes}
    for line in sql('\n'.join(statements)).splitlines():
        table, data=line.split('\t',1)
        rows[table].append(json.loads(data))
    return rows

def normalized(rows):
    return {t:sorted(json.dumps(r,sort_keys=True) for r in rs) for t,rs in rows.items()}

def desired(before):
    after=copy.deepcopy(before)
    assert len(before['items'])==1 and before['items'][0]['Name']=='Leather Padding'
    assert before['items'][0]['price']=='400' and float(before['items'][0]['sellrate'])==2
    assert len(before['merchantlist'])==18
    assert sorted(int(r['slot']) for r in before['merchantlist'])==list(range(1,19))
    assert all(r['item']!='16488' for r in before['merchantlist'])
    assert {r['id'] for r in before['npc_types']}=={'999600','999603'}
    donor=next(r for r in before['npc_types'] if r['id']=='999600')
    merchant=next(r for r in before['npc_types'] if r['id']=='999603')
    assert donor['name']=='Tessa' and donor['class']=='41'
    assert merchant['name']=='Haldra' and merchant['merchant_id']=='999603' and merchant['class']=='41'
    for field in ('npc_faction_id','loottable_id','npc_spells_id','adventure_template_id','trap_template','emoteid'):
        assert donor[field]=='0', (field,donor[field])
    assert len(before['spawngroup'])==len(before['spawnentry'])==len(before['spawn2'])==1
    assert before['spawn2'][0]['zone']=='ecommons' and before['spawn2'][0]['version']=='0'
    after['items'][0]['sellrate']='3'
    stock=copy.deepcopy(next(r for r in before['merchantlist'] if r['slot']=='18'))
    stock.update(slot='19',item='16488')
    assert stock['classes_required']=='65535' and stock['probability']=='100'
    assert stock['alt_currency_cost']=='0' and stock['level_required']=='0'
    after['merchantlist'].append(stock)
    banker=copy.deepcopy(donor)
    banker.update(id='999821',name='Mira_Coinwell',lastname='Banker',
                  **{'class':'40'},merchant_id='0',gender='1',race='1')
    after['npc_types'].append(banker)
    group=copy.deepcopy(before['spawngroup'][0])
    group.update(id='999821',name='NightcapTunnel999821')
    after['spawngroup'].append(group)
    entry=copy.deepcopy(before['spawnentry'][0])
    entry.update(spawngroupID='999821',npcID='999821')
    after['spawnentry'].append(entry)
    spawn=copy.deepcopy(before['spawn2'][0])
    spawn.update(id='999821',spawngroupID='999821',x='-144.000000',
                 y='-1584.000000',z='3.750000',heading='128.000000')
    after['spawn2'].append(spawn)
    return after

def insert(table,row):
    return f'INSERT INTO `{table}` ('+','.join(f'`{k}`' for k in row)+') VALUES ('+','.join(value(v) for v in row.values())+');'

def patch(before,after):
    out=['DELIMITER //','BEGIN NOT ATOMIC','DECLARE n BIGINT;',
         "DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;",
         'SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;','START TRANSACTION;']
    for table,scope in SCOPES.items():
        out += [f"SELECT COUNT(*) INTO n FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='{table}' AND ENGINE='InnoDB';",
                f"IF n<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Engine drift: {table}'; END IF;",
                f"SELECT COUNT(*) INTO n FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() AND EVENT_OBJECT_TABLE='{table}';",
                f"IF n<>0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Unexpected trigger: {table}'; END IF;",
                f'SELECT COUNT(*) INTO n FROM `{table}` WHERE {scope} FOR UPDATE;',
                f"IF n<>{len(before[table])} THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Count drift: {table}'; END IF;"]
        for row in before[table]:
            out += [f'SELECT COUNT(*) INTO n FROM `{table}` WHERE {predicate(row)};',
                    f"IF n<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Preimage drift: {table}'; END IF;"]
    for table,keys in KEYS.items():
        old={tuple(r[k] for k in keys):r for r in before[table]}
        new={tuple(r[k] for k in keys):r for r in after[table]}
        for k,row in old.items():
            if k not in new:
                out.append(f'DELETE FROM `{table}` WHERE {predicate(row)};')
            elif row!=new[k]:
                fields=','.join(f'`{c}`={value(v)}' for c,v in new[k].items() if row[c]!=v)
                out.append(f'UPDATE `{table}` SET {fields} WHERE {predicate(row)};')
        for k,row in new.items():
            if k not in old:
                out.append(insert(table,row))
    out+=['COMMIT;','END //','DELIMITER ;']
    return '\n'.join(out)+'\n'

def save(name,data):
    (OUT/name).write_text(json.dumps(data,indent=2)+'\n' if not isinstance(data,str) else data)

def fingerprint():
    return run(['docker','compose','exec','-T','game','sha256sum',
                '/opt/nightcap/bin/world','/opt/nightcap/bin/zone','/opt/nightcap/bin/shared_memory'])

def item_cache():
    probe=r'''
import hashlib,json,mmap,struct
with open('/srv/nightcap/shared/items','rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as m:
 payload,count,maximum,current=struct.unpack_from('<IIII',m)
 assert payload+8==len(m) and maximum==current
 assert len(m)==20+4*count+1332*current
 index=struct.unpack_from('<I',m,16+16488*4)[0]
 begin=16+4*count+1332*index;end=begin+1332
 record=m[begin:end];assert b'Leather Padding\0' in record
 digest=hashlib.sha256()
 for a,b in ((0,begin),(end,len(m))):
  for p in range(a,b,1024*1024): digest.update(m[p:min(p+1024*1024,b)])
 print(json.dumps(dict(items=current,index=index,record=record.hex(),other_bytes=digest.hexdigest())))
'''
    return json.loads(run(['docker','compose','exec','-T','game','python3','-c',probe]))

def check_cache(before,after):
    assert before['other_bytes']==after['other_bytes'],'Unrelated item-cache bytes changed'
    old=bytes.fromhex(before['record']);new=bytes.fromhex(after['record'])
    matches=[]
    for offset in range(0,len(old)-3,4):
        if old[offset:offset+4]==struct.pack('<f',2.) and new[offset:offset+4]==struct.pack('<f',3.):
            if old[:offset]+old[offset+4:]==new[:offset]+new[offset+4:]:matches.append(offset)
    assert len(matches)==1,'Expected exactly one cached float change from 2 to 3'
    return dict(items_checked=before['items'],sellrate_offset=matches[0],sellrate=3,
                all_other_cache_bytes_preserved=True)

def start_and_wait():
    run(['docker','compose','start','game'])
    for _ in range(60):
        state=json.loads(run(['docker','inspect','nightcap-production-game-1']))[0]['State']
        if state.get('Health',{}).get('Status')=='healthy':
            return state
        time.sleep(1)
    raise RuntimeError('Game did not become healthy; gateway remains stopped')

def placement():
    banker=(-144.,-1584.);front=(-132.,-1584.)
    def segment(p,a,b):
        dx=b[0]-a[0];dy=b[1]-a[1]
        t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy))) if dx or dy else 0
        return math.dist(p,(a[0]+t*dx,a[1]+t*dy))
    static=[]
    for query in ("SELECT x,y FROM spawn2 WHERE zone='ecommons' AND version IN (0,-1) AND pathgrid=0;",
                  "SELECT xpos,ypos FROM object WHERE zoneid=22;",
                  "SELECT pos_x,pos_y FROM doors WHERE zone='ecommons' AND version IN (0,-1);"):
        static += [tuple(map(float,r.split('\t'))) for r in sql(query).splitlines()]
    assert all(math.dist(banker,p)>=14 for p in static),'Banker overlaps existing content'
    assert all(segment(p,banker,front)>=8 for p in static),'Banker approach obstructed'
    routes={}
    for row in sql('SELECT gridid,number,x,y FROM grid_entries WHERE zoneid=22 ORDER BY gridid,number;').splitlines():
        grid,num,x,y=row.split('\t');routes.setdefault(grid,[]).append((float(x),float(y)))
    gaps=[segment(banker,a,b) for points in routes.values() for a,b in zip(points,points[1:]+points[:1])]
    assert min(gaps)>=12,'Banker obstructs a walking route'
    assert sql("SELECT COUNT(*) FROM zone_state_spawns WHERE npc_id=999821 OR spawn2_id=999821 OR spawngroup_id=999821;").strip()=='0'
    assert sql('SELECT COUNT(*) FROM spawn2_disabled WHERE spawn2_id=999821;').strip()=='0'
    for zone in ('global','ecommons'):
        for name in ('999821','Mira_Coinwell'):
            for suffix in ('.pl','.lua'):
                assert not (ROOT/'data/server/quests'/zone/(name+suffix)).exists(),'Existing banker quest binding'
    return dict(nearest_static= min(math.dist(banker,p) for p in static),nearest_walking_route=min(gaps),
                approach_clear=True,unrelated_saved_states_untouched=True)

def apply(preflight=False):
    os.umask(0o077)
    with (ROOT/'.deployment.lock').open('a') as lock, open('/var/lock/nightcap-gm.lock','a') as gm:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (ROOT/'private/gm-maintenance.json').exists()
        assert sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1'
        OUT.mkdir(mode=0o700,exist_ok=True)
        assert not (OUT/'activation-started').exists(),'One-shot activation already started; inspect evidence'
        save('placement.json',placement())
        before=capture(); after=desired(before)
        save('before.json',before);save('after.json',after)
        forward=patch(before,after); reverse=patch(after,before)
        save('forward.sql',forward);save('rollback.sql',reverse)
        # Session-local copies shadow every target table throughout rehearsal.
        setup=[]
        for table in SCOPES:
            setup.append(f'CREATE TEMPORARY TABLE `nc_seed_{table}` LIKE `peq`.`{table}`;')
            setup.append(f'CREATE TEMPORARY TABLE `{table}` LIKE `nc_seed_{table}`;')
            setup.extend(insert(table,row) for row in before[table])
        def verify(rows):
            checks=[];expected=[]
            for table,records in rows.items():
                checks.append(f"SELECT '{table}',COUNT(*) FROM `{table}`;")
                checks.extend(f'SELECT COUNT(*) FROM `{table}` WHERE {predicate(row)};' for row in records)
                expected += [f'{table}\t{len(records)}']+['1']*len(records)
            return '\n'.join(checks),expected
        after_checks,after_expected=verify(after);before_checks,before_expected=verify(before)
        rehearsal=sql('\n'.join(setup)+'\n'+forward+after_checks+'\n'+reverse+before_checks+'\n')
        expected=after_expected+before_expected
        assert rehearsal.splitlines()==expected,rehearsal
        assert normalized(capture())==normalized(before)
        rejected=[]
        for label,mutation in [('item drift','UPDATE items SET sellrate=2.1 WHERE id=16488;'),
                               ('occupied merchant slot','UPDATE merchantlist SET slot=19 WHERE slot=18;'),
                               ('changed donor',"UPDATE npc_types SET npc_faction_id=100 WHERE id=999600;")]:
            try: sql('\n'.join(setup)+'\n'+mutation+'\n'+forward)
            except RuntimeError as error:
                assert 'drift' in str(error),str(error)
                rejected.append(label)
            else: raise AssertionError('Unexpected acceptance: '+label)
        save('rehearsal.json',dict(forward_afterimages=True,inverse_afterimages=True,
                                   live_unchanged=True,rejected_drift=rejected))
        if preflight:
            print('Preflight passed: placement, exact forward/inverse and three rejected drift cases.',flush=True)
            return
        original_hashes=fingerprint();save('native-before.sha256',original_hashes)
        cached_before=item_cache();save('cache-before.json',cached_before)
        touched=False
        try:
            (OUT/'activation-started').touch(exist_ok=False)
            run(['docker','compose','stop','gateway'])
            run(['docker','compose','stop','-t','90','game'])
            assert normalized(capture())==normalized(before),'Content changed during shutdown'
            # Full stopped backup retained; recovery never replays player state.
            command=['docker','compose','exec','-T','db','mariadb-dump',
                     '--defaults-extra-file=/run/secrets/db_backup_config','--single-transaction',
                     '--routines','--triggers','--events','peq']
            digest=hashlib.sha256(); tail=b''; has_inventory=False
            with (OUT/'dump.stderr').open('wb') as errors, gzip.open(OUT/'peq-before.sql.gz','wb') as stream:
                process=subprocess.Popen(command,cwd=ROOT,stdout=subprocess.PIPE,stderr=errors)
                while chunk:=process.stdout.read(1024*1024):
                    has_inventory |= b'CREATE TABLE `inventory`' in tail+chunk
                    tail=(tail+chunk)[-4096:];digest.update(chunk);stream.write(chunk)
                assert process.wait(timeout=30)==0,'Backup command failed'
            assert has_inventory and b'Dump completed' in tail,'Incomplete backup'
            verified=hashlib.sha256()
            with gzip.open(OUT/'peq-before.sql.gz','rb') as stream:
                while chunk:=stream.read(1024*1024): verified.update(chunk)
            assert digest.digest()==verified.digest(),'Backup verification failed'
            save('backup.json',dict(uncompressed_sha256=digest.hexdigest(),gzip_verified=True,
                                   isolated_restore_rehearsed=False))
            preserved=sql('CHECKSUM TABLE inventory,character_data,character_currency,character_multiclass,zone_state_spawns;')
            save('preserved-before.txt',preserved)
            touched=True
            sql(forward)
            assert normalized(capture())==normalized(after)
            assert sql('CHECKSUM TABLE inventory,character_data,character_currency,character_multiclass,zone_state_spawns;')==preserved
            state=start_and_wait()
            assert fingerprint()==original_hashes
            save('cache-verification.json',check_cache(cached_before,item_cache()))
            assert normalized(capture())==normalized(after)
            run(['docker','compose','start','gateway'])
            save('result.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                merchant='Haldra',merchant_id=999603,slot=19,item=16488,sellrate=3,
                banker='Mira Coinwell',npc_id=999821,spawn_id=999821,zone='ecommons',
                loc_yxz=[-1584,-144,3.75],native_hashes_unchanged=True,
                stopped_player_and_zone_state_checksums_preserved=True,
                runtime_started_at=state['StartedAt'],player_qa='pending'))
            print((OUT/'result.json').read_text(),flush=True)
        except Exception:
            # Keep access closed on uncertain mutation/verification. Never auto-restore a database.
            if not touched:
                start_and_wait();run(['docker','compose','start','gateway'])
            raise

if __name__=='__main__':
    if sys.argv[1:] == ['capture']:
        print(json.dumps(capture(),indent=2))
    elif sys.argv[1:] == ['apply']:
        apply()
    elif sys.argv[1:] == ['preflight']:
        apply(preflight=True)
    else:
        raise SystemExit('Specify capture or apply')
