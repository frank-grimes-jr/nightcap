"""Negative full-row drift control: late zone failure must roll back item edits."""
import json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]/'docs/releases/classic-raid-augments-20261112'))
from probe import remote
CODE=r"""
import importlib.util,json,sys,uuid
from pathlib import Path
folder=Path('/opt/nightcap/releases/classic-equipment-paths-20261121-candidate-v3');sys.path.insert(0,str(folder))
s=importlib.util.spec_from_file_location('equipment_release',folder/'release.py');r=importlib.util.module_from_spec(s);s.loader.exec_module(r);r.initialize()
from zone_catalog import row
from catalog import literal,generate as item_sql
db='nightcap_dungeon_stage_'+uuid.uuid4().hex[:12]
r.sql('CREATE DATABASE '+db)
try:
 for t in ('items','zone'):
  r.sql(f'CREATE TABLE {db}.{t} LIKE peq.{t}')
  where='id IN ('+r.ids+')' if t=='items' else 'id=357'
  r.sql(f'INSERT INTO {db}.{t} SELECT * FROM peq.{t} WHERE '+where)
 r.before_rows(db)
 r.sql("UPDATE zone SET long_name=CONCAT(long_name,' drift') WHERE id=357",db)
 failed=False
 try:r.sql(r.generate('forward'),db)
 except Exception:failed=True
 assert failed,'late zone drift unexpectedly accepted'
 r.sql(item_sql('before'),db)
 r.sql('UPDATE zone SET long_name='+literal(row()['long_name'])+' WHERE id=357',db)
 r.before_rows(db)
 r.sql('UPDATE items SET hp=hp+1 WHERE id='+r.ids.split(',')[0],db)
 failed=False
 try:r.sql(r.generate('forward'),db)
 except Exception:failed=True
 assert failed,'item drift unexpectedly accepted'
 assert r.sql('SELECT expansion FROM zone WHERE id=357',db).strip()=='1'
 print(json.dumps(dict(passed=True,late_zone_failure_rolls_back_all_items=True,item_drift_rejected=True,production_mutated=False)))
finally:r.sql('DROP DATABASE '+db)
"""
if __name__=='__main__':
 d=json.loads(remote(CODE,timeout=300));(HERE/'atomic-rehearsal.json').write_text(json.dumps(d,indent=2)+'\n',encoding='utf8');print(d)
