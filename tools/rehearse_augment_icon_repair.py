"""Exercise the actual guarded repair against an isolated host-only database."""
from pathlib import Path
import json
from augment_icon_remote import run

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'docs/items/augment-icons-20261112'
REMOTE = r'''
import importlib.util,json,os,re,time
from pathlib import Path
os.umask(0o077)
path=Path('/opt/nightcap/releases/last-lantern-20261107-v4/rollout.py')
s=importlib.util.spec_from_file_location('prior',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.initialize()
assert m.players()==0
stage=Path('/opt/nightcap/releases/augment-icons-20261112-v1')
capture=json.loads(sorted(stage.glob('capture-*.json'))[-1].read_text())
repair={'__name__':'repair'};exec(REPAIR,repair)
prepared=repair['prepare'](m.sql,capture)
folder=stage/'repair-rehearsal-v2';folder.mkdir(mode=0o700)
database='nightcap_dungeon_stage_20261112a101'
assert re.fullmatch('nightcap_dungeon_stage_[0-9a-f]{12}',database) and database!='peq'
assert m.sql("SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name='"+database+"';").strip()=='0'
m.sql('CREATE DATABASE `'+database+'`;')
results=[]
try:
 m.sql('CREATE TABLE inventory LIKE peq.inventory; INSERT INTO inventory SELECT * FROM peq.inventory WHERE character_id=29;',database)
 test={**prepared,'outside':repair['outside'](m.sql,prepared['columns'],database)}
 before=repair['inventory'](m.sql,database)
 try:m.sql(repair['statement'](test,fail_after=1),database)
 except Exception as e:(folder/'rollback-error.txt').write_text(str(e))
 else:raise AssertionError('Injected failure unexpectedly committed')
 assert repair['inventory'](m.sql,database)==before
 results.append('Injected mid-repair failure rolls back every row')
 m.sql("UPDATE inventory SET custom_data=CONCAT(COALESCE(custom_data,''),'review-drift') WHERE character_id=29 AND slot_id=19;",database)
 drift=repair['inventory'](m.sql,database)
 try:m.sql(repair['statement'](test),database)
 except Exception as e:(folder/'drift-error.txt').write_text(str(e))
 else:raise AssertionError('Full-row metadata drift was not rejected')
 assert repair['inventory'](m.sql,database)==drift
 results.append('Unrelated metadata drift in last target rejects and rolls back earlier updates')
 m.sql('UPDATE inventory i JOIN peq.inventory p ON p.character_id=i.character_id AND p.slot_id=i.slot_id SET i.custom_data=p.custom_data WHERE i.character_id=29 AND i.slot_id=19;',database)
 assert repair['inventory'](m.sql,database)==before
 m.sql(repair['statement'](test),database)
 verified=repair['verify'](m.sql,test,database)
 results.append('Five exact icon-only changes preserve all205 rows/augments/NULLs/metadata')
 after=repair['inventory'](m.sql,database)
 try:m.sql(repair['statement'](test),database)
 except Exception as e:(folder/'replay-error.txt').write_text(str(e))
 else:raise AssertionError('Replay accepted')
 assert repair['inventory'](m.sql,database)==after
 results.append('Replay rejects without data changes')
 assert repair['inventory'](m.sql)==before,'Production changed during isolated rehearsal'
 report={'status':'PASS','checks':results,'verified':verified,'production_inventory_written':False}
 (folder/'verified.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report,indent=2))
finally:
 m.sql('DROP DATABASE `'+database+'`;')
'''

if __name__ == '__main__':
    result = run('REPAIR=' + repr((HERE / 'repair.py').read_text(encoding='utf-8')) + '\n' + REMOTE)
    (HERE / 'repair-rehearsal.json').write_text(result, encoding='utf-8')
    print(result, end='')
