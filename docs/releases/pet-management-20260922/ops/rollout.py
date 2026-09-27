"""Paired pet release: image-only rollout; private backups remain on OVH."""
import argparse,gzip,hashlib,json,os,re,shutil,subprocess,time
from pathlib import Path
if not __debug__: raise RuntimeError('Assertions must be enabled')
ROOT=Path('/opt/nightcap/deploy/production')
STAGE=Path('/opt/nightcap/releases/pet-management-20260922')
EVIDENCE=Path('/opt/nightcap/releases/pet-management-evidence-20260922')
REHEARSAL='nightcap-pet-rehearsal-20260922'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def out(*a,**k):return subprocess.check_output(a,cwd=ROOT,text=True,**k)
def call(*a,**k):return subprocess.run(a,cwd=ROOT,check=True,**k)
def compose(*a):return call('docker','compose',*a)
def save(n,v):
    with (EVIDENCE/n).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def load(n):return json.loads((EVIDENCE/n).read_text())
def state(service):
    cid=out('docker','compose','ps','-aq',service).strip();assert cid
    return json.loads(out('docker','inspect',cid))[0]
def sql(q,isolated=False):
    a=['docker','exec','-i',REHEARSAL,'mariadb','-uroot'] if isolated else ['docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config']
    r=subprocess.run(a+['--batch','--raw','--skip-column-names','peq'],cwd=ROOT,input=q,text=True,capture_output=True,timeout=180)
    if r.returncode:raise RuntimeError('Database verification failed; no raw rows exported')
    return r.stdout

def fingerprints(isolated=False):
    tables=sql("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA='peq' AND (TABLE_NAME LIKE 'character\\_%' OR TABLE_NAME IN ('account','inventory','quest_globals','starting_items','nightcap_market_trades','rule_values')) ORDER BY TABLE_NAME;",isolated).splitlines()
    result={}
    for table in tables+['merchantlist']:
        assert re.fullmatch('[a-z_]+',table)
        where=' WHERE merchantid NOT BETWEEN 999600 AND 999639' if table=='merchantlist' else ''
        rows=sql('SELECT * FROM `'+table+'`'+where+';',isolated).splitlines()
        result[table]={'rows':len(rows),'sha256':hashlib.sha256('\n'.join(sorted(rows)).encode()).hexdigest()}
    return result

def runtime_files():
    root=ROOT/'data/server'
    return {str(p.relative_to(root)):sha(p) for directory in ('quests','plugins','lua_modules')
            for p in (root/directory).rglob('*') if p.is_file() and p.suffix in ('.pl','.lua','.json')}

def manifest():
    assert Path(__file__).resolve()==STAGE/'rollout.py'
    m=json.loads((STAGE/'manifest.json').read_text())
    for n,h in m['files'].items():
        p=STAGE/n;assert p.resolve().is_relative_to(STAGE.resolve()) and sha(p)==h,n
    assert set(m['binaries'])=={'world','zone','loginserver','ucs','shared_memory'}
    for n,h in m['binaries'].items():assert sha(STAGE/'native-bin'/n)==h,n
    return m

def image_hashes(image):
    code="from pathlib import Path;import hashlib,json;r=Path('/opt/nightcap');print(json.dumps({p:hashlib.sha256((r/p).read_bytes()).hexdigest() for p in ['bin/loginserver','bin/world','bin/zone','bin/ucs','bin/shared_memory','start.py','configure.py','accounts.py']}))"
    return json.loads(out('docker','run','--rm','--network','none','--entrypoint','python3',image,'-c',code))

def running(image_id,binaries,expected_restarts=0):
    s=state('game');assert s['Image']==image_id and s['RestartCount']==expected_restarts
    assert s['State']['Running'] and not s['State'].get('OOMKilled',False) and s['State']['Health']['Status']=='healthy'
    code="from pathlib import Path;import hashlib,json;rows=[]\nfor p in Path('/proc').iterdir():\n if p.name.isdigit():\n  try:\n   e=p/'exe';n=e.resolve().name\n   if n in {'world','zone','ucs','loginserver'}:rows.append([n,hashlib.sha256(e.read_bytes()).hexdigest()])\n  except (FileNotFoundError,PermissionError):pass\nprint(json.dumps(rows))"
    rows=json.loads(out('docker','compose','exec','-T','game','python3','-c',code))
    assert sum(n=='zone' for n,h in rows)==12
    assert all(sum(n==wanted for n,h in rows)==1 for wanted in ('world','ucs','loginserver'))
    assert all(binaries[n]==h for n,h in rows)
    logs=out('docker','compose','logs','--no-color','--since',s['State']['StartedAt'],'game',stderr=subprocess.DEVNULL)
    patterns={'quest_api':r"Can't locate object method|Undefined subroutine|Perl runtime error",'native':r'Segmentation fault|core dumped|a native process exited','database':r'Unknown column|SQL syntax|does not exist.*nightcap_market'}
    errors={n:len(re.findall(p,logs,re.I)) for n,p in patterns.items()};assert not any(errors.values()),errors
    return {'image_id':image_id,'native_processes':len(rows),'running_hashes':rows,'started_at':s['State']['StartedAt'],'restart_count':s['RestartCount'],'errors':errors}

def verify_baseline(m):
    result=running(m['old_image_id'],{n:m['old_hashes']['bin/'+n] for n in m['binaries']},expected_restarts=m['old_restart_count'])
    assert result['started_at']==m['old_started_at'],'Old server start changed after baseline capture'
    return result

def preflight():
    m=manifest();assert not EVIDENCE.exists()
    assert json.loads(out('docker','compose','config','--format','json'))['services']['game']['image']==m['old_image']
    assert out('docker','image','inspect','--format','{{.Id}}',m['old_image']).strip()==m['old_image_id']
    old=image_hashes(m['old_image_id']);assert old==m['old_hashes']
    verify_baseline(m)
    assert state('gateway')['State']['Running'] and shutil.disk_usage(ROOT).free>8_000_000_000
    call('docker','build','--network','none','-t',m['new_image'],str(STAGE))
    new_id=out('docker','image','inspect','--format','{{.Id}}',m['new_image']).strip()
    new=image_hashes(new_id);assert new=={**old,**{'bin/'+n:h for n,h in m['binaries'].items()}}
    call('docker','run','--rm','--network','none','--entrypoint','python3',new_id,'-c',"import sys;sys.path.insert(0,'/opt/nightcap');import start;start.validate_native()")
    call('docker','run','--rm','--network','none','--entrypoint','/opt/nightcap/bin/loginserver',new_id,'--nightcap-crypto-self-test')
    EVIDENCE.mkdir(mode=0o700);save('preflight.json',{'old':old,'new':new,'new_image_id':new_id,'manifest_sha256':sha(STAGE/'manifest.json'),'runtime':runtime_files()})
    print(json.dumps({'preflight':'passed','new_image_id':new_id}),flush=True)

def stopped(clean_game=False):
    states={s:state(s)['State'] for s in ('game','gateway')}
    assert all(not s['Running'] for s in states.values()),'Game/gateway still running'
    if clean_game:
        assert states['game'].get('ExitCode')==0 and not states['game'].get('OOMKilled',False),'Game shutdown was not clean (exit/OOM); do not activate'

def hold_gateway_closed(gateway_id=None):
    # A failed Compose invocation can have started the gateway before returning.
    # Verify closure and fall back to its already captured immutable container ID.
    try:compose('stop','gateway')
    except BaseException:pass
    try:
        current=state('gateway')
        if not current['State']['Running']:return True
        gateway_id=current['Id']
    except BaseException:pass
    if gateway_id:
        try:
            call('docker','stop','--time','30',gateway_id)
            return not json.loads(out('docker','inspect',gateway_id))[0]['State']['Running']
        except BaseException:pass
    return False

def stable_running(image_id,binaries):
    first=running(image_id,binaries)
    time.sleep(5)
    second=running(image_id,binaries)
    assert first['started_at']==second['started_at'],'Game restarted during health grace'
    return second
def select(image):
    path=ROOT/'.env';lines=path.read_text().splitlines();assert sum(x.startswith('NIGHTCAP_GAME_IMAGE=') for x in lines)==1
    data='\n'.join('NIGHTCAP_GAME_IMAGE='+image if x.startswith('NIGHTCAP_GAME_IMAGE=') else x for x in lines)+'\n'
    tmp=path.with_name('.env.pet-pending-'+str(time.time_ns()));stat=path.stat()
    try:
        with tmp.open('xb') as f:f.write(data.encode());f.flush();os.fsync(f.fileno())
        os.chmod(tmp,0o600);os.chown(tmp,stat.st_uid,stat.st_gid);os.replace(tmp,path)
    finally:
        if tmp.exists():tmp.unlink()

def backup():
    path=EVIDENCE/'peq-before.sql.gz'
    with path.open('xb') as dest:
        dump=subprocess.Popen(['docker','compose','exec','-T','db','mariadb-dump','--defaults-extra-file=/run/secrets/db_backup_config','--single-transaction','--routines','--triggers','--events','--hex-blob','peq'],cwd=ROOT,stdout=subprocess.PIPE)
        try:
            with gzip.GzipFile(fileobj=dest,mode='wb') as zipped:shutil.copyfileobj(dump.stdout,zipped,1024*1024)
        finally:dump.stdout.close()
        assert dump.wait()==0
    size=0
    with gzip.open(path,'rb') as src:
        while chunk:=src.read(1024*1024):size+=len(chunk)
    assert size>100_000_000;save('backup.json',{'sha256':sha(path),'uncompressed_bytes':size})

def restore_rehearsal(before):
    image=state('db')['Image'];assert not out('docker','ps','-aq','--filter','name=^/'+REHEARSAL+'$').strip()
    call('docker','run','-d','--rm','--name',REHEARSAL,'--network','none','--memory','1536m','-e','MARIADB_ALLOW_EMPTY_ROOT_PASSWORD=1',image)
    try:
        for _ in range(60):
            ready=subprocess.run(['docker','exec',REHEARSAL,'mariadb-admin','-uroot','ping'],capture_output=True)
            daemon=subprocess.run(['docker','exec',REHEARSAL,'cat','/proc/1/comm'],capture_output=True,text=True)
            if ready.returncode==0 and daemon.stdout.strip()=='mariadbd':break
            time.sleep(1)
        else:raise RuntimeError('Backup rehearsal database unavailable')
        call('docker','exec',REHEARSAL,'mariadb','-uroot','-e','CREATE DATABASE peq;')
        call('docker','cp',str(EVIDENCE/'peq-before.sql.gz'),REHEARSAL+':/tmp/backup.sql.gz')
        with (EVIDENCE/'restore-private.log').open('xb') as log:
            r=subprocess.run(['docker','exec',REHEARSAL,'bash','-o','pipefail','-c','gzip -dc /tmp/backup.sql.gz | mariadb -uroot peq'],stdout=log,stderr=log,timeout=300)
        assert r.returncode==0,'Backup restore failed; inspect private host log'
        assert fingerprints(True)==before,'Restored preservation differs'
        save('rehearsal.json',{'full_backup_restored':True,'preserved_tables':len(before)})
    finally:call('docker','stop',REHEARSAL)

def check_preservation(before,runtime):
    assert fingerprints()==before,'Player/rule/merchant preservation mismatch'
    assert runtime_files()==runtime,'Runtime quest drift'

def activate():
    m=manifest();p=load('preflight.json');assert sha(STAGE/'manifest.json')==p['manifest_sha256']
    assert runtime_files()==p['runtime'];assert state('game')['Image']==m['old_image_id']
    assert out('docker','image','inspect','--format','{{.Id}}',m['new_image']).strip()==p['new_image_id']
    verify_baseline(m)
    gateway_id=state('gateway')['Id'];before=None;switched=False
    try:
        compose('stop','gateway');compose('stop','-t','90','game');stopped(clean_game=True)
        before=fingerprints();save('preservation-before.json',before)
        epoch=int(sql('SELECT epoch FROM nightcap_market_state;'));save('epoch-before.json',{'epoch':epoch})
        backup();restore_rehearsal(before);check_preservation(before,p['runtime'])
        switched=True;select(m['new_image'])
        compose('up','-d','--wait','--wait-timeout','240','game')
        check_preservation(before,p['runtime'])
        assert int(sql('SELECT epoch FROM nightcap_market_state;'))==epoch+1
        assert sorted(sql('SELECT kind,COUNT(*),SUM(remaining) FROM nightcap_market_offers GROUP BY kind;').splitlines())==sorted(['find\t10\t10','sell\t20\t20','buy\t12\t12'])
        result=stable_running(p['new_image_id'],m['binaries']);result.update(epoch=epoch+1,preserved_tables=len(before),runtime_files=len(p['runtime']),backup_sha256=load('backup.json')['sha256'])
        save('verified-before-open.json',result)
        compose('up','-d','--wait','--wait-timeout','60','gateway');assert state('gateway')['State']['Running']
        running(p['new_image_id'],m['binaries'])
        save('activated.json',result);print(json.dumps(result),flush=True)
    except BaseException:
        try:
            assert hold_gateway_closed(gateway_id),'Gateway closure could not be verified'
            compose('stop','-t','90','game');stopped()
            if switched:select(m['old_image'])
            compose('up','-d','--force-recreate','--wait','--wait-timeout','240','game')
            stable_running(m['old_image_id'],{n:m['old_hashes']['bin/'+n] for n in m['binaries']})
            if before is not None:check_preservation(before,p['runtime'])
            compose('up','-d','--wait','--wait-timeout','60','gateway')
            assert state('gateway')['State']['Running']
            running(m['old_image_id'],{n:m['old_hashes']['bin/'+n] for n in m['binaries']})
            save('rolled-back.json',{'old_image_restored':True,'database_restored':False})
        except BaseException:
            closed=hold_gateway_closed(gateway_id)
            save('rollback-failed.json',{'gateway_held_closed':closed});raise
        raise

def rollback():
    m=manifest();p=load('preflight.json');assert state('game')['Image']==p['new_image_id']
    gateway_id=state('gateway')['Id']
    try:
        assert hold_gateway_closed(gateway_id),'Gateway closure could not be verified'
        compose('stop','-t','90','game');stopped()
        before=fingerprints();runtime=runtime_files()
        select(m['old_image']);compose('up','-d','--force-recreate','--wait','--wait-timeout','240','game')
        stable_running(m['old_image_id'],{n:m['old_hashes']['bin/'+n] for n in m['binaries']});check_preservation(before,runtime)
        compose('up','-d','--wait','--wait-timeout','60','gateway');assert state('gateway')['State']['Running']
        running(m['old_image_id'],{n:m['old_hashes']['bin/'+n] for n in m['binaries']})
        save('rollback-'+str(time.time_ns())+'.json',{'current_progress_preserved':True,'database_restored':False})
    except BaseException:
        closed=hold_gateway_closed(gateway_id)
        save('rollback-failed-'+str(time.time_ns())+'.json',{'gateway_held_closed':closed});raise

if __name__=='__main__':
    os.umask(0o077)
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['preflight','activate','rollback']);args=parser.parse_args()
    {'preflight':preflight,'activate':activate,'rollback':rollback}[args.action]()
