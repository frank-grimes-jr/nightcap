"""One named-victory correction from an exact retained player kill event.

Run via the pinned private SSH transport only after successful title activation.
No title award, worn title, generic slayer/dragon counter or unrelated player write.
"""
from pathlib import Path
import fcntl
import importlib.util
import json
import sys
import time

STAGE=Path('/opt/nightcap/releases/titles-live-20261114-v1')
spec=importlib.util.spec_from_file_location('titles_live',STAGE/'release.py')
release=importlib.util.module_from_spec(spec);sys.modules[spec.name]=release;spec.loader.exec_module(release)
with (release.ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
    deadline=time.monotonic()+1200
    for handle in (lock,gm):
        while True:
            try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);break
            except BlockingIOError:
                assert time.monotonic()<deadline,'Maintenance lock remains owned; no correction started'
                time.sleep(5)
    op=release.initialize()
    assert not (op.ROOT/'private/gm-maintenance.json').exists()
    sql=op.prior.sql
    assert sql("SELECT IS_FREE_LOCK('nightcap_gm_writes')").strip()=='1'
    dep=op.read(op.ACTIVE/'deployed.json')
    assert dep['gateway_open'] and op.r.compact('gateway')['running']
    assert op.r.compact('game')['image_id']==dep['image']
    op.title_state()
    started=op.ACTIVE/'palwar-nagafen-started.json'
    receipt=op.ACTIVE/'palwar-nagafen-correction.json'
    assert not started.exists() and not receipt.exists(),'Inspect existing correction; never replay uncertain writes'
    event=sql("SELECT JSON_OBJECT('id',id,'character',character_id,'zone',zone_id,'instance',instance_id,'type',event_type_name,'data',event_data,'time',created_at) FROM player_event_logs WHERE id=20094")
    event=json.loads(event)
    assert {k:event[k] for k in ['id','character','zone','instance','type','time']}==dict(id=20094,character=29,zone=32,instance=0,type='Killed Raid NPC',time='2026-11-14 19:40:51')
    data=json.loads(event['data']) if isinstance(event['data'],str) else event['data']
    assert data['npc_id']==32040 and data['npc_name']=='Lord Nagafen'
    assert sql("SELECT COUNT(*) FROM character_data c JOIN account a ON a.id=c.account_id WHERE c.id=29 AND c.name='Palwar' AND c.gm=0 AND a.status=0").strip()=='1'
    old=sql('SELECT counter_id,value FROM nightcap_title_counters WHERE character_id=29 ORDER BY counter_id')
    op.p.save(started,dict(character_id=29,event=event,counters_before=old,scope='named Nagafen victory only'))
    # The statement itself rechecks ordinary-character identity and source-event
    # ownership. Unique primary key makes an already present victory a no-op.
    changed=sql("INSERT IGNORE INTO nightcap_title_counters(character_id,counter_id,value) SELECT c.id,100,1 FROM character_data c JOIN account a ON a.id=c.account_id JOIN player_event_logs e ON e.character_id=c.id WHERE c.id=29 AND c.name='Palwar' AND c.gm=0 AND a.status=0 AND e.id=20094 AND e.zone_id=32 AND e.instance_id=0 AND e.event_type_name='Killed Raid NPC' AND JSON_EXTRACT(e.event_data,'$.npc_id')=32040; SELECT ROW_COUNT()").strip()
    assert changed in ('0','1'),'Uncertain write acknowledgment: inspect rather than replay'
    current=sql('SELECT counter_id,value FROM nightcap_title_counters WHERE character_id=29 ORDER BY counter_id')
    assert int(sql('SELECT value FROM nightcap_title_counters WHERE character_id=29 AND counter_id=100').strip())>=1
    result=dict(result='PASS',character='Palwar',character_id=29,event_id=20094,npc_id=32040,
        named_counter=100,counters_before=old,counters_after=current,changed=int(changed),
        generic_counters_written=False,award_inserted_by_operator=False,worn_title_changed=False,
        next_step='Open Titles or use #titles to reconcile Flamebreaker and receive the native first-award notification')
    op.p.save(receipt,result)
    print(json.dumps(result))
