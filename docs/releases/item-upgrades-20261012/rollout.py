"""Owner-authorized zone-only release; retain all data and prior immutable image."""
import argparse,fcntl,hashlib,json,os,sys,time
from pathlib import Path

STAGE=Path('/opt/nightcap/releases/item-upgrades-20261012')
sys.path.insert(0,'/opt/nightcap/releases/zone-hunt-20261009')
import runtime_ops as r
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
    tables=r.sql("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA='peq' AND TABLE_NAME LIKE 'nightcap\\_%' AND TABLE_NAME NOT IN ('nightcap_market_offers','nightcap_market_state','nightcap_item_upgrade_state','nightcap_item_upgrades') ORDER BY TABLE_NAME;").splitlines()
    assert all(n.replace('_','').isalnum() for n in tables)
    result={n:r.sql('CHECKSUM TABLE `'+n+'` EXTENDED;').strip().split('\t')[-1] for n in tables}
    assert all(v.isdigit() for v in result.values())
    return result
def select(image):
    p=ROOT/'.env';raw=p.read_text();lines=raw.splitlines()
    assert sum(x.startswith('NIGHTCAP_GAME_IMAGE=') for x in lines)==1
    data='\n'.join('NIGHTCAP_GAME_IMAGE='+image if x.startswith('NIGHTCAP_GAME_IMAGE=') else x for x in lines)+'\n'
    temp=p.with_name('.env.item-upgrades-'+str(time.time_ns()));st=p.stat()
    with temp.open('x') as f:f.write(data);f.flush();os.fsync(f.fileno())
    os.chmod(temp,st.st_mode & 0o777);os.chown(temp,st.st_uid,st.st_gid);os.replace(temp,p)
def validate_image(image):
    libraries=r.out('docker','run','--rm','--network','none','--entrypoint','ldd',image,'/opt/nightcap/bin/zone')
    assert 'not found' not in libraries,'Missing zone runtime library'
    r.call('docker','run','--rm','--network','none','--entrypoint','python3',image,'-c',"import sys;sys.path.insert(0,'/opt/nightcap');import start;start.validate_native()")
    r.call('docker','run','--rm','--network','none','--entrypoint','/opt/nightcap/bin/loginserver',image,'--nightcap-crypto-self-test')
def preflight():
    m=manifest();assert not r.EVIDENCE.exists()
    old=r.compact('game');assert old['running'] and old['health']=='healthy'
    hashes=r.image_hashes(old['image_id'])
    assert {n:hashes['bin/'+n] for n in m['base_binaries']}==m['base_binaries'],'Deployed baseline differs'
    r.running(old['image_id'],m['base_binaries'],expected_restarts=old['restarts'])
    services={n:r.compact(n) for n in ('game','gateway','db','web','tunnel')}
    assert services['gateway']['running']
    r.closed_ports()
    assert 'quests/ecommons/999820.pl' not in r.runtime()
    assert r.sql("SELECT COUNT(*) FROM items WHERE id=900620; SELECT COUNT(*) FROM npc_types WHERE id=999820; SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='peq' AND TABLE_NAME LIKE 'nightcap_item_upgrade%';").splitlines()==['0','0','0']
    tag='nightcap-game:item-upgrades-base-20261012'
    r.call('docker','tag',old['image_id'],tag)
    assert r.out('docker','image','inspect','--format','{{.Id}}',tag).strip()==old['image_id']
    (STAGE/'Dockerfile').write_text('FROM '+tag+'\nCOPY bin/zone /opt/nightcap/bin/zone\n')
    r.call('docker','build','--network','none','-t','nightcap-game:item-upgrades-20261012',str(STAGE))
    new=r.out('docker','image','inspect','--format','{{.Id}}','nightcap-game:item-upgrades-20261012').strip()
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
              'content':content(),'policies':policies(),'backup':backup}
    save('preflight.json',snapshot)
    print(json.dumps({'status':'preflight_passed','new_image_id':new,'old_image_id':old['image_id'],'backup_verified':True}),flush=True)
def activate():
    m=manifest();p=load('preflight.json')
    assert p['manifest_sha256']==sha(STAGE/'manifest.json')
    assert r.compact('game')==p['services']['game'] and r.compact('gateway')==p['services']['gateway']
    assert r.image_hashes(p['new_image_id'])=={**p['old_hashes'],'bin/zone':m['binaries']['zone']}
    untouched(p);r.closed_ports();assert policies()==p['policies'] and content()==p['content']
    player=None;custom=None;opened=False;preservation_failed=False
    try:
        r.compose('stop','gateway');r.compose('stop','-t','90','game')
        old=r.state('game')['State']
        assert not r.state('gateway')['State']['Running'] and not old['Running'] and old['ExitCode']==0 and not old.get('OOMKilled')
        player=r.player_data();custom=extras();save('stopped-data.json',{'player':player,'custom':custom})
        cache_before=cache_fingerprint(False)
        sql_file('install.sql')
        assert feature_state()=='1\t2026101201\t0', 'Installer did not leave feature disabled'
        verify_content_rows()
        quest=ROOT/'data/server/quests/ecommons/999820.pl'
        assert not quest.exists()
        with quest.open('xb') as output:output.write((STAGE/'quests/ecommons/999820.pl').read_bytes())
        os.chmod(quest,0o644)
        assert sha(quest)==m['files']['quests/ecommons/999820.pl']
        select(p['new_image_id']);r.compose('up','-d','--wait','--wait-timeout','240','game')
        first=r.running(p['new_image_id'],m['binaries']);time.sleep(5)
        result=r.running(p['new_image_id'],m['binaries'])
        assert result['started_at']==first['started_at']
        preservation_failed=not (r.player_data()==player and extras()==custom)
        assert not preservation_failed,'Persisted data drift while gateway closed'
        assert policies()==p['policies'] and content()==p['content'];untouched(p,True)
        cache_after=cache_fingerprint(True)
        assert cache_after['other_items_sha256']==cache_before['other_items_sha256'], 'Unrelated cached item drift'
        sql_file('activate.sql');assert feature_state()=='1\t2026101201\t1'
        preservation_failed=r.sql('SELECT COUNT(*) FROM nightcap_item_upgrades;').strip()!='0'
        assert not preservation_failed,'Unexpected upgrade receipts while gateway closed'
        save('verified-closed.json',{'runtime':result,'cache':cache_after,'feature_state':feature_state()})
        opened=True  # An acknowledgment may be lost after players were admitted.
        r.compose('up','-d','--wait','--wait-timeout','60','gateway')
        assert r.state('gateway')['State']['Running'];r.closed_ports()
        result=r.running(p['new_image_id'],m['binaries']);untouched(p,True)
        save('activated.json',{'runtime':result,'gateway_open':True,'player_tables_preserved':len(player),
             'custom_tables_preserved':len(custom),'database_restored':False,'backup':p['backup'],
             'cache':cache_after,'feature_state':feature_state(),'npc_verified':True})
        print(json.dumps({'status':'activated','zone_sha256':m['binaries']['zone'],'zones':12,'gateway_open':True}),flush=True)
    except BaseException:
        try:
            r.compose('stop','gateway');r.compose('stop','-t','90','game')
            assert not r.state('gateway')['State']['Running'] and not r.state('game')['State']['Running']
            # A SQL commit acknowledgment may be lost. Inspect durable state instead of trusting a local flag.
            if r.sql("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='peq' AND TABLE_NAME='nightcap_item_upgrade_state';").strip()=='1':
                sql_file('rollback.sql')
            quest=ROOT/'data/server/quests/ecommons/999820.pl'
            if quest.exists():
                assert sha(quest)==m['files']['quests/ecommons/999820.pl']
                quest.rename(STAGE/'disabled-999820.pl')
            assert r.image_hashes(p['old_image_id'])==p['old_hashes']
            select(p['old_image_id']);r.compose('up','-d','--wait','--wait-timeout','240','game')
            r.running(p['old_image_id'],m['base_binaries'])
            assert policies()==p['policies'] and content()==p['content'];untouched(p)
            assert not preservation_failed, 'Unexplained saved-data drift; hold gateway closed'
            if not opened and player is not None:
                assert r.player_data()==player and extras()==custom, 'Saved-data drift during recovery'
                if r.sql("SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='peq' AND TABLE_NAME='nightcap_item_upgrades';").strip()=='1':
                    assert r.sql('SELECT COUNT(*) FROM nightcap_item_upgrades;').strip()=='0','Unexpected receipts during recovery'
            # Keep all current character/receipt/world state, including anything saved after gateway reopening.
            r.compose('up','-d','--wait','--wait-timeout','60','gateway')
            save('rolled-back.json',{'old_image_id':p['old_image_id'],'database_restored':False,'gateway_open':True})
        except BaseException:
            r.compose('stop','gateway');save('held-closed.json',{'database_restored':False,'gateway_open':False});raise
        raise

def report():
    m=manifest();p=load('preflight.json');a=load('activated.json')
    result=r.running(p['new_image_id'],m['binaries'])
    assert result['started_at']==a['runtime']['started_at']
    assert r.compact('gateway')['running'] and policies()==p['policies'];untouched(p,True);r.closed_ports()
    assert feature_state()=='1\t2026101201\t1';verify_content_rows();cache_fingerprint(True)
    print(json.dumps({'status':'healthy','runtime':result,'gateway_open':True,'player_tables_preserved':a['player_tables_preserved'],
                     'custom_tables_preserved':a['custom_tables_preserved']}),flush=True)
def sql_file(name):
    import subprocess
    assert name in ('install.sql','activate.sql','rollback.sql')
    result=subprocess.run(['docker','compose','exec','-T','db','mariadb','--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','--skip-column-names','peq'],cwd=ROOT,input=(STAGE/'sql'/name).read_text(),text=True,capture_output=True,timeout=120)
    if result.returncode:raise RuntimeError('Release SQL failed: '+name+'; '+result.stderr[-1500:])

def feature_state():
    return r.sql('SELECT id,revision,enabled FROM nightcap_item_upgrade_state ORDER BY id;').strip()

def untouched(p,installed=False):
    expected=dict(p['runtime'])
    if installed:expected['quests/ecommons/999820.pl']=manifest()['files']['quests/ecommons/999820.pl']
    r.untouched({**p,'runtime':expected})

def content():
    # Hash every original row while excluding only this release's new identities.
    tables={'items':'id<>900620','npc_types':'id<>999820','spawngroup':'id<>999820','spawn2':'id<>999820','spawnentry':'spawngroupID<>999820'}
    result={}
    for table,where in tables.items():
        columns=[line.split('\t')[0] for line in r.sql('SHOW COLUMNS FROM `'+table+'`;').splitlines()]
        assert all(c.replace('_','').isalnum() for c in columns)
        expression=','.join("IFNULL(HEX(CAST(`"+c+"` AS BINARY)),'NULL')" for c in columns)
        rows=r.sql("SELECT SHA2(CONCAT_WS(':',"+expression+"),256) AS h FROM `"+table+"` WHERE "+where+" ORDER BY h;")
        result[table]=hashlib.sha256(rows.encode()).hexdigest()
    for table in ('spells_new','merchantlist'):
        result[table]=r.sql('CHECKSUM TABLE `'+table+'` EXTENDED;').strip()
    return result

def verify_content_rows():
    assert r.sql("SELECT Name,bagtype,bagslots,bagsize,price FROM items WHERE id=900620;").strip()=='Reforging Box\t13\t4\t10\t0'
    assert r.sql("SELECT name,lastname FROM npc_types WHERE id=999820;").strip()=='Artisan_Veyra\tReforging Boxes'
    assert r.sql("SELECT zone,version,x,y,z FROM spawn2 WHERE id=999820 AND spawngroupID=999820;").strip()=='ecommons\t0\t-385.000000\t-1818.000000\t3.750000'
    assert r.sql('SELECT chance FROM spawnentry WHERE spawngroupID=999820 AND npcID=999820;').strip()=='100'

def cache_fingerprint(expect_box):
    import mmap,struct
    ids=[int(n) for n in r.sql('SELECT id FROM items ORDER BY id;').splitlines()]
    assert (900620 in ids)==expect_box
    path=ROOT/'data/server/shared/items'
    digest=hashlib.sha256()
    with path.open('rb') as source,mmap.mmap(source.fileno(),0,access=mmap.ACCESS_READ) as mem:
        payload,count,maximum,current=struct.unpack_from('<IIII',mem,0)
        assert payload+8==len(mem) and current==maximum==len(ids)
        assert len(mem)==20+4*count+1332*maximum
        start=16+4*count
        for item_id in ids:
            assert item_id<count
            index=struct.unpack_from('<I',mem,16+item_id*4)[0];assert index<current
            data=mem[start+index*1332:start+(index+1)*1332]
            assert struct.unpack_from('<I',data,440)[0]==item_id
            if item_id!=900620:digest.update(data)
            else:
                assert b'Reforging Box\x00' in data
                # Native offsets are recorded by the release's typed layout probe.
                layout=manifest()['item_layout']
                assert len(data)==layout['sizeof']
                for field,expected in {'ItemClass':1,'BagType':13,'BagSlots':4,'BagSize':10}.items():
                    assert data[layout[field]]==expected,field
    return {'items_checked':len(ids),'box_verified':expect_box,'other_items_sha256':digest.hexdigest()}

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
