"""Read the completed DoT receipt and independently verify running native IDs."""
import json
from pathlib import Path
from dot_release_remote import run

ROOT = Path(__file__).resolve().parents[1]
REMOTE = r'''
import importlib.util,json,time
from pathlib import Path
path=Path('/opt/nightcap/releases/dot-no-initial-damage-20261112-v2/rollout.py')
s=importlib.util.spec_from_file_location('quick_buff',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);m=m.initialize()
proof=m.read(m.EVIDENCE/'activation/deployed.json')
assert proof['gateway_open'] and m.r.state('gateway')['State']['Running']
runtime=m.r.running(proof['runtime']['image_id'],m.binaries());m.base.health();m.r.closed_ports()
before=m.read(m.EVIDENCE/'preflight.json')
assert all(m.r.compact(n)==before['services'][n] for n in ('db','web','tunnel'))
assert m.r.runtime()==before['runtime'] and m.h.caches()==before['caches']
m.unchanged(before,after_open=True)
client={'release':proof['client_release'],'channel_sha256':proof['client_channel_sha256']}
assert client['release']==2026111201
print(json.dumps({'status':'PASS','verified_at':time.time(),'source_revision':proof['source_revision'],
 'runtime':runtime,
 'gateway_open':True,'client_release':client['release'],'client_channel_sha256':client['channel_sha256'],'stopped_full_backup':m.read(m.EVIDENCE/'activation/backup.json'),
 'db_web_tunnel_unchanged':True,'quests_plugins_cache_unchanged':True,'client_update_required':False,
 'database_restored':False,'owner_gameplay_accepted':False},indent=2))
'''

if __name__ == '__main__':
    result = run(REMOTE)
    (ROOT / 'docs/balance/dot-initial-damage-20261112/production-verification.json').write_text(result, encoding='utf-8')
    data = json.loads(result)
    print(json.dumps({key: data[key] for key in ('status', 'gateway_open', 'client_release', 'db_web_tunnel_unchanged', 'client_update_required')}))
