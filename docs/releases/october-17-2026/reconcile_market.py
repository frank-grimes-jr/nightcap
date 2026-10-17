"""One-shot recovery for the observed world-start market rotation; no SQL writes."""
import argparse,datetime,fcntl,gzip,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import rollout as op

MARKET={'nightcap_market_state','nightcap_market_offers'}
def validate_change(before,after):
    assert set(before)==set(after)
    assert {n for n in before if before[n]!=after[n]}==MARKET,'Unexpected custom-table drift'
def validate_state(before,after,started):
    assert len(before)==len(after)==7
    assert before[:2]==after[:2]==['1','1']
    assert before[2]=='79' and after[2]=='80','Expected exactly one observed world-start rotation'
    assert before[3:6]==after[3:6]==['0','4','2.500000']
    stamp=datetime.datetime.fromisoformat(after[6]).replace(tzinfo=datetime.timezone.utc)
    start=datetime.datetime.fromisoformat(started.replace('Z','+00:00'))
    assert 0 <= (stamp-start).total_seconds() <= 60
def holds():return {p.name:op.sha(p) for p in sorted(op.EVIDENCE.glob('held-*.json'))}
def paired():
    op.manifest();p=op.load('preflight.json')
    assert not op.r.state('gateway')['State']['Running']
    current=op.r.running(p['new_image_id'],op.binaries(p));op.health()
    assert op.sha(op.ROOT/'data/server/shared/items')==p['expected_cache']['sha256']
    return p,current
def reconcile():
    assert not (op.EVIDENCE/'market-reconciliation.json').exists()
    assert not (op.EVIDENCE/'activated-closed.json').exists() and not (op.EVIDENCE/'opening.json').exists()
    p,current=paired();data=op.load('stopped-data.json');now=op.custom()
    assert op.player()==data['player'];validate_change(data['custom'],now)
    held=holds();assert len(held)==1
    assert op.load(next(iter(held)))['reason']=='Activation failed: preserve current state and inspect receipts before recovery'
    before=None;capture=False
    with gzip.open(op.STAGE/'private-backup/peq-before.sql.gz','rt') as f:
        for line in f:
            if line.startswith('INSERT INTO `nightcap_market_state` VALUES'):capture=True;continue
            if capture:
                match=re.fullmatch(r"\((1),(1),(79),(0),(4),(2\.500000),'([^']+)'\);\s*",line)
                assert match,'Unexpected backup state';before=list(match.groups());break
    assert before
    after=op.sql('SELECT id,enabled,epoch,expansion,loot_multiplier,buy_cost_mod,rotated_at FROM nightcap_market_state;').strip().split('\t')
    validate_state(before,after,current['started_at'])
    assert op.sql('SELECT epoch,COUNT(*) FROM nightcap_market_offers GROUP BY epoch;').strip()=='80\t42'
    invalid=op.sql("""SELECT COUNT(*) FROM nightcap_market_offers o
LEFT JOIN nightcap_market_actors a ON a.npc_id=o.npc_id
LEFT JOIN nightcap_market_catalog c ON c.item_id=o.item_id
LEFT JOIN items i ON i.id=o.item_id
WHERE a.npc_id IS NULL OR c.item_id IS NULL OR i.id IS NULL OR o.epoch<>80 OR o.remaining<>1
OR o.zone_id<>a.zone_id OR o.kind<>a.kind OR o.price_cp<=0
OR o.price_cp<>CASE o.kind WHEN 'find' THEN c.find_cp WHEN 'sell' THEN c.sell_cp ELSE c.buy_cp END
OR c.pool<>IF(o.kind='find','find','tunnel') OR c.min_expansion>(SELECT expansion FROM nightcap_market_state WHERE id=1) OR (c.max_expansion>=0 AND c.max_expansion<(SELECT expansion FROM nightcap_market_state WHERE id=1))
OR i.nodrop=0 OR i.norent=0 OR i.stackable<>0 OR i.maxcharges<>0 OR i.itemclass<>0 OR i.questitemflag<>0 OR i.attuneable<>0
OR c.buy_cp>=c.sell_cp OR c.buy_cp>=c.find_cp
OR EXISTS(SELECT 1 FROM merchantlist m JOIN npc_types n ON n.merchant_id=m.merchantid WHERE m.item=o.item_id AND n.id=o.npc_id);
SELECT COUNT(*) FROM (SELECT npc_id,kind,COUNT(*) n FROM nightcap_market_offers GROUP BY npc_id,kind HAVING n<>IF(kind='find',1,2)) x;
SELECT COUNT(*) FROM (SELECT item_id,kind,COUNT(*) n FROM nightcap_market_offers GROUP BY item_id,kind HAVING n>IF(kind='sell',3,2)) x;""").splitlines()
    assert invalid==['0','0','0'],'New market stock violates retained rotation policy'
    op.untouched(p,True);assert op.custom()==now and op.player()==data['player']
    data={'player':data['player'],'custom':now}
    op.save('market-reconciliation.json',{'reason':'Unchanged world main.cpp calls nightcap_market_rotate on startup; procedure increments epoch and replaces finite offers','held_receipts':held,'before_state':before,'after_state':after,'offer_count':42,'all_other_custom_and_player_data_preserved':True,'data':data,'operator_sha256':op.sha(Path(__file__))})
    op.save('activated-closed.json',{'game':op.r.compact('game'),'runtime':current,'cache':p['expected_cache'],'backup':op.load('backup.json'),'player_tables_preserved':len(data['player']),'custom_tables_preserved':len(now)-2,'market_rotation_reconciled':True})
    print('Verified closed-access server; exact expected market rotation recorded; no SQL restored.',flush=True)
def open_access():
    p,current=paired();a=op.load('activated-closed.json');resolution=op.load('market-reconciliation.json')
    assert holds()==resolution['held_receipts'] and resolution['operator_sha256']==op.sha(Path(__file__))
    assert not (op.EVIDENCE/'opening.json').exists()
    try:
        assert op.r.compact('game')==a['game'] and current['started_at']==a['runtime']['started_at']
        op.preserved(resolution['data']);op.untouched(p,True,True)
        op.save('opening.json',{'matching_client_sha256':op.manifest()['client_channel_sha256'],'market_resolution_sha256':op.sha(op.EVIDENCE/'market-reconciliation.json')})
        op.r.compose('up','-d','--wait','--wait-timeout','60','gateway')
        assert op.r.state('gateway')['State']['Running'];op.health();op.r.closed_ports()
        result=op.r.running(p['new_image_id'],op.binaries(p));assert result['started_at']==current['started_at']
        op.untouched(p,True,True)
        op.save('activated.json',{'status':'deployed','gateway_open':True,'runtime':result,'cache':a['cache'],'client_release':2026101702,'database_restored':False,'owner_gameplay_accepted':False,'market_rotation_reconciled':True,'player_tables_preserved':a['player_tables_preserved'],'custom_tables_preserved':a['custom_tables_preserved']})
        print('Release deployed; matching client published; access open.',flush=True)
    except BaseException:op.hold('Reconciled opening failed; preserve subsequent activity');raise
if __name__=='__main__':
    assert __debug__;op.initialize()
    action=argparse.ArgumentParser();action.add_argument('action',choices=['reconcile','open']);args=action.parse_args()
    with (op.ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (op.ROOT/'private/gm-maintenance.json').exists() and op.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1'
        {'reconcile':reconcile,'open':open_access}[args.action]()
