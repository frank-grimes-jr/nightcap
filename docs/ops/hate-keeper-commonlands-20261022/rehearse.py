"""Execute the actual scoped migration on a new isolated local MariaDB schema."""
import copy,json,sys,uuid
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tools/tests')]
from rehearse_dungeons import query
from pok_hub_migration import insert
import hate_keeper as patch

def normalize(snapshot):return {t:sorted(json.dumps(r,sort_keys=True) for r in rows) for t,rows in snapshot['rows'].items()}
def main():
    db='nightcap_dungeon_rehearsal_'+uuid.uuid4().hex[:12]
    source=json.loads((HERE/'preimages.json').read_text())
    query('CREATE DATABASE `'+db+'` CHARACTER SET utf8mb4;','information_schema')
    for table,meta in source['schemas'].items():
        query(meta['create']+';',db)
        query('\n'.join(insert(table,r) for r in source['rows'][table]),db)
    def capture():return patch.capture(lambda q:query(q,db).stdout)
    original=capture();assert normalize(original)==normalize(source)
    target=patch.desired(original);forward=patch.patch_sql(original,target)
    failure=forward.replace('COMMIT;',"SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='synthetic keeper failure'; COMMIT;")
    p=query(failure,db,False);assert p.returncode and 'synthetic keeper failure' in p.stderr
    assert normalize(capture())==normalize(original)
    query(forward,db);assert normalize(capture())==normalize(target)
    p=query(forward,db,False);assert p.returncode and 'drift' in p.stderr.lower()
    query(patch.patch_sql(target,original),db);assert normalize(capture())==normalize(original)
    # Actual saved-state deletion is restricted to the old public service.
    for row in ((987654,76,0,998812,9100012,998812,50000),(987655,76,2,998812,9100012,998812,50000),(987656,76,0,123,9100013,123,100)):
        saved=dict(zip(('id','zone_id','instance_id','npc_id','spawn2_id','spawngroup_id','hp'),row))
        saved.update(x=0,y=0,z=0,heading=0,respawn_time=0,variance=0)
        query(insert('zone_state_spawns',saved),db)
    before=capture();assert len(before['rows']['zone_state_spawns'])==1
    untouched=query('SELECT id,instance_id,hp FROM zone_state_spawns WHERE id IN (987655,987656) ORDER BY id;',db).stdout
    query(patch.patch_sql(before,patch.desired(before)),db)
    assert not capture()['rows']['zone_state_spawns']
    assert query('SELECT id,instance_id,hp FROM zone_state_spawns WHERE id IN (987655,987656) ORDER BY id;',db).stdout==untouched
    report={'status':'passed','database':db,'source':'captured production DDL and public service rows only',
            'forward_exact':True,'inverse_exact':True,'mid_transaction_failure_rolled_back':True,
            'repeat_rejected':True,'private_and_unrelated_saved_state_preserved':True,'production_changed':False}
    (HERE/'rehearsal.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
if __name__=='__main__':main()
