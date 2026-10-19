"""Resume only the authenticated three compiled rule-note normalizations.

No production SQL is written and no migration is replayed. Original hold and
preflight receipts remain immutable. The sole expected-content change is proven
on the retained public-content clone before restarting the existing new image.
"""
import argparse
import fcntl
import hashlib
import json
import os
import time
import sys
from pathlib import Path

STAGE=Path('/opt/nightcap/releases/thj-parity-20261018')
sys.path.insert(0,str(STAGE))
import rollout as op
REPAIR=STAGE/'rule-notes-recovery'
NOTES={
 'Combat:NightcapHeroicMeleeScaling':(
  'Reviewed WPM heroic-strength weapon-hit curve; requires paired world and zone.',
  'Enable Nightcap diminishing heroic STR percentage scaling for player weapon hits; pair with reviewed WPM content'),
 'Spells:NightcapHeroicSpellScaling':(
  'Client direct values gain 0.1 percent per heroic INT/WIS; periodic ticks excluded',
  'Player heroic INT/WIS add 0.1 percent per point to final direct damage/healing; excludes DoTs and HoTs'),
 'Spells:NightcapTHJDamageScaling':(
  'THJ historical additive direct SD and half-SD ticks; critical ordering is Nightcap calibration',
  'Player/permanent-pet item SD adds to direct damage; half SD per DoT tick before native critical ratio. Healing retains its separate legacy policy')}
RULES='SELECT ruleset_id,rule_name,rule_value,notes FROM rule_values ORDER BY ruleset_id,rule_name;'


def parse_rules(text):
    rows={}
    for line in text.splitlines():
        parts=line.split('\t',3);assert len(parts)==4
        key=(parts[0],parts[1]);assert key not in rows
        rows[key]=parts[2:]
    return rows


def exact_normalization(before,after):
    old=parse_rules(before);new=parse_rules(after)
    expected=dict(old)
    for name,(prior,compiled) in NOTES.items():
        assert old[('1',name)]==['true',prior]
        expected[('1',name)]=['true',compiled]
    assert new==expected,'Change extends beyond the three exact compiled descriptions'


def holds():
    return {p.name:op.sha(p) for p in (STAGE/'evidence').glob('held-*.json')}


def closed():
    assert not op.r.state('gateway')['State']['Running']
    state=op.r.state('game')['State']
    assert not state['Running'] and state['ExitCode']==0 and not state.get('OOMKilled')


def patch_manifest():
    m=op.load(REPAIR/'manifest.json')
    for name,digest in m.items():
        p=REPAIR/name;assert p.resolve().is_relative_to(REPAIR) and not p.is_symlink() and op.sha(p)==digest
    return m


def prepare():
    m=patch_manifest();p=op.load(STAGE/'evidence/preflight.json')
    assert op.sha(STAGE/'manifest.json')==p['manifest_sha256']
    assert not (REPAIR/'expected.json').exists();closed()
    assert len(holds())==1 and op.saved_state()==op.load(STAGE/'evidence/stopped-state.json')
    assert op.r.state('game')['Image']==p['new_image_id']
    first_market=op.b.verify_market(op.load(STAGE/'evidence/market-before.json'),op.r.state('game')['State']['StartedAt'])
    for component in op.manifest()['components']:
        name=Path(component).stem
        assert op.load(STAGE/'evidence'/(name+'-committed.json'))=={'status':'success'}
        assert op.load(STAGE/'evidence'/(name+'-attempted.json'))['sha256']==op.manifest()['files'][component]
    assert op.checksums(op.TABLES,op.CLONE)==p['after']
    old=op.sql(RULES,op.CLONE);new=op.sql(RULES)
    exact_normalization(old,new)
    before=op.checksums(op.TABLES)
    assert {k:v for k,v in before.items() if k!='rule_values'}=={k:v for k,v in p['after'].items() if k!='rule_values'}
    hexstr=lambda s:"CONVERT(X'"+s.encode().hex()+"' USING utf8mb4)"
    for name,(prior,compiled) in NOTES.items():
        assert op.sql('UPDATE rule_values SET notes='+hexstr(compiled)+' WHERE ruleset_id=1 AND rule_name='+hexstr(name)+" AND rule_value='true' AND BINARY notes="+hexstr(prior)+'; SELECT ROW_COUNT();',op.CLONE).strip()=='1'
    assert op.sql(RULES,op.CLONE)==new
    # All recovery statements now use the compiled descriptions, proving that
    # normal world startup no longer invalidates guarded disable/enable/reapply.
    for prefix in ('spell','heroic'):
        for mode in ('disable','disable','enable','enable','forward'):
            name=prefix+'-'+mode+'.sql';assert name in m
            op.sql((REPAIR/name).read_text(),op.CLONE)
    assert op.checksums(op.TABLES,op.CLONE)==before
    p['after']=before
    op.untouched(p,True)
    op.save(REPAIR/'expected.json',p)
    op.save(REPAIR/'reviewed.json',{'original_manifest_sha256':p['manifest_sha256'],
      'repair_manifest_sha256':op.sha(REPAIR/'manifest.json'),'changes':NOTES,'holds':holds(),
      'first_startup_market':first_market,
      'production_sql_written':False,'clone_recovery_checks':10,'player_preserved':True})
    print('Exact compiled notes authenticated; recovery/reapply passed on clone. No production SQL written.',flush=True)


def checked():
    patch_manifest();review=op.load(REPAIR/'reviewed.json')
    assert holds()==review['holds'],'New hold requires separate diagnosis'
    assert op.sha(STAGE/'manifest.json')==review['original_manifest_sha256']
    assert op.sha(REPAIR/'manifest.json')==review['repair_manifest_sha256']
    return op.load(REPAIR/'expected.json')


def resume():
    p=checked();closed()
    assert not (REPAIR/'resume-started.json').exists()
    op.untouched(p,True)
    review=op.load(REPAIR/'reviewed.json')
    assert op.b.verify_market(op.load(STAGE/'evidence/market-before.json'),op.r.state('game')['State']['StartedAt'])==review['first_startup_market']
    data=op.load(STAGE/'evidence/stopped-state.json');assert op.saved_state()==data
    caches=op.load(STAGE/'evidence/generated-caches.json')
    for n,row in caches.items():assert op.sha(op.ROOT/'data/server/shared'/n)==row['sha256']
    op.save(REPAIR/'resume-started.json',{'migrations_replayed':False,'player_state_restored':False})
    market=op.b.market();op.save(REPAIR/'market-before.json',market)
    try:
        op.r.compose('up','-d','--wait','--wait-timeout','240','game')
        first=op.r.running(p['new_image_id'],op.binaries());op.health();time.sleep(8)
        current=op.r.running(p['new_image_id'],op.binaries());assert current['started_at']==first['started_at']
        rotation=op.b.verify_market(market,current['started_at'])
        assert op.saved_state()==data;op.untouched(p,True)
        assert op.sql('SELECT ruleset_id,rule_name,rule_value FROM rule_values ORDER BY ruleset_id,rule_name;')==p['rules_after']
        for n,row in caches.items():assert op.sha(op.ROOT/'data/server/shared'/n)==row['sha256']
        op.r.closed_ports();assert not op.r.state('gateway')['State']['Running']
        a={'game':op.r.compact('game'),'runtime':current,'market':rotation,'caches':caches,
           'player_tables':len(data['player']),'custom_tables':len(data['custom']),'rule_notes_reviewed':True}
        op.save(STAGE/'evidence/activated-closed.json',a)
        op.save(REPAIR/'resumed.json',{'status':'verified_closed','runtime':current})
        print('Resumed and verified with access closed.',flush=True)
    except BaseException:
        op.hold();raise


def open_access():
    p=checked();a=op.load(STAGE/'evidence/activated-closed.json')
    assert op.load(REPAIR/'resumed.json')['status']=='verified_closed'
    assert not (STAGE/'evidence/opening.json').exists();op.published_client()
    try:
        assert not op.r.state('gateway')['State']['Running'] and op.r.compact('game')==a['game']
        assert op.saved_state()==op.load(STAGE/'evidence/stopped-state.json')
        assert op.b.verify_market(op.load(REPAIR/'market-before.json'),a['runtime']['started_at'])==a['market']
        for n,row in a['caches'].items():assert op.sha(op.ROOT/'data/server/shared'/n)==row['sha256']
        op.untouched(p,True,True);op.health();op.r.closed_ports()
        op.save(STAGE/'evidence/opening.json',{'client_release':2026101802,'reviewed_rule_notes':True})
        op.r.compose('up','-d','--wait','--wait-timeout','60','gateway')
        assert op.r.state('gateway')['State']['Running']
        current=op.r.running(p['new_image_id'],op.binaries());op.health();op.r.closed_ports()
        assert current['started_at']==a['runtime']['started_at'];op.untouched(p,True,True)
        op.save(STAGE/'evidence/deployed.json',{**a,'runtime':current,'gateway_open':True,'client_release':2026101802,
          'database_restored':False,'owner_gameplay_accepted':False})
        print('Deployed with access open; no content replay or player restore.',flush=True)
    except BaseException:
        op.hold();raise


if __name__=='__main__':
    assert __debug__;os.umask(0o077);op.initialize()
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','resume','open'])
    action=parser.parse_args().action
    with (op.ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (op.ROOT/'private/gm-maintenance.json').exists() and op.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1'
        {'prepare':prepare,'resume':resume,'open':open_access}[action]()
