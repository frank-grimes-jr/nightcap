"""Finish this diagnosed release without replaying SQL or restoring player data."""
import argparse,copy,datetime,importlib.util,json,os,shutil,time
from pathlib import Path
S=Path('/opt/nightcap/releases/aa-pacing-million-20261021')
F=S/'finish-evidence'

def validate(before,now,diagnosis):
    old=copy.deepcopy(before);new=copy.deepcopy(now)
    old_cache=old['player'].pop('zone_state_spawns')
    new_cache=new['player'].pop('zone_state_spawns')
    assert old==new, 'Unexplained player/custom drift'
    assert old_cache==diagnosis['original']==diagnosis['scratch_restore']
    assert diagnosis['exact_restore_matches'] and diagnosis['rule']=='7'
    assert old_cache['rows']==6551
    assert new_cache=={'rows':6066,'sha256':'6c1b6ef1a78d69ec4f9d963165fcbc53100515d86d610249dee315d9ca5fe5d4'}
    assert diagnosis['surviving_field_differences']==diagnosis['added_rows']==diagnosis['removed_nonexpired']==0
    assert diagnosis['removed_groups']=='38\t0\t0\t0\t357\t2026-10-13 01:28:39\t2026-10-13 01:28:39\n75\t0\t0\t0\t128\t2026-10-13 01:28:39\t2026-10-13 01:28:39\n'

def finish(op):
    r=op.r
    assert not F.exists() and not r.state('game')['State']['Running'] and not r.state('gateway')['State']['Running']
    assert r.state('game')['State']['ExitCode']==0 and not r.state('game')['State'].get('OOMKilled')
    original=S/'evidence/activation'
    assert not (original/'opening.json').exists()
    assert op.load(original/'content-committed.json')=={'target':'after','aa_xp_per_point':'1000000'}
    p=op.load(S/'evidence/preflight.json')
    assert p['manifest_sha256']==op.sha(S/'manifest.json')
    old=op.load(original/'stopped-state.json');now=op.saved_state()
    diagnosis=op.load(original/'cache-diagnosis.json');validate(old,now,diagnosis)
    # Reauthenticate the complete current table against the exact restored backup.
    scratch='nightcap_aa_state_hold_20261021.zone_state_spawns'
    rows=op.sql('SELECT * FROM '+scratch+';').splitlines()
    import hashlib
    assert {'rows':len(rows),'sha256':hashlib.sha256('\n'.join(sorted(rows)).encode()).hexdigest()}==diagnosis['original']
    fields=[v.split('\t') for v in op.sql('SHOW COLUMNS FROM zone_state_spawns;').splitlines()]
    bt=chr(96);pred=[]
    for name,kind,*_ in fields:
        assert name.replace('_','').isalnum()
        a='o.'+bt+name+bt;b='n.'+bt+name+bt
        # Dumps preserve serialized floats, not necessarily their binary storage.
        if kind.startswith(('float','double')):
            a='BINARY CAST('+a+' AS CHAR)';b='BINARY CAST('+b+' AS CHAR)'
        elif any(v in kind for v in ('char','text','blob','binary','enum','set')):
            a='BINARY '+a;b='BINARY '+b
        pred.append('('+a+'<=>'+b+')')
    same=' AND '.join(pred)
    assert op.sql('SELECT COUNT(*) FROM '+scratch+' o JOIN peq.zone_state_spawns n ON n.id=o.id WHERE NOT('+same+');').strip()=='0'
    assert op.sql('SELECT COUNT(*) FROM peq.zone_state_spawns n LEFT JOIN '+scratch+' o ON o.id=n.id WHERE o.id IS NULL;').strip()=='0'
    assert op.sql('SELECT COUNT(*) FROM '+scratch+' o LEFT JOIN peq.zone_state_spawns n ON o.id=n.id WHERE n.id IS NULL AND o.zone_id IN (38,75) AND o.instance_id=0 AND o.is_zone=0 AND o.is_corpse=0 AND o.created_at='+chr(39)+'2026-10-13 01:28:39'+chr(39)+';').strip()=='485'
    assert op.sql("SELECT rule_value FROM rule_values WHERE ruleset_id=1 AND rule_name='Zone:StateSaveClearDays';").strip()=='7'
    first_rotation=op.verify_market(op.load(original/'market-before.json'),diagnosis['first_started_at'])
    op.untouched(p,'after')
    assert shutil.disk_usage(op.ROOT).free>=768*1024**2
    F.mkdir(mode=0o700);folder=F/'activation';folder.mkdir(mode=0o700)
    op.EVIDENCE=F;r.EVIDENCE=F;r.STAGE=folder
    op.save(F/'preflight.json',p);op.save(folder/'stopped-state.json',now)
    market=op.market();op.save(folder/'market-before.json',market)
    op.save(folder/'cache-expiry.json',{'expired':485,'zones':[38,75],'corpse_rows':0,'instance':0,'survivors_exact':True,'other_player_custom_state_preserved':True,'first_market_rotation':first_rotation})
    try:
        op.save(folder/'backup.json',r.database_backup())
        assert shutil.disk_usage(op.ROOT).free>=512*1024**2
        assert op.saved_state()==now;op.untouched(p,'after')
        assert r.image_hashes(p['new_image_id'])=={**op.manifest()['base_hashes'],'bin/zone':op.binaries()['zone']}
        r.select(p['new_image_id']);r.compose('up','-d','--wait','--wait-timeout','240','game')
        first=r.running(p['new_image_id'],op.binaries());op.health();time.sleep(8)
        current=r.running(p['new_image_id'],op.binaries());assert current['started_at']==first['started_at']
        rotation=op.verify_market(market,current['started_at'])
        assert op.saved_state()==now;op.untouched(p,'after');op.health();r.closed_ports()
        closed={'runtime':current,'game':r.compact('game'),'market':rotation,'player_tables_preserved':len(now['player']),'custom_tables_preserved':len(now['custom']),'cache_expiry_authenticated':485}
        op.save(folder/'verified-closed.json',closed)
        print('Verified cache expiry and restarted runtime with access closed.',flush=True)
    except BaseException:
        op.hold(folder);raise

def main():
    import fcntl
    assert __debug__;os.umask(0o077)
    import hashlib
    pins={'rollout.py':'9b309dec411b4809e969c920d88f060c2334bfca2ecf5c30fc6292dbbf7039e1','manifest.json':'2f5d69124568702334624f1c35d16794dc1432862be61c05cd2eaa115ddf3b38'}
    assert all(hashlib.sha256((S/n).read_bytes()).hexdigest()==v for n,v in pins.items())
    sp=importlib.util.spec_from_file_location('release',S/'rollout.py')
    op=importlib.util.module_from_spec(sp);sp.loader.exec_module(op);op.initialize()
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['finish','open']);action=parser.parse_args().action
    with (op.ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (op.ROOT/'private/gm-maintenance.json').exists() and op.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1'
        if action=='finish':finish(op)
        else:
            op.EVIDENCE=F;op.r.EVIDENCE=F;op.r.STAGE=F/'activation';op.open_access()
if __name__=='__main__':main()
