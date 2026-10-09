"""Passive AA rollout: five matched binaries, one additive rule; preserve data/client/quests."""
import argparse,fcntl,gzip,hashlib,json,mmap,os,re,shutil,struct,subprocess,time
from pathlib import Path

ROOT=Path('/opt/nightcap/deploy/production')
STAGE=Path('/opt/nightcap/releases/passive-aa-20261004')
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
        rows=sql('SELECT * FROM `'+table+'`'+(" WHERE rule_name <> 'AA:PassiveExpPercent'" if table=='rule_values' else '')+';').splitlines()
        result[table]={'rows':len(rows),'sha256':hashlib.sha256('\n'.join(sorted(rows)).encode()).hexdigest()}
    assert {'inventory','character_advloot_claims','character_advloot_filters','character_advloot_settings','zone_state_spawns'}<=set(result)
    return result
def closed_ports():
    for service in ('game','gateway'):
        i=state(service);assert not i['HostConfig'].get('PortBindings') and i['HostConfig']['NetworkMode']!='host'
def running(image,binaries,expected_restarts=0):
    i=state('game');assert i['Image']==image and i['RestartCount']==expected_restarts and i['State']['Running'] and not i['State'].get('OOMKilled') and i['State']['Health']['Status']=='healthy'
    code="from pathlib import Path;import hashlib,json;r=[]\nfor p in Path('/proc').iterdir():\n if p.name.isdigit():\n  try:\n   e=p/'exe';n=e.resolve().name\n   if n in {'world','zone','ucs','loginserver'}:r.append([n,hashlib.sha256(e.read_bytes()).hexdigest()])\n  except (FileNotFoundError,PermissionError):pass\nprint(json.dumps(r))"
    rows=json.loads(out('docker','exec',i['Id'],'python3','-c',code))
    assert sum(n=='zone' for n,h in rows)==12
    assert all(sum(n==k for n,h in rows)==1 for k in ('world','ucs','loginserver'))
    assert all(binaries[n]==h for n,h in rows)
    logs=out('docker','compose','logs','--no-color','--since',i['State']['StartedAt'],'game')
    patterns={'native':r'Segmentation fault|core dumped|a native process exited','quest':r"Can't locate object method|Undefined subroutine|Perl runtime error",'database':r'Unknown column|SQL syntax'}
    errors={n:len(re.findall(p,logs,re.I)) for n,p in patterns.items()};assert not any(errors.values()),errors
    return {'image_id':image,'started_at':i['State']['StartedAt'],'restart_count':i['RestartCount'],'processes':rows,'errors':errors}
def untouched(p):
    for service in ('db','web','tunnel'):assert compact(service)==p['services'][service],service
    assert runtime()==p['runtime'],'Quest/plugin drift'
    current=public()
    for n,h in p['public'].items():assert current[n]==h,n
def select(image):
    p=ROOT/'.env';raw=p.read_text();lines=raw.splitlines();assert sum(s.startswith('NIGHTCAP_GAME_IMAGE=') for s in lines)==1
    data='\n'.join('NIGHTCAP_GAME_IMAGE='+image if s.startswith('NIGHTCAP_GAME_IMAGE=') else s for s in lines)+'\n'
    tmp=p.with_name('.env.passive-aa-'+str(time.time_ns()));st=p.stat()
    with tmp.open('x') as f:f.write(data);f.flush();os.fsync(f.fileno())
    os.chmod(tmp,0o600);os.chown(tmp,st.st_uid,st.st_gid);os.replace(tmp,p)
def preflight():
    m=manifest();old=m['baseline'];assert not EVIDENCE.exists();closed_ports()
    assert policy_rows()==[], 'Unexpected pre-existing Passive AA rule; stop for rebaseline'
    assert sql("SELECT rule_value FROM rule_values WHERE ruleset_id=1 AND rule_name='Character:AAExpMinLevel';").strip()=='1', 'AA minimum level drift'
    assert sql("SELECT ruleset_id FROM rule_sets WHERE name=COALESCE((SELECT value FROM variables WHERE varname='RuleSet'),'default');").strip()=='1', 'Active ruleset drift'
    assert compact('game')==old['services']['game']
    for service in ('gateway','db','web','tunnel'):assert compact(service)==old['services'][service]
    assert public()=={n:v['sha256'] for n,v in old['public'].items()}
    assert image_hashes(m['old_image_id'])==m['old_hashes']
    # An explicitly captured prior restart is baseline history, not a new-release pass.
    running(m['old_image_id'],{n:m['old_hashes']['bin/'+n] for n in m['binaries']},expected_restarts=old['services']['game']['restarts'])
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
    backup=database_backup()
    save('preflight.json',{'manifest_sha256':sha(STAGE/'manifest.json'),'new_image_id':image,'runtime':runtime(),'services':old['services'],'public':public(),'old_receipt_aware_image_verified':True,'backup':backup})
    print(json.dumps({'status':'preflight_passed','image_id':image}),flush=True)
def activate():
    m=manifest();p=load('preflight.json');assert p['manifest_sha256']==sha(STAGE/'manifest.json')
    assert compact('game')==p['services']['game'] and compact('gateway')==p['services']['gateway']
    # This server-only repair preserves the currently published client channel.
    assert p['public']['channel.json']==m['client_channel_sha256'];untouched(p);closed_ports()
    assert out('docker','image','inspect','--format','{{.Id}}',m['new_image']).strip()==p['new_image_id']
    assert policy_rows()==[], 'Passive AA rule changed since preflight'
    before=None;content=None;rule_inserted=False
    try:
        compose('stop','gateway');compose('stop','-t','90','game')
        assert not state('gateway')['State']['Running']
        old=state('game')['State'];assert not old['Running'] and old['ExitCode']==0 and not old.get('OOMKilled')
        before=player_data();save('player-before.json',before)
        content=content_data();save('content-before.json',content)
        sql("INSERT INTO rule_values(ruleset_id,rule_name,rule_value) VALUES(1,'AA:PassiveExpPercent','1');")
        rule_inserted=True
        select(m['new_image']);compose('up','-d','--wait','--wait-timeout','240','game')
        cache=verify_cache();save('hosted-cache.json',cache)
        first=running(p['new_image_id'],m['binaries']);time.sleep(5);result=running(p['new_image_id'],m['binaries']);assert first['started_at']==result['started_at']
        assert player_data()==before,'Player/receipt/settings data changed while gateway closed'
        assert content_data()==content,'Content data drift';assert policy_rows()==['1\t1'];untouched(p)
        save('verified-closed.json',{**result,'player_tables_preserved':len(before),'quest_files_preserved':len(p['runtime'])})
        compose('up','-d','--wait','--wait-timeout','60','gateway')
        assert state('gateway')['State']['Running'];closed_ports();running(p['new_image_id'],m['binaries']);untouched(p)
        save('activated.json',{**result,'client_release':m['client_release'],'client_channel_sha256':m['client_channel_sha256'],'player_tables_preserved':len(before),'quest_files_preserved':len(p['runtime']),'database_restored':False,'gateway_open':True,'cache':cache,'content_preserved':content,'backup':p['backup']})
        print(json.dumps(load('activated.json')),flush=True)
    except BaseException:
        # Roll back only the immediately previous receipt-aware image. Keep all
        # current receipts, inventory and saved state; never restore the database.
        try:
            compose('stop','gateway');compose('stop','-t','90','game')
            assert not state('gateway')['State']['Running'] and not state('game')['State']['Running']
            assert image_hashes(m['old_image_id'])==m['old_hashes']
            if rule_inserted:
                assert policy_rows()==['1\t1'], 'Owned rule changed; preserve it for investigation'
                sql("DELETE FROM rule_values WHERE ruleset_id=1 AND rule_name='AA:PassiveExpPercent' AND rule_value='1';")
            select(m['old_image_id']);compose('up','-d','--wait','--wait-timeout','240','game')
            running(m['old_image_id'],{n:m['old_hashes']['bin/'+n] for n in m['binaries']})
            if before is not None:assert player_data()==before
            if content is not None:assert content_data()==content
            assert policy_rows()==[]
            assert old_cache_valid(), 'Old-format cache was not restored'
            untouched(p);compose('up','-d','--wait','--wait-timeout','60','gateway');closed_ports()
            save('rolled-back.json',{'receipt_aware_image':m['old_image_id'],'database_restored':False,'gateway_open':state('gateway')['State']['Running']})
        except BaseException:
            compose('stop','gateway');save('held-closed.json',{'gateway_running':state('gateway')['State']['Running'],'database_restored':False});raise
        raise
def report():
    m=manifest();p=load('preflight.json');result=running(p['new_image_id'],m['binaries'])
    assert state('gateway')['State']['Running'];closed_ports();p['public']['channel.json']=m['client_channel_sha256'];untouched(p)
    assert policy_rows()==['1\t1'];cache=verify_cache()
    print(json.dumps({'cache':cache,'deployment':load('activated.json'),'current':result,'services':{s:compact(s) for s in ('game','gateway','db','web','tunnel')}}))

def policy_rows():
    return sql("SELECT ruleset_id,rule_value FROM rule_values WHERE rule_name='AA:PassiveExpPercent' ORDER BY ruleset_id;").splitlines()

def content_data():
    rows=sql('CHECKSUM TABLE items EXTENDED; CHECKSUM TABLE spells_new EXTENDED; CHECKSUM TABLE npc_types EXTENDED; CHECKSUM TABLE spawn2 EXTENDED; CHECKSUM TABLE merchantlist EXTENDED;').splitlines()
    result=dict(row.split('\t') for row in rows)
    assert len(result)==5 and all(v.isdigit() for v in result.values()), 'Missing content checksum'
    return result

def database_backup():
    directory=STAGE/'private-backup';directory.mkdir(mode=0o700)
    path=directory/'peq-before.sql.gz'
    cmd=['docker','compose','exec','-T','db','mariadb-dump','--defaults-extra-file=/run/secrets/db_backup_config','--single-transaction','--routines','--events','--hex-blob','peq']
    with (directory/'dump.log').open('wb') as log:
        process=subprocess.Popen(cmd,cwd=ROOT,stdout=subprocess.PIPE,stderr=log)
        with gzip.open(path,'xb',compresslevel=1) as dest:shutil.copyfileobj(process.stdout,dest)
        process.stdout.close();assert process.wait(timeout=180)==0, 'Database backup failed; see private log'
    size=0;tail=b''
    with gzip.open(path,'rb') as source:
        while chunk:=source.read(1024*1024):size+=len(chunk);tail=(tail+chunk)[-4096:]
    assert size>1000000 and b'-- Dump completed on' in tail, 'Truncated database backup'
    return {'path':str(path),'sha256':sha(path),'compressed_bytes':path.stat().st_size,'uncompressed_bytes':size,'gzip_integrity':'passed'}

def cache_header():
    path=ROOT/'data/server/shared/items'
    with path.open('rb') as source:return struct.unpack('<IIII',source.read(16)),path.stat().st_size

def old_cache_valid():
    # Previous free-trade release has the same item ABI and policy.
    return bool(verify_cache())

def verify_cache():
    assert sql("SELECT ruleset_id,rule_value FROM rule_values WHERE rule_name='Items:FreeTrade' ORDER BY ruleset_id;").splitlines()==['1\ttrue'], 'Existing free-trade rule changed'
    rows=sql('SELECT id,nodrop,notransfer,attuneable,fvnodrop,price FROM items ORDER BY id;').splitlines()
    path=ROOT/'data/server/shared/items'
    with path.open('rb') as source, mmap.mmap(source.fileno(),0,access=mmap.ACCESS_READ) as mem:
        payload,count,maximum,current=struct.unpack_from('<IIII',mem,0)
        # MemoryMappedFile adds sizeof({uint32 size; byte data[1];}) == 8,
        # but data starts at offset 4; the allocation has four trailing bytes.
        assert payload+8==len(mem) and current==maximum==len(rows)
        assert len(mem)==20+4*count+1332*maximum, 'Unexpected cache layout'
        start=16+4*count;fixed_count=0
        offsets={'ID':440,'FreeTrade':0,'FixedSellPrice':4,'NoDrop':449,'NoTransfer':800,'Attuneable':796,'FVNoDrop':472,'Price':456}
        for row in rows:
            item_id,nodrop,no_transfer,attune,fv,price=map(int,row.split('\t'))
            assert item_id<count
            index=struct.unpack_from('<I',mem,16+item_id*4)[0];assert index<current
            base=start+index*1332
            def read(n,f):return struct.unpack_from(f,mem,base+offsets[n])[0]
            fixed=1000 if nodrop==0 else 0
            assert read('ID','<I')==item_id
            assert read('FreeTrade','<B')==1 and read('FixedSellPrice','<I')==fixed,item_id
            assert read('NoDrop','<B')==255 and read('NoTransfer','<B')==0,item_id
            assert read('Attuneable','<B')==0 and read('FVNoDrop','<B')==0,item_id
            assert read('Price','<I')==max(price,fixed),item_id
            fixed_count+=bool(fixed)
        return {'items_checked':current,'fixed_payout_items':fixed_count,'all_items_tradable':True,'fixed_payout_copper':1000,'item_struct_bytes':1332,'cache_sha256':hashlib.sha256(mem).hexdigest(),'catalog_flags_sha256':hashlib.sha256('\n'.join(rows).encode()).hexdigest()}

if __name__=='__main__':
    os.umask(0o077);p=argparse.ArgumentParser();p.add_argument('action',choices=['preflight','activate','report']);a=p.parse_args()
    with (ROOT/'.deployment.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        {'preflight':preflight,'activate':activate,'report':report}[a.action]()
