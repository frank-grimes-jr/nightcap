"""Read the completed repair receipt and independently verify running native IDs."""
import json
from pathlib import Path
from augment_icon_remote import run

ROOT = Path(__file__).resolve().parents[1]
REMOTE = r'''
import importlib.util,json,time
from pathlib import Path
path=Path('/opt/nightcap/releases/augment-icons-20261112-v1/rollout.py')
s=importlib.util.spec_from_file_location('icons',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m.initialize()
proof=m.read(m.EVIDENCE/'activation/deployed.json')
assert proof['gateway_open'] and m.r.state('gateway')['State']['Running']
runtime=m.r.running(proof['runtime']['image_id'],m.binaries());m.base.health();m.r.closed_ports()
before=m.read(m.EVIDENCE/'preflight.json')
assert all(m.r.compact(n)==before['services'][n] for n in ('db','web','tunnel'))
assert m.r.runtime()==before['runtime'] and m.h.caches()==before['caches']
repair=m.read(m.EVIDENCE/'activation/repair-verified.json')
assert repair['repaired_rows']==5 and repair['preserved_character_rows']==205 and repair['unrelated_inventory_unchanged']
print(json.dumps({'status':'PASS','verified_at':time.time(),'source_revision':proof['source_revision'],
 'main_pr':420,'main_merge_revision':'1568fb710b6441fe70bca5f9fc40f6dd805c20dc','runtime':runtime,
 'gateway_open':True,'repair':repair,'stopped_full_backup':m.read(m.EVIDENCE/'activation/backup.json'),
 'db_web_tunnel_unchanged':True,'quests_plugins_cache_unchanged':True,'client_update_required':False,
 'database_restored':False,'owner_visual_accepted':False},indent=2))
'''

if __name__ == '__main__':
    result = run(REMOTE)
    (ROOT / 'docs/items/augment-icons-20261112/production-verification.json').write_text(result, encoding='utf-8')
    data = json.loads(result)
    print(json.dumps({key: data[key] for key in ('status', 'gateway_open', 'repair', 'db_web_tunnel_unchanged', 'client_update_required')}))
