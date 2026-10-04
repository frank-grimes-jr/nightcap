"""Two-binary blessing reconnect repair. No database writes, schema changes or quest replacement."""
import argparse,fcntl,hashlib,json,os,re,subprocess,time
from pathlib import Path

ROOT=Path('/opt/nightcap/deploy/production')
STAGE=Path('/opt/nightcap/releases/blessing-relogin-server-20261003')
EVIDENCE=STAGE/'evidence'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def out(*args):return subprocess.check_output(args,cwd=ROOT,text=True)
def call(*args):subprocess.run(args,cwd=ROOT,check=True)
def compose(*args):call('docker','compose',*args)
def load(n):return json.loads((EVIDENCE/n).read_text())
def save(n,v):
    with (EVIDENCE/n).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def state(service):
    cid=out('docker','compose','ps','-aq',service).strip();assert cid
    return json.loads(out('docker','inspect',cid))[0]
def compact(service):
    i=state(service);s=i['State']
    return {'id':i['Id'],'image_id':i['Image'],'started_at':s['StartedAt'],'restarts':i['RestartCount'],'running':s['Running'],'health':s.get('Health',{}).get('Status'),'oom_killed':s.get('OOMKilled',False)}
def manifest():
    m=json.loads((STAGE/'manifest.json').read_text())
    for n,h in m['files'].items():
        p=STAGE/n;assert p.resolve().is_relative_to(STAGE) and not p.is_symlink() and sha(p)==h,n
    assert set(m['binaries'])=={'world','zone','ucs','loginserver','shared_memory'}
    return m
def image_hashes(image):
    code="from pathlib import Path;import hashlib,json;r=Path('/opt/nightcap');print(json.dumps({n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in ['bin/world','bin/zone','bin/ucs','bin/loginserver','bin/shared_memory','start.py','configure.py','accounts.py']}))"
    return json.loads(out('docker','run','--rm','--network','none','--entrypoint','python3',image,'-c',code))
def runtime():
    base=ROOT/'data/server'
    return {p.relative_to(base).as_posix():sha(p) for d in ('quests','plugins','lua_modules') for p in (base/d).rglob('*') if p.is_file() and p.suffix in ('.pl','.lua','.json')}
def public():
    return {n:sha(ROOT/'data/public'/n) for n in ('channel.json','launcher-channel.json','nightcap-friends.zip','guide.html')}
def sql(q):
    p=subprocess.run(['docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','--skip-column-names','peq'],cwd=ROOT,input=q,text=True,capture_output=True,timeout=180)
    if p.returncode:raise RuntimeError('Read-only database fingerprint failed; no rows exported')
    return p.stdout
def player_data():
    tables=sql("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA='peq' AND (TABLE_NAME LIKE 'character\\_%' OR TABLE_NAME IN ('account','inventory','quest_globals','rule_values','zone_state_spawns')) ORDER BY TABLE_NAME;").splitlines()
    result={}
    for table in tables:
        assert re.fullmatch('[a-z_]+',table)
        rows=sql('SELECT * FROM `'+table+'`;').splitlines()
        result[table]={'rows':len(rows),'sha256':hashlib.sha256('\n'.join(sorted(rows)).encode()).hexdigest()}
    assert {'inventory','character_advloot_claims','character_advloot_filters','character_advloot_settings','zone_state_spawns'}<=set(result)
    return result
def closed_ports():
    for service in ('game','gateway'):
        i=state(service);assert not i['HostConfig'].get('PortBindings') and i['HostConfig']['NetworkMode']!='host'
def running(image,binaries):
    i=state('game');assert i['Image']==image and i['RestartCount']==0 and i['State']['Running'] and not i['State'].get('OOMKilled') and i['State']['Health']['Status']=='healthy'
    code="from pathlib import Path;import hashlib,json;r=[]\nfor p in Path('/proc').iterdir():\n if p.name.isdigit():\n  try:\n   e=p/'exe';n=e.resolve().name\n   if n in {'world','zone','ucs','loginserver'}:r.append([n,hashlib.sha256(e.read_bytes()).hexdigest()])\n  except (FileNotFoundError,PermissionError):pass\nprint(json.dumps(r))"
    rows=json.loads(out('docker','exec',i['Id'],'python3','-c',code))
    assert sum(n=='zone' for n,h in rows)==12
    assert all(sum(n==k for n,h in rows)==1 for k in ('world','ucs','loginserver'))
    assert all(binaries[n]==h for n,h in rows)
    logs=out('docker','compose','logs','--no-color','--since',i['State']['StartedAt'],'game')
    patterns={'native':r'Segmentation fault|core dumped|a native process exited','quest':r"Can't locate object method|Undefined subroutine|Perl runtime error",'database':r'Unknown column|SQL syntax'}
    errors={n:len(re.findall(p,logs,re.I)) for n,p in patterns.items()};assert not any(errors.values()),errors
    return {'image_id':image,'started_at':i['State']['StartedAt'],'restart_count':0,'processes':rows,'errors':errors}
def untouched(p):
    for service in ('db','web','tunnel'):assert compact(service)==p['services'][service],service
    assert runtime()==p['runtime'],'Quest/plugin drift'
    current=public()
    for n,h in p['public'].items():assert current[n]==h,n
def select(image):
    p=ROOT/'.env';raw=p.read_text();lines=raw.splitlines();assert sum(s.startswith('NIGHTCAP_GAME_IMAGE=') for s in lines)==1
    data='\n'.join('NIGHTCAP_GAME_IMAGE='+image if s.startswith('NIGHTCAP_GAME_IMAGE=') else s for s in lines)+'\n'
    tmp=p.with_name('.env.blessing-relogin-'+str(time.time_ns()));st=p.stat()
    with tmp.open('x') as f:f.write(data);f.flush();os.fsync(f.fileno())
    os.chmod(tmp,0o600);os.chown(tmp,st.st_uid,st.st_gid);os.replace(tmp,p)
def preflight():
    m=manifest();old=m['baseline'];assert not EVIDENCE.exists();closed_ports()
    assert compact('game')==old['services']['game']
    for service in ('gateway','db','web','tunnel'):assert compact(service)==old['services'][service]
    assert public()=={n:v['sha256'] for n,v in old['public'].items()}
    assert image_hashes(m['old_image_id'])==m['old_hashes']
    running(m['old_image_id'],{n:m['old_hashes']['bin/'+n] for n in m['binaries']})
    assert out('docker','image','inspect','--format','{{.Id}}',m['old_image']).strip()==m['old_image_id'],'Base image tag drift'
    call('docker','build','--network','none','-t',m['new_image'],str(STAGE))
    assert out('docker','image','inspect','--format','{{.Id}}',m['old_image']).strip()==m['old_image_id'],'Base image tag drift during build'
    image=out('docker','image','inspect','--format','{{.Id}}',m['new_image']).strip()
    layers=lambda i:json.loads(out('docker','image','inspect',i))[0]['RootFS']['Layers']
    base_layers=layers(m['old_image_id']);new_layers=layers(image)
    assert new_layers[:len(base_layers)]==base_layers and len(new_layers)==len(base_layers)+1,'Unexpected image ancestry'
    expected={**m['old_hashes'],**{'bin/'+n:h for n,h in m['binaries'].items()}}
    assert image_hashes(image)==expected
    call('docker','run','--rm','--network','none','--entrypoint','python3',image,'-c',"import sys;sys.path.insert(0,'/opt/nightcap');import start;start.validate_native()")
    call('docker','run','--rm','--network','none','--entrypoint','/opt/nightcap/bin/loginserver',image,'--nightcap-crypto-self-test')
    EVIDENCE.mkdir(mode=0o700)
    save('preflight.json',{'manifest_sha256':sha(STAGE/'manifest.json'),'new_image_id':image,'runtime':runtime(),'services':old['services'],'public':public(),'old_receipt_aware_image_verified':True})
    print(json.dumps({'status':'preflight_passed','image_id':image}),flush=True)
def activate():
    m=manifest();p=load('preflight.json');assert p['manifest_sha256']==sha(STAGE/'manifest.json')
    assert compact('game')==p['services']['game'] and compact('gateway')==p['services']['gateway']
    # This server-only repair preserves the currently published client channel.
    assert p['public']['channel.json']==m['client_channel_sha256'];untouched(p);closed_ports()
    assert out('docker','image','inspect','--format','{{.Id}}',m['new_image']).strip()==p['new_image_id']
    before=None
    try:
        compose('stop','gateway');compose('stop','-t','90','game')
        assert not state('gateway')['State']['Running']
        old=state('game')['State'];assert not old['Running'] and old['ExitCode']==0 and not old.get('OOMKilled')
        before=player_data();save('player-before.json',before)
        select(m['new_image']);compose('up','-d','--wait','--wait-timeout','240','game')
        first=running(p['new_image_id'],m['binaries']);time.sleep(5);result=running(p['new_image_id'],m['binaries']);assert first['started_at']==result['started_at']
        assert player_data()==before,'Player/receipt/settings data changed while gateway closed';untouched(p)
        save('verified-closed.json',{**result,'player_tables_preserved':len(before),'quest_files_preserved':len(p['runtime'])})
        compose('up','-d','--wait','--wait-timeout','60','gateway')
        assert state('gateway')['State']['Running'];running(p['new_image_id'],m['binaries']);untouched(p)
        save('activated.json',{**result,'client_release':m['client_release'],'client_channel_sha256':m['client_channel_sha256'],'player_tables_preserved':len(before),'quest_files_preserved':len(p['runtime']),'database_restored':False,'gateway_open':True})
        print(json.dumps(load('activated.json')),flush=True)
    except BaseException:
        # Roll back only the immediately previous receipt-aware image. Keep all
        # current receipts, inventory and saved state; never restore the database.
        try:
            compose('stop','gateway');compose('stop','-t','90','game')
            assert not state('gateway')['State']['Running'] and not state('game')['State']['Running']
            assert image_hashes(m['old_image_id'])==m['old_hashes']
            select(m['old_image_id']);compose('up','-d','--wait','--wait-timeout','240','game')
            running(m['old_image_id'],{n:m['old_hashes']['bin/'+n] for n in m['binaries']})
            if before is not None:assert player_data()==before
            untouched(p);compose('up','-d','--wait','--wait-timeout','60','gateway')
            save('rolled-back.json',{'receipt_aware_image':m['old_image_id'],'database_restored':False,'gateway_open':state('gateway')['State']['Running']})
        except BaseException:
            compose('stop','gateway');save('held-closed.json',{'gateway_running':state('gateway')['State']['Running'],'database_restored':False});raise
        raise
def report():
    m=manifest();p=load('preflight.json');result=running(p['new_image_id'],m['binaries'])
    assert state('gateway')['State']['Running'];p['public']['channel.json']=m['client_channel_sha256'];untouched(p)
    print(json.dumps({'deployment':load('activated.json'),'current':result,'services':{s:compact(s) for s in ('game','gateway','db','web','tunnel')}}))
if __name__=='__main__':
    os.umask(0o077);p=argparse.ArgumentParser();p.add_argument('action',choices=['preflight','activate','report']);a=p.parse_args()
    with (ROOT/'.deployment.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        {'preflight':preflight,'activate':activate,'report':report}[a.action]()
