import base64,hashlib,json,shutil,sys
from pathlib import Path
sys.path.insert(0,'/opt/nightcap/releases/zone-hunt-20261009')
import runtime_ops as r
game=r.compact('game')
channel=r.ROOT/'data/public/channel.json'
print(json.dumps({'services':{s:r.compact(s) for s in ('game','gateway','db','web','tunnel')},'base_hashes':r.image_hashes(game['image_id']),'runtime_helper_sha256':r.sha(Path(r.__file__)),'client_channel_sha256':r.sha(channel),'channel_manifest':json.loads(base64.b64decode(json.loads(channel.read_text())['manifest'])),'free_bytes':shutil.disk_usage(r.ROOT).free,'stage_exists':Path('/opt/nightcap/releases/all-class-aa-20261019').exists(),'gm_maintenance':(r.ROOT/'private/gm-maintenance.json').exists(),'aa389':r.sql('SELECT * FROM aa_ability WHERE id=389;'),'era':r.sql("SELECT ruleset_id,rule_name,rule_value FROM rule_values WHERE rule_name IN ('Character:MaxLevel','Expansion:CurrentExpansion','World:ExpansionSettings','Character:AAExpMinLevel');"),'wiki':str((r.ROOT/'data/public/wiki/current').readlink()),'shared_files':{p.name:{'bytes':p.stat().st_size,'sha256':r.sha(p)} for p in (r.ROOT/'data/server/shared').iterdir() if p.is_file()}},indent=2))