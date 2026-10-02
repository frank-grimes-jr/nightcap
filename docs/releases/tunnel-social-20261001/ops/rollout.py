"""Scoped production social tunnel deployment; private preimages remain on the host."""
import argparse
import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

if not __debug__:
    raise RuntimeError('Assertions must be enabled')
STAGE=Path(__file__).resolve().parent
ROOT=Path('/opt/nightcap/deploy/production')
EVIDENCE=Path('/opt/nightcap/releases/tunnel-social-evidence-20261001')
REHEARSAL='nightcap-social-rehearsal-20261001'
sys.path.insert(0,str(STAGE/'tools'))
import tunnel_social as content

def digest(data):return hashlib.sha256(data).hexdigest()
def out(*args,**kw):return subprocess.check_output(args,cwd=ROOT,text=True,**kw)
def call(*args,**kw):return subprocess.run(args,cwd=ROOT,check=True,**kw)
def compose(*args):return call('docker','compose',*args)
def load(name):return json.loads((EVIDENCE/name).read_text())
def save(name,value):
    with (EVIDENCE/name).open('x') as f:json.dump(value,f,indent=2);f.write('\n')
def sql(query,isolated=False,check=True,database='peq'):
    args=['docker','exec','-i',REHEARSAL,'mariadb','-uroot'] if isolated else [
        'docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config']
    result=subprocess.run(args+['--batch','--raw','--skip-column-names',database],
        cwd=ROOT,input=query,text=True,capture_output=True,timeout=180)
    if check and result.returncode:
        raise RuntimeError('SQL failed; inspect private host evidence')
    return result if not check else result.stdout


def runtime_files():
    root=ROOT/'data/server'
    return {str(p.relative_to(root)):digest(p.read_bytes()) for directory in ('quests','plugins','lua_modules')
            for p in (root/directory).rglob('*') if p.is_file() and p.suffix in ('.pl','.lua','.json')}

def scene_hash():
    queries={
        'spawn2':"zone='ecommons'",
        'spawnentry':"spawngroupID IN (SELECT spawngroupID FROM spawn2 WHERE zone='ecommons')",
        'npc_types':"id IN (SELECT e.npcID FROM spawnentry e JOIN spawn2 s ON e.spawngroupID=s.spawngroupID WHERE s.zone='ecommons')",
        'grid':'zoneid=22','grid_entries':'zoneid=22','object':'zoneid=22','doors':"zone='ecommons'"}
    result={}
    for table,where in queries.items():
        result[table]=digest('\n'.join(sorted(sql('SELECT * FROM `'+table+'` WHERE '+where+';').splitlines())).encode())
    return digest(json.dumps(result,sort_keys=True).encode())

def verify_geometry_inputs(m):
    for name,sha in m['maps'].items():
        assert Path(name).name==name and name.endswith('.map')
        assert digest((ROOT/'data/server/maps/base'/name).read_bytes())==sha,'Map drift: '+name
    query="SELECT short_name,zoneidnumber,COALESCE(NULLIF(map_file_name,''),short_name),expansion,min_status,min_level FROM zone WHERE version=0 AND short_name IN ("+','.join("'"+n+"'" for n in m['zones'])+');'
    zones={r[0]:r for r in (line.split('\t') for line in sql(query).splitlines())}
    assert zones==m['zones'],'Wizard zone metadata drift'

def verify_quests(m):
    # docker cp cannot write through this image's read-only root filesystem.
    # Use exec stdin into /tmp, then test the actual installed quest files.
    for name in ('tunnel_social_quests.t','tunnel_residents_quests.t','tunnel_spires_quests.t'):
        path='/tmp/'+name
        code="import sys;from pathlib import Path;Path(sys.argv[1]).write_bytes(sys.stdin.buffer.read())"
        call('docker','compose','exec','-T','game','python3','-c',code,path,
             input=(STAGE/'tools/tests'/name).read_bytes())
        call('docker','compose','exec','-T','game','perl',path,'/srv/nightcap')

def manifest():
    assert STAGE==Path('/opt/nightcap/releases/tunnel-social-20261001')
    assert Path(__file__).resolve()==STAGE/'rollout.py','Use the pinned staged helper'
    m=json.loads((STAGE/'manifest.json').read_text())
    for name,sha in m['files'].items():assert digest((STAGE/name).read_bytes())==sha,name
    return m
def state(service):
    cid=out('docker','compose','ps','-aq',service).strip()
    assert cid,service+' missing'
    return json.loads(out('docker','inspect',cid))[0]
def stopped():
    assert all(not state(s)['State']['Running'] for s in ('game','gateway'))
def new_files(m):
    for entry in m['runtime']:
        path=ROOT/'data/server'/entry['target']
        assert path.parent.is_dir() and not path.is_symlink(),str(path)
        actual=digest(path.read_bytes()) if path.exists() else None
        assert actual==entry.get('before_sha256'),'Runtime preimage drift: '+entry['target']

def backup_runtime(m):
    metadata={}
    for e in m['runtime']:
        path=ROOT/'data/server'/e['target']
        if e.get('before_sha256') is None:continue
        target=EVIDENCE/'runtime-before'/e['target'];target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f:f.write(path.read_bytes())
        st=path.stat();metadata[e['target']]=dict(mode=st.st_mode & 0o777,uid=st.st_uid,gid=st.st_gid)
        assert digest(target.read_bytes())==e['before_sha256']
    save('runtime-before.json',metadata)

def installed_files(m):
    for e in m['runtime']:assert digest((ROOT/'data/server'/e['target']).read_bytes())==e['sha256']
def fingerprints(isolated=False):
    tables=sql("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA='peq' AND (TABLE_NAME LIKE 'character\\_%' OR TABLE_NAME IN ('account','inventory','quest_globals','starting_items','nightcap_market_trades','rule_values','object_contents','items')) ORDER BY TABLE_NAME;",isolated).splitlines()
    result={}
    for table in tables+['merchantlist','zone_state_spawns']+[t for t in content.KEYS if t!='zone_state_spawns']:
        where=' WHERE NOT ('+content.SCOPES[table]+')' if table in content.SCOPES else ''
        rows=sql('SELECT * FROM `'+table+'`'+where+';',isolated).splitlines()
        result[table]=dict(rows=len(rows),sha256=digest('\n'.join(sorted(rows)).encode()))
    return result
def matches(current,expected,allow_saved=False):
    for table in content.KEYS:
        if allow_saved and table=='zone_state_spawns':continue
        norm=lambda rows:sorted(json.dumps(r,sort_keys=True) for r in rows)
        if norm(current['rows'][table])!=norm(expected['rows'][table]):return False
    return True
def exact(expected,isolated=False,allow_saved=False):
    current=content.capture(lambda q:sql(q,isolated))
    assert matches(current,expected,allow_saved),'Scoped content drift'
    if allow_saved:
        content.rollback_target(load('before-content.json'),current,expected)
    return current
def artifacts():
    return {n:digest((EVIDENCE/n).read_bytes()) for n in (
        'before-content.json','after-content.json','forward.sql','immediate-rollback.sql','rollback-target.json','peq-before.sql.gz')}
def verified_target():
    assert artifacts()==load('prepared.json')['artifacts_sha256'],'Prepared target drift'

def running(m,restart_count=0):
    s=state('game')
    assert s['Image']==m['image_id'] and s['Config']['Image']==m['image']
    assert s['State']['Health']['Status']=='healthy' and s['RestartCount']==restart_count
    code="from pathlib import Path;import hashlib,json;rows=[]\nfor p in Path('/proc').iterdir():\n if p.name.isdigit():\n  try:\n   e=p/'exe';n=e.resolve().name\n   if n in {'world','zone','ucs','loginserver'}:rows.append([n,hashlib.sha256(e.read_bytes()).hexdigest()])\n  except (FileNotFoundError,PermissionError):pass\nprint(json.dumps(rows))"
    rows=json.loads(out('docker','compose','exec','-T','game','python3','-c',code))
    assert sum(n=='zone' for n,h in rows)==12
    assert all(sum(n==k for n,h in rows)==1 for k in ('world','ucs','loginserver'))
    assert all(m['binaries']['bin/'+n]==h for n,h in rows)
    logs=out('docker','compose','logs','--no-color','--since',s['State']['StartedAt'],'game',stderr=subprocess.DEVNULL)
    patterns={'quest_api':r"Can't locate object method|Undefined subroutine|Perl runtime error",
              'native':r'Segmentation fault|core dumped|a native process exited',
              'database':r'Unknown column|SQL syntax|does not exist.*nightcap_market'}
    errors={name:len(re.findall(pattern,logs,re.I)) for name,pattern in patterns.items()}
    assert not any(errors.values()),str(errors)
    return dict(image_id=s['Image'],native_processes=len(rows),hashes_match=True,
                started_at=s['State']['StartedAt'],restart_count=s['RestartCount'],errors=errors)

def preflight():
    m=manifest();new_files(m);health=running(m,m['baseline_restarts'])
    assert state('gateway')['State']['Running']
    assert shutil.disk_usage(ROOT).free>8_000_000_000
    cfg=json.loads(out('docker','compose','config','--format','json'))
    assert cfg['services']['game']['image']==m['image']
    # Validate the live target before entering maintenance. Recapture after shutdown.
    before=content.capture(sql);content.desired(before)
    assert scene_hash()==m['scene_sha256'],'Tunnel geometry content drift'
    dirs=json.loads((ROOT/'private/eqemu_config.json').read_text())['server']['directories']
    assert dirs.get('plugin_paths') in (None,[],['plugins/']) and dirs.get('quest_paths') in (None,[],['quests/']) and dirs.get('plugins','plugins/')=='plugins/' and dirs.get('quests','quests/')=='quests/','Runtime path drift'
    verify_geometry_inputs(m)
    assert not EVIDENCE.exists();EVIDENCE.mkdir(mode=0o700)
    save('preflight.json',dict(health=health,runtime=runtime_files()))
    print(json.dumps(dict(preflight='passed',source_commit=m['source_commit'],runtime_files=len(m['runtime']))),flush=True)

def backup():
    path=EVIDENCE/'peq-before.sql.gz'
    with path.open('xb') as f:
        proc=subprocess.Popen(['docker','compose','exec','-T','db','mariadb-dump',
            '--defaults-extra-file=/run/secrets/db_backup_config','--single-transaction',
            '--routines','--triggers','--events','--hex-blob','peq'],cwd=ROOT,stdout=subprocess.PIPE)
        try:
            with gzip.GzipFile(fileobj=f,mode='wb') as zipped:shutil.copyfileobj(proc.stdout,zipped,1024*1024)
        finally:proc.stdout.close()
        assert proc.wait()==0,'Backup failed'
    with gzip.open(path,'rb') as f:size=sum(len(c) for c in iter(lambda:f.read(1024*1024),b''))
    assert size>100_000_000
    save('backup.json',dict(sha256=digest(path.read_bytes()),uncompressed_bytes=size))

def rehearse(before,after):
    image=state('db')['Image']
    assert not out('docker','ps','-aq','--filter','name=^/'+REHEARSAL+'$').strip()
    call('docker','run','-d','--rm','--name',REHEARSAL,'--label','nightcap.release=tunnel-social-20261001',
         '--network','none','--memory','1536m','-e','MARIADB_ALLOW_EMPTY_ROOT_PASSWORD=1',image)
    try:
        for _ in range(60):
            ready=subprocess.run(['docker','exec',REHEARSAL,'mariadb-admin','-uroot','ping'],capture_output=True)
            daemon=subprocess.run(['docker','exec',REHEARSAL,'cat','/proc/1/comm'],capture_output=True,text=True)
            if ready.returncode==0 and daemon.stdout.strip()=='mariadbd':break
            time.sleep(1)
        else:raise RuntimeError('Isolated database startup timeout')
        call('docker','exec',REHEARSAL,'mariadb','-uroot','-e','CREATE DATABASE peq;')
        call('docker','cp',str(EVIDENCE/'peq-before.sql.gz'),REHEARSAL+':/tmp/backup.sql.gz')
        with (EVIDENCE/'restore-private.log').open('xb') as errors:
            restored=subprocess.run(['docker','exec',REHEARSAL,'bash','-o','pipefail','-c',
                'gzip -dc /tmp/backup.sql.gz | mariadb -uroot peq'],stdout=errors,stderr=errors,timeout=300)
        assert restored.returncode==0,'Restore failed; inspect private host log'
        baseline=load('preservation-before.json')
        assert fingerprints(True)==baseline;exact(before,True)
        print('Full production backup restored and verified in isolation.',flush=True)
        sys.path.insert(0,str(STAGE/'tools/tests'))
        import rehearse_tunnel_social as tests
        tests.sql=lambda q,check=True:sql(q,True,False) if not check else checked_test_sql(q)
        checks=tests.run(EVIDENCE/'before-content.json',EVIDENCE/'regression')
        assert len(checks)==17
        sql((EVIDENCE/'forward.sql').read_text(),True);exact(after,True)
        assert fingerprints(True)==baseline
        sql((EVIDENCE/'immediate-rollback.sql').read_text(),True);exact(load('rollback-target.json'),True)
        assert fingerprints(True)==baseline
        save('rehearsal.json',dict(full_backup_restored=True,checks=checks,
            exact_full_database_forward=True,exact_full_database_rollback=True,preserved_tables=len(baseline)))
    finally:
        inspected=json.loads(out('docker','inspect',REHEARSAL))[0]
        assert inspected['Config']['Labels'].get('nightcap.release')=='tunnel-social-20261001'
        call('docker','stop',REHEARSAL)
    assert not out('docker','ps','-aq','--filter','name=^/'+REHEARSAL+'$').strip()

def checked_test_sql(query):
    result=sql(query,True,False)
    if result.returncode:raise RuntimeError('Rehearsal SQL failed; inspect private host evidence')
    return result

def prepare():
    m=manifest();assert (EVIDENCE/'preflight.json').exists()
    health=running(m,m['baseline_restarts']);new_files(m)
    assert health['started_at']==load('preflight.json')['health']['started_at'],'Game restarted after preflight'
    assert runtime_files()==load('preflight.json')['runtime'],'Runtime file drift'
    assert scene_hash()==m['scene_sha256'],'Tunnel geometry content drift'
    compose('stop','gateway');compose('stop','-t','90','game');stopped()
    verify_geometry_inputs(m)
    assert state('game')['State']['ExitCode']==0 and not state('game')['State'].get('OOMKilled',False),'Runtime did not shut down cleanly'
    save('preservation-before.json',fingerprints())
    save('epoch-before.json',dict(epoch=int(sql('SELECT epoch FROM nightcap_market_state;'))))
    backup();backup_runtime(m)
    before=content.capture(sql);after=content.desired(before)
    save('before-content.json',before);save('after-content.json',after)
    (EVIDENCE/'forward.sql').write_text(content.patch_sql(before,after))
    target=content.rollback_target(before,after,after)
    save('rollback-target.json',target)
    (EVIDENCE/'immediate-rollback.sql').write_text(content.patch_sql(after,target))
    rehearse(before,after)
    exact(before);assert fingerprints()==load('preservation-before.json')
    save('prepared.json',dict(artifacts_sha256=artifacts()))
    print(json.dumps(dict(prepared=True,live_content_changed=False)),flush=True)

def install(m):
    new_files(m)
    for entry in m['runtime']:
        path=ROOT/'data/server'/entry['target'];data=(STAGE/entry['source']).read_bytes()
        assert digest(data)==entry['sha256']
        temp=path.with_name(path.name+'.social-pending');created=False
        try:
            with temp.open('xb') as f:
                created=True;f.write(data);f.flush();os.fsync(f.fileno())
            temp.chmod(0o644);os.chown(temp,1000,1000)
            actual=digest(path.read_bytes()) if path.exists() else None
            assert actual==entry.get('before_sha256'),'Runtime raced during installation'
            if entry.get('before_sha256') is None:os.link(temp,path)
            else:os.replace(temp,path)
        finally:
            if created and temp.exists():temp.unlink()

def restore_runtime(m):
    metadata=load('runtime-before.json') if (EVIDENCE/'runtime-before.json').exists() else {}
    for e in m['runtime']:
        path=ROOT/'data/server'/e['target']
        actual=digest(path.read_bytes()) if path.exists() else None
        if actual==e.get('before_sha256'):continue
        assert actual==e['sha256'],'Unexpected file during rollback: '+e['target']
        if e.get('before_sha256') is None:
            path.unlink();continue
        backup=EVIDENCE/'runtime-before'/e['target'];data=backup.read_bytes()
        assert digest(data)==e['before_sha256'],'Runtime backup drift'
        st=metadata[e['target']];temp=path.with_name(path.name+'.social-rollback');created=False
        try:
            with temp.open('xb') as f:
                created=True;f.write(data);f.flush();os.fsync(f.fileno())
            temp.chmod(st['mode']);os.chown(temp,st['uid'],st['gid']);os.replace(temp,path)
        finally:
            if created and temp.exists():temp.unlink()
    assert runtime_files()==load('preflight.json')['runtime'],'Unrelated runtime drift on rollback'

def apply():
    m=manifest();stopped();new_files(m);verified_target()
    verify_geometry_inputs(m)
    assert scene_hash()==m['scene_sha256'],'Tunnel geometry content drift'
    assert runtime_files()==load('preflight.json')['runtime'],'Runtime file drift'
    assert fingerprints()==load('preservation-before.json')
    save('apply-started.json',dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    sql((EVIDENCE/'forward.sql').read_text());exact(load('after-content.json'))
    assert fingerprints()==load('preservation-before.json')
    install(m);installed_files(m)
    expected_runtime={**load('preflight.json')['runtime'],**{e['target']:e['sha256'] for e in m['runtime']}}
    assert runtime_files()==expected_runtime,'Unrelated runtime files changed'
    # Recreate with the pinned image so this activation starts its own restart counter.
    compose('up','-d','--no-deps','--force-recreate','--wait','--wait-timeout','240','game')
    health=running(m);installed_files(m)
    assert runtime_files()==expected_runtime,'Runtime changed on boot'
    verify_quests(m)
    exact(load('after-content.json'),allow_saved=True)
    assert fingerprints()==load('preservation-before.json'),'Preservation failed; gateway remains closed'
    epoch=int(sql('SELECT epoch FROM nightcap_market_state;'))
    assert epoch==load('epoch-before.json')['epoch']+1
    offers=sql('SELECT kind,COUNT(*),SUM(remaining) FROM nightcap_market_offers GROUP BY kind;').splitlines()
    assert sorted(offers)==sorted(['find\t10\t10','sell\t20\t20','buy\t12\t12'])
    for e in m['runtime']:call('docker','compose','exec','-T','game','perl','-c','/srv/nightcap/'+e['target'])
    health.update(source_commit=m['source_commit'],preserved_tables=len(fingerprints()),
                  runtime_files=len(m['runtime']),exact_static_afterimages=True,epoch=epoch)
    save('verified-before-open.json',health)
    try:
        compose('up','-d','--wait','--wait-timeout','60','gateway')
        assert state('gateway')['State']['Running']
        health['gateway_running']=True;save('opened-awaiting-public.json',health)
        print(json.dumps(health),flush=True)
    except BaseException:
        compose('stop','gateway');raise

def rollback():
    m=manifest();compose('stop','gateway');compose('stop','-t','90','game');stopped()
    baseline=fingerprints()
    if not (EVIDENCE/'verified-before-open.json').exists():
        assert baseline==load('preservation-before.json'),'Investigate pre-open preservation mismatch'
    if (EVIDENCE/'apply-started.json').exists():
        verified_target();before=load('before-content.json');after=load('after-content.json')
        current=content.capture(sql)
        if not matches(current,before,allow_saved=True):
            target=content.rollback_target(before,current,after)
            rollback_sql=content.patch_sql(current,target)
            (EVIDENCE/('rollback-'+str(time.time_ns())+'.sql')).write_text(rollback_sql)
            sql(rollback_sql);exact(target)
    restore_runtime(m)
    compose('up','-d','--no-deps','--force-recreate','--wait','--wait-timeout','240','game')
    report=running(m);assert fingerprints()==baseline
    try:
        compose('up','-d','--wait','--wait-timeout','60','gateway')
        assert state('gateway')['State']['Running']
        report.update(rollback=True,player_data_preserved=True,gateway_running=True)
        save('rollback-'+str(time.time_ns())+'.json',report);print(json.dumps(report),flush=True)
    except BaseException:
        compose('stop','gateway');raise

def verify():
    # Read-only static/health verification after play; old player fingerprints
    # must not be compared with legitimate subsequent character changes.
    m=manifest();report=running(m);installed_files(m)
    verify_geometry_inputs(m)
    exact(load('after-content.json'),allow_saved=True)
    assert state('gateway')['State']['Running']
    report.update(exact_static_afterimages=True,runtime_files=len(m['runtime']),gateway_running=True)
    print(json.dumps(report))

if __name__=='__main__':
    os.umask(0o077)
    p=argparse.ArgumentParser();p.add_argument('action',choices=['preflight','prepare','apply','rollback','verify'])
    globals()[p.parse_args().action]()
