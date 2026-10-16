"""Real MariaDB lock/receipt invariants, only in the isolated rehearsal DB.

This exercises storage concurrency, not native packet scheduling or gameplay.
"""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import threading
import uuid
from rehearse_dungeons import query

ROOT=Path(__file__).resolve().parents[2]
folder=ROOT/'docs/dungeons'
db=json.loads((folder/'rehearsal.json').read_text())['database']

def race(statements):
    barrier=threading.Barrier(len(statements))
    def execute(statement):
        barrier.wait(timeout=10)
        return query(statement,db,False)
    with ThreadPoolExecutor(max_workers=len(statements)) as pool:
        return list(pool.map(execute,statements))

allocation="""START TRANSACTION;
SELECT id FROM nightcap_dungeon_state WHERE id=1 FOR UPDATE;
DO SLEEP(0.2);
SELECT MIN(candidate) INTO @native FROM (SELECT 1 AS candidate UNION SELECT id+1 FROM instance_list WHERE id>=0) ids
WHERE candidate<=32000 AND NOT EXISTS (SELECT 1 FROM instance_list i WHERE i.id=ids.candidate);
INSERT INTO instance_list(id,zone,version,start_time,duration,notes) VALUES(@native,36,0,100,43200,'isolated-concurrency');
COMMIT;"""
results=race([allocation,allocation]);assert all(r.returncode==0 for r in results)
assert query("SELECT COUNT(DISTINCT id) FROM instance_list WHERE notes='isolated-concurrency';",db).stdout.strip()=='2'
run=str(uuid.uuid4())
query(f"INSERT INTO nightcap_dungeon_runs(run_id,instance_id,instance_start,zone_id,owner_id,mode,seed,revision,expires_at) VALUES('{run}',59999,100,36,1001,1,42,2026101601,9999999999);",db)
for char in range(1001,1006):
    query(f"INSERT INTO nightcap_dungeon_members(run_id,character_id,reward_item,reward_drop_id) VALUES('{run}',{char},960001,'{uuid.uuid4()}');",db)
def enroll(char):
    return f"""START TRANSACTION;
SELECT run_id FROM nightcap_dungeon_runs WHERE run_id='{run}' FOR UPDATE;
DO SLEEP(0.2);
INSERT INTO nightcap_dungeon_members(run_id,character_id,reward_item,reward_drop_id)
SELECT '{run}',{char},960001,'{uuid.uuid4()}' FROM DUAL
WHERE (SELECT COUNT(*) FROM nightcap_dungeon_members WHERE run_id='{run}')<6;
COMMIT;"""
results=race([enroll(1006),enroll(1007)]);assert all(r.returncode==0 for r in results)
assert query(f"SELECT COUNT(*) FROM nightcap_dungeon_members WHERE run_id='{run}';",db).stdout.strip()=='6'
receipt=str(uuid.uuid4())
def deliver(slot):
    return f"""START TRANSACTION;
INSERT INTO inventory(character_id,slot_id,item_id,charges) VALUES(1001,{slot},960001,1);
DO SLEEP(0.2);
INSERT INTO character_advloot_claims(drop_id,character_id,item_id,charges,inventory_after)
VALUES('{receipt}',1001,960001,1,'isolated-concurrency');
COMMIT;"""
results=race([deliver(23),deliver(24)])
assert sum(r.returncode==0 for r in results)==1
assert query("SELECT COUNT(*) FROM inventory WHERE character_id=1001;",db).stdout.strip()=='1'
assert query(f"SELECT COUNT(*) FROM character_advloot_claims WHERE drop_id='{receipt}';",db).stdout.strip()=='1'
prefix=f"START TRANSACTION; SELECT run_id FROM nightcap_dungeon_runs WHERE run_id='{run}' FOR UPDATE; DO SLEEP(0.2);"
entry=prefix+f"UPDATE nightcap_dungeon_members SET inside_instance=1 WHERE run_id='{run}' AND character_id=1001 AND EXISTS(SELECT 1 FROM nightcap_dungeon_runs WHERE run_id='{run}' AND retired=0); COMMIT;"
reset=prefix+f"UPDATE nightcap_dungeon_runs SET retired=1 WHERE run_id='{run}' AND NOT EXISTS(SELECT 1 FROM nightcap_dungeon_members WHERE run_id='{run}' AND inside_instance<>0); COMMIT;"
results=race([entry,reset]);assert all(r.returncode==0 for r in results)
state=query(f"SELECT r.retired,m.inside_instance FROM nightcap_dungeon_runs r JOIN nightcap_dungeon_members m ON m.run_id=r.run_id WHERE r.run_id='{run}' AND m.character_id=1001;",db).stdout.strip()
assert state in ('1\t0','0\t1'),state
report=dict(status='passed',scope='Actual MariaDB transactions with concurrent sessions; no native gameplay',
            database=db,unique_concurrent_allocations=True,six_member_cap=True,
            duplicate_receipt_rolls_back_inventory=True,reset_and_entry_mutually_exclusive=True)
(folder/'concurrency-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
