"""Read-only release baseline; never print private configuration or player rows."""
import hashlib,importlib.util,json,shutil
from pathlib import Path
ROOT=Path('/opt/nightcap/deploy/production')
HELPERS={
 'runtime':'/opt/nightcap/releases/zone-hunt-20261009/runtime_ops.py',
 'state':'/opt/nightcap/releases/classic-dungeons-rewards-20261022/rollout.py',
 'startup':'/opt/nightcap/releases/aa-level-progression-20261023-v3/rollout.py',
 'market':'/opt/nightcap/releases/quest-tier-handins-20261022/rollout.py'}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('runtime',HELPERS['runtime']);r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
image=r.state('game')['Image'];b=r.image_hashes(image)
report={'base_image_id':image,'base_hashes':b,'services':{s:r.compact(s) for s in ('game','gateway','db','web','tunnel')},
 'helpers':{k:{'path':p,'sha256':sha(p)} for k,p in HELPERS.items()},'client_channel_sha256':sha(ROOT/'data/public/channel.json'),
 'contract':{'path':'/opt/nightcap/releases/october-24-coordinated-20261024-v2/runtime-contract.json','sha256':sha('/opt/nightcap/releases/october-24-coordinated-20261024-v2/runtime-contract.json')},
 'free_bytes':shutil.disk_usage(ROOT).free,
 'runtime':r.running(image,{n:b['bin/'+n] for n in ('zone','world','ucs','loginserver','shared_memory')},r.state('game')['RestartCount'])}
state_spec=importlib.util.spec_from_file_location('saved_state',HELPERS['state']);base=importlib.util.module_from_spec(state_spec);state_spec.loader.exec_module(base)
report['inventory_schema']=base.sql('SHOW CREATE TABLE inventory;').strip()
report['currency_schema']=base.sql('SHOW CREATE TABLE character_currency;').strip()
report['existing_bazaar_tables']=base.sql("SELECT table_name FROM information_schema.tables WHERE table_schema='peq' AND table_name LIKE 'nightcap_bazaar_%';").splitlines()
report['bazaar_storage_engines']=base.sql("SELECT table_name,engine FROM information_schema.tables WHERE table_schema='peq' AND table_name IN ('inventory','character_currency');").splitlines()
report['bazaar_storage_triggers']=base.sql("SELECT trigger_name FROM information_schema.triggers WHERE trigger_schema='peq' AND event_object_table IN ('inventory','character_currency');").splitlines()
print(json.dumps(report))
