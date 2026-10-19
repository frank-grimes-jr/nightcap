"""Read-only deployment inputs. Contains no credentials or player rows."""
import base64
import hashlib
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, '/opt/nightcap/releases/zone-hunt-20261009')
import runtime_ops as r

helper = Path('/opt/nightcap/releases/zone-hunt-20261009/runtime_ops.py')
channel = (r.ROOT / 'data/public/channel.json').read_bytes()
game = r.compact('game')
result = {'services': {s: r.compact(s) for s in ('game', 'gateway', 'db', 'web', 'tunnel')},
          'base_hashes': r.image_hashes(game['image_id']),
          'runtime_helper_sha256': hashlib.sha256(helper.read_bytes()).hexdigest(),
          'runtime': r.runtime(), 'public': r.public(),
          'channel_base64': base64.b64encode(channel).decode(),
          'free_bytes': shutil.disk_usage(r.ROOT).free,
          'pet_schema': r.sql('SHOW CREATE TABLE character_pet_armor;'),
          'pet_slot_counts': r.sql('SELECT slot_id,COUNT(*) FROM character_pet_armor GROUP BY slot_id;'),
          'rules': r.sql('SELECT ruleset_id,rule_name,rule_value FROM rule_values ORDER BY ruleset_id,rule_name;'),
          'stage_exists': Path('/opt/nightcap/releases/thj-parity-20261018').exists(),
          'gm_maintenance': (r.ROOT / 'private/gm-maintenance.json').exists(),
          'shared_files': {p.name: {'bytes': p.stat().st_size, 'sha256': r.sha(p)}
                           for p in (r.ROOT / 'data/server/shared').iterdir() if p.is_file()},
          'start_source': r.out('docker','exec',game['id'],'cat','/opt/nightcap/start.py')}
print(json.dumps(result, indent=2))
