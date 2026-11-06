"""Authorized augment-only release. Explicit one-shot actions; no player restores."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
import mmap
import os
from pathlib import Path
import re
import secrets
import shutil
import struct
import subprocess
import tempfile
import time
import uuid

ROOT = Path('/opt/nightcap/deploy/production')
STAGE = Path('/opt/nightcap/releases/augment-audit-20261106-v1')
EVIDENCE = STAGE / 'evidence'
PRIOR = Path('/opt/nightcap/releases/power-source-xp-display-20261103-v1')
TAG = 'nightcap-game:augment-audit-20261106-v1'
TABLE = 'nightcap_zone_hunt_zones'
RESERVE = 2 * 1024**3


def sha(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()


def save(path, value):
    with path.open('x') as f:
        json.dump(value, f, indent=2); f.write('\n'); f.flush(); os.fsync(f.fileno())
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)


def read(path): return json.loads(path.read_text())


def sql(statement, database='peq'):
    assert database == 'peq' or re.fullmatch('nightcap_dungeon_stage_[0-9a-f]{12}', database)
    p = subprocess.run(['docker','compose','exec','-T','db','mariadb',
        '--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','--quick','--skip-column-names',database],
        cwd=ROOT, input='SET SESSION max_session_mem_used=134217728;\n'+statement,
        text=True, capture_output=True, timeout=600)
    if p.returncode:
        raise RuntimeError('Database operation failed; statement/log withheld' if 'IDENTIFIED BY' in statement else p.stderr[-1200:])
    return p.stdout


def initialize():
    global m, p, r, h, base, startup, market_ops, rows, zones
    m = read(STAGE/'manifest.json')
    expected = {'bin/zone','rollout.py','forward.sql','rollback.sql','item-preimages.json','zone-preimages.json'}
    assert set(m['files']) == expected
    for name, digest in m['files'].items():
        path = STAGE/name
        assert path.resolve().is_relative_to(STAGE) and not path.is_symlink() and sha(path)==digest, name
    assert sha(PRIOR/'rollout.py') == m['prior_rollout_sha256']
    spec = importlib.util.spec_from_file_location('prior_display',PRIOR/'rollout.py')
    p = importlib.util.module_from_spec(spec); spec.loader.exec_module(p); p.initialize()
    r,h,base,startup,market_ops = p.r,p.h,p.base,p.startup,p.market_ops
    assert read(PRIOR/'evidence/activation/deployed.json')['runtime']['image_id']==m['base_image_id']
    assert r.image_hashes(m['base_image_id'])==m['base_hashes']
    rows,zones = read(STAGE/'item-preimages.json'),read(STAGE/'zone-preimages.json')
    assert len(rows)==232 and len({int(x['before']['id']) for x in rows})==232
    assert len(zones)==56 and m['owner_deploy_authorized']=='2026-11-06 chat: Merge the augment changes to main and deploy to OVH for live QA'


def literal(v): return 'NULL' if v=='NULL' else "X'"+str(v).encode().hex()+"'"


def predicate(row, key):
    return f'`{key}`={int(row[key])} AND '+' AND '.join(f'BINARY `{k}` <=> {literal(v)}' for k,v in row.items())


def owned(after=False, database='peq'):
    queries = ['SELECT COUNT(*) FROM items WHERE '+predicate(x['after' if after else 'before'],'id') for x in rows]
    for z in zones:
        row={k:v for k,v in z.items() if k not in ('short_name','long_name')}
        if after and z['short_name'] in ('cazicthule','hateplaneb'): row['enabled']='1'
        queries.append('SELECT COUNT(*) FROM '+TABLE+' WHERE '+predicate(row,'zone_id'))
    values = sql(';\n'.join(queries)+';',database).splitlines()
    assert len(values)==288 and set(values)=={'1'},'Exact augment/config preimage or afterimage drift'


def scope_hash(table, where):
    cols=[line.split('\t') for line in sql("SELECT COLUMN_NAME,DATA_TYPE FROM information_schema.COLUMNS WHERE TABLE_SCHEMA='peq' AND TABLE_NAME='"+table+"' ORDER BY ORDINAL_POSITION;").splitlines()]
    assert cols and all(re.fullmatch('[A-Za-z_][A-Za-z0-9_]*',c[0]) for c in cols)
    expr=','.join('CAST(`'+n+'` AS DOUBLE)' if t in ('float','double') else '`'+n+'`' for n,t in cols)
    values=sorted(sql('SELECT SHA2(JSON_ARRAY('+expr+'),256) FROM `'+table+'` WHERE '+where+';').splitlines())
    return {'rows':len(values),'sha256':hashlib.sha256('\n'.join(values).encode()).hexdigest(),
            'schema_sha256':hashlib.sha256(sql('SHOW CREATE TABLE `'+table+'`;').encode()).hexdigest()}


def content():
    result={k:v for k,v in p.pl.content().items() if k.split('/')[0] not in ('items',TABLE)}
    ids=','.join(str(int(x['before']['id'])) for x in rows)
    result['items/outside-augment-release']=scope_hash('items','id NOT IN ('+ids+')')
    result[TABLE+'/outside-enable-flags']=scope_hash(TABLE,'zone_id NOT IN (48,186)')
    return result


def contract_data(): return read(Path(h.manifest()['contract']['path']))


def contract(overrides=None):
    overrides=overrides or {}; data=contract_data(); result={}
    for family,checks in data.items():
        values=sql(';\n'.join(c['sql'] for c in checks)+';').splitlines()
        assert len(values)==len(checks)
        for c,value in zip(checks,values):
            key=family+'/'+c['label']; expected=c['expected']
            if key in overrides:
                delta=overrides[key]
                assert delta['before']==expected and delta['sql_sha256']==hashlib.sha256(c['sql'].encode()).hexdigest()
                expected=delta['after']
            assert value==expected,'Content contract: '+key
        result[family]=len(checks)
    return result


def records(path):
    result={}
    with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as data:
        payload,count,maximum,current=struct.unpack_from('<IIII',data,0)
        assert maximum==current and len(data)==payload+8==20+4*count+1332*maximum
        start=16+4*count
        for item in range(count):
            index=struct.unpack_from('<I',data,16+item*4)[0]
            if index<current:
                value=data[start+index*1332:start+(index+1)*1332]
                assert struct.unpack_from('<I',value,440)[0]==item
                result[item]=hashlib.sha256(value).hexdigest()
    assert len(result)==current
    return result


def compare_cache(before,after):
    ids={int(x['before']['id']) for x in rows}
    assert set(before)==set(after),'Item cache identity set changed'
    changed={i for i in before if before[i]!=after[i]}
    assert changed==ids,('Wrong item cache changes',len(changed),len(ids))
    return {'definitions':len(after),'changed_augments':len(changed),'unrelated_preserved':len(after)-len(changed),
            'records_sha256':hashlib.sha256(json.dumps(after,sort_keys=True).encode()).hexdigest()}


def binaries(candidate=True): return {**p.binaries(),**({'zone':m['files']['bin/zone']} if candidate else {})}


def unchanged(before,installed=False):
    for service in ('db','web','tunnel'): assert r.compact(service)==before['services'][service],service
    assert r.runtime()==before['runtime'],'Quest/config drift'
    assert h.publication()==before['publication'],'Public client/wiki drift'
    assert p.pl.rules()==before['rules'],'Rule catalog drift'
    assert content()==before['content'],'Unrelated content drift'
    caches=h.caches(); assert caches['spells']==before['caches']['spells']
    expected=before['rehearsal']['cache_sha256'] if installed else before['caches']['items']
    assert caches['items']==expected,'Item cache drift'


def build_image():
    old=TAG+'-base'; r.call('docker','tag',m['base_image_id'],old)
    (STAGE/'Dockerfile').write_text('FROM '+old+'\nCOPY bin/zone /opt/nightcap/bin/zone\n')
    (STAGE/'.dockerignore').write_text('*\n!Dockerfile\n!.dockerignore\n!bin\n!bin/zone\n')
    r.call('docker','build','--pull=false','--network','none','-t',TAG,str(STAGE))
    image=r.out('docker','image','inspect','--format','{{.Id}}',TAG).strip()
    layers=lambda x:json.loads(r.out('docker','image','inspect',x))[0]['RootFS']['Layers']
    assert layers(image)[:-1]==layers(m['base_image_id'])
    assert r.image_hashes(image)=={**m['base_hashes'],'bin/zone':m['files']['bin/zone']}
    assert 'not found' not in r.out('docker','run','--rm','--network','none','--entrypoint','ldd',image,'/opt/nightcap/bin/zone')
    r.call('docker','run','--rm','--network','none','--entrypoint','python3',image,'-c','import sys;sys.path.insert(0,"/opt/nightcap");import start;start.validate_native()')
    return image


def rehearsal(image):
    database='nightcap_dungeon_stage_'+uuid.uuid4().hex[:12]; user='na_'+uuid.uuid4().hex[:12]; password=secrets.token_hex(24)
    runtime=STAGE/'rehearsal'; runtime.mkdir(mode=0o700); (runtime/'shared').mkdir(); (runtime/'logs').mkdir()
    tables={'items','spells_new',TABLE,'nightcap_zone_hunt_state','rule_values','rule_sets','variables','logsys_categories','content_flags'}
    sql('CREATE DATABASE `'+database+'`;')
    for table in sorted(tables): sql(f'CREATE TABLE `{database}`.`{table}` LIKE peq.`{table}`;')
    sql('START TRANSACTION WITH CONSISTENT SNAPSHOT;\n'+'\n'.join(f'INSERT INTO `{database}`.`{t}` SELECT * FROM peq.`{t}`;' for t in sorted(tables))+'\nCOMMIT;')
    owned(False,database)
    sql(f"CREATE USER '{user}'@'%' IDENTIFIED BY '{password}'; GRANT ALL ON `{database}`.* TO '{user}'@'%';")
    cfg=runtime/'eqemu_config.json'
    try:
        config=read(ROOT/'private/eqemu_config.json'); connection=config['server']['database']
        connection.update(db=database,username=user,password=password);config['server']['content_database']=dict(connection)
        config['server'].setdefault('directories',{}).update(shared_memory='/runtime/shared/',logs='/runtime/logs/')
        cfg.write_text(json.dumps(config));cfg.chmod(0o600)
        networks=list(r.state('db')['NetworkSettings']['Networks']);assert len(networks)==1
        def loader(target,label):
            args=['docker','run','--rm','--network',networks[0],'--user','0','-v',str(runtime)+':/runtime','--workdir','/runtime','--entrypoint','/opt/nightcap/bin/shared_memory',target,'items']
            with (runtime/(label+'.log')).open('x') as log:
                proc=subprocess.run(args,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=240)
            assert proc.returncode==0,'Isolated loader failed; private log retained'
        loader(m['base_image_id'],'before')
        before_path=runtime/'before-items';(runtime/'shared/items').rename(before_path)
        before=records(before_path);assert before==records(ROOT/'data/server/shared/items'),'Fresh baseline cache differs from live'
        plan=sql('EXPLAIN SELECT id FROM items WHERE id=940024;',database).split('\t');assert plan[5]=='ID' and plan[8]=='1'
        sql((STAGE/'forward.sql').read_text(),database);owned(True,database)
        loader(image,'after');after=records(runtime/'shared/items');cache=compare_cache(before,after)
        overrides={}
        pattern=re.compile(r'\b(FROM|JOIN)\s+(`?)(items|nightcap_zone_hunt_zones)\2(?=\s|[;,.)]|$)',re.I)
        for family,checks in contract_data().items():
            for check in checks:
                rewritten=pattern.sub(lambda x:x[1]+' `'+database+'`.`'+x[3]+'`',check['sql'])
                if rewritten==check['sql']:continue
                value=sql(rewritten).strip()
                if value!=check['expected']:
                    overrides[family+'/'+check['label']]={'before':check['expected'],'after':value,'sql_sha256':hashlib.sha256(check['sql'].encode()).hexdigest()}
        sql((STAGE/'rollback.sql').read_text(),database);owned(False,database)
        result={'database':database,'cache':cache,'cache_sha256':sha(runtime/'shared/items'),'contract_overrides':overrides,
                'forward_inverse':'passed on full production item catalog','indexed_item_lookup':'ID, one row'}
        save(runtime/'evidence.json',result);return result
    finally:
        cfg.unlink(missing_ok=True);sql(f"DROP USER '{user}'@'%';")


def preflight():
    assert not EVIDENCE.exists(),'Inspect prior attempt; never replay'
    services={s:r.compact(s) for s in ('game','gateway','db','web','tunnel')}
    assert all(v['running'] and not v['oom_killed'] for v in services.values())
    assert services['game']['image_id']==m['base_image_id'] and services['game']['health']==services['db']['health']=='healthy'
    r.running(m['base_image_id'],binaries(False),services['game']['restarts']);base.health();startup.startup_guards();r.closed_ports();owned()
    assert shutil.disk_usage(ROOT).free>RESERVE+2*1024**3
    checks=contract()
    before={'manifest_sha256':sha(STAGE/'manifest.json'),'services':services,'runtime':r.runtime(),
            'publication':h.publication(),'caches':h.caches(),'content':content(),'rules':p.pl.rules(),'checks':checks}
    EVIDENCE.mkdir(mode=0o700);save(EVIDENCE/'preflight-started.json',before)
    before['image']=build_image();before['rehearsal']=rehearsal(before['image']);unchanged(before)
    assert all(r.compact(s)==v for s,v in services.items())
    save(EVIDENCE/'preflight.json',before)
    print(json.dumps({'status':'preflight passed; gameplay/access unchanged','cache':before['rehearsal']['cache'],
                      'contract_overrides':before['rehearsal']['contract_overrides'],'free_bytes':shutil.disk_usage(ROOT).free}),flush=True)


def activate():
    before=read(EVIDENCE/'preflight.json');folder=EVIDENCE/'activation'
    assert before['manifest_sha256']==sha(STAGE/'manifest.json') and not folder.exists(),'Never replay a transition'
    unchanged(before);owned();startup.startup_guards();contract()
    assert all(r.compact(s)==v for s,v in before['services'].items())
    assert shutil.disk_usage(ROOT).free>RESERVE
    folder.mkdir(mode=0o700);save(folder/'started.json',{'image':before['image']})
    try:
        r.compose('stop','gateway');start=time.monotonic();r.compose('stop','-t','90','game')
        assert time.monotonic()-start<70
        state=r.state('game')['State'];assert not state['Running'] and state['ExitCode']==0 and not state['OOMKilled']
        startup.startup_guards();unchanged(before);owned()
        data=base.saved_state();market=market_ops.market();save(folder/'stopped-state.json',data);save(folder/'market-before.json',market)
        r.STAGE=folder;base.EVIDENCE=folder;save(folder/'backup.json',r.database_backup());assert base.saved_state()==data
        assert shutil.disk_usage(ROOT).free>RESERVE
        save(folder/'sql-started.json',{'forward_sha256':m['files']['forward.sql']})
        sql((STAGE/'forward.sql').read_text());owned(True)
        after=base.saved_state();assert {k:v for k,v in after.items() if k!=TABLE}=={k:v for k,v in data.items() if k!=TABLE},'Unexpected saved-table mutation'
        assert content()==before['content'] and p.pl.rules()==before['rules']
        save(folder/'sql-installed.json',{'changed_items':232,'enable_flags':[48,186]})
        base.boot_state(after)
        r.select(before['image']);r.compose('up','-d','--wait','--wait-timeout','240','game')
        first=r.running(before['image'],binaries());base.health();time.sleep(8)
        current=r.running(before['image'],binaries());assert current['started_at']==first['started_at']
        logs=r.out('docker','compose','logs','--no-color','--since',current['started_at'],'game')
        assert not any(s in logs for s in ('MySQL Error','Orphaned Rule','Unknown column'))
        cache=compare_cache(records(STAGE/'rehearsal/before-items'),records(ROOT/'data/server/shared/items'))
        assert cache==before['rehearsal']['cache']
        rotation=market_ops.verify_market(market,current['started_at'])
        assert base.saved_state()==read(folder/'expected-boot-state.json'),'Saved state drift'
        checks=contract(before['rehearsal']['contract_overrides']);unchanged(before,True);owned(True);base.health();r.closed_ports()
        assert not r.state('gateway')['State']['Running']
        save(folder/'verified-closed.json',{'runtime':current,'game':r.compact('game'),'cache':cache,'market':rotation,'checks':checks})
        print('Native/cache/content/player-state verification passed; access remains closed.',flush=True)
    except BaseException:h.hold(folder);raise


def rollback():
    before=read(EVIDENCE/'preflight.json');activation=EVIDENCE/'activation';folder=EVIDENCE/'rollback'
    assert list(activation.glob('held-*.json')) and not (activation/'opening.json').exists() and not folder.exists()
    assert not r.state('gateway')['State']['Running'] and not r.state('game')['State']['Running']
    folder.mkdir(mode=0o700);save(folder/'started.json',{'base_image':m['base_image_id']})
    try:
        try: owned(True)
        except AssertionError: owned(False)  # Only a complete known before-state is also safe.
        else:
            save(folder/'inverse-started.json',{'rollback_sha256':m['files']['rollback.sql']})
            sql((STAGE/'rollback.sql').read_text());owned(False)
        data=base.saved_state();market=market_ops.market();base.EVIDENCE=folder;base.boot_state(data)
        r.select(m['base_image_id']);r.compose('up','-d','--wait','--wait-timeout','240','game')
        current=r.running(m['base_image_id'],binaries(False));base.health()
        assert base.saved_state()==read(folder/'expected-boot-state.json')
        unchanged(before);contract();owned(False);market_ops.verify_market(market,current['started_at']);r.closed_ports()
        save(folder/'verified-closed.json',{'runtime':current,'game':r.compact('game'),'content_inverse_verified':True})
        print('Content inverse and compatible base runtime restored; access closed.',flush=True)
    except BaseException:h.hold(folder);raise


def open_access():
    before=read(EVIDENCE/'preflight.json');folder=EVIDENCE/('rollback' if (EVIDENCE/'rollback').exists() else 'activation')
    candidate=folder.name=='activation';a=read(folder/'verified-closed.json')
    assert not list(folder.glob('held-*.json')) and not (folder/'opening.json').exists()
    try:
        assert not r.state('gateway')['State']['Running'] and r.compact('game')==a['game']
        assert base.saved_state()==read(folder/'expected-boot-state.json')
        unchanged(before,candidate);owned(candidate);contract(before['rehearsal']['contract_overrides'] if candidate else {});base.health();r.closed_ports()
        save(folder/'opening.json',{'owner_authorized':True})
        r.compose('up','-d','--wait','--wait-timeout','60','gateway')
        current=r.running(before['image'] if candidate else m['base_image_id'],binaries(candidate));assert current['started_at']==a['runtime']['started_at']
        unchanged(before,candidate);base.health();r.closed_ports();assert r.state('gateway')['State']['Running']
        save(folder/'deployed.json',{**a,'runtime':current,'gateway_open':True,'changed_items':232 if candidate else 0,'zone_enable_flags':[48,186] if candidate else [],
             'database_restored':False,'owner_gameplay_accepted':False,'client_update_required':False})
        print('Augments deployed for live QA; access restored; no client update.' if candidate else 'Compatible base restored; access reopened after verified inverse.',flush=True)
    except BaseException:h.hold(folder);raise


def main():
    assert __debug__;os.umask(0o077);initialize()
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('preflight','activate','rollback','open'))
    action=parser.parse_args().action
    with (ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (ROOT/'private/gm-maintenance.json').exists()
        assert sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1'
        {'preflight':preflight,'activate':activate,'rollback':rollback,'open':open_access}[action]()


if __name__=='__main__':main()
