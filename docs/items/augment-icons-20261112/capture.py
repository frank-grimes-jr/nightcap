"""Read current affected inventory; retain full rows privately on the host."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time

os.umask(0o077)
stage = Path('/opt/nightcap/releases/augment-icons-20261112-v1')
stage.mkdir(mode=0o700, exist_ok=True)
path = Path('/opt/nightcap/releases/last-lantern-20261107-v4/rollout.py')
assert hashlib.sha256(path.read_bytes()).hexdigest() == '92bd9251948b503a646997f2e76844fbba9a5d018c4c31fe052bec5fa76d8ff7'
spec = importlib.util.spec_from_file_location('prior', path)
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
prior.initialize()
assert prior.players() == 0, 'Players must be logged out for a coherent incident capture'
assert prior.sql("SELECT name FROM character_data WHERE id=29;").strip() == 'Palwar'
columns = [line.split('\t')[0] for line in prior.sql('SHOW COLUMNS FROM inventory;').splitlines()]
assert all(name.replace('_', '').isalnum() for name in columns)
fields = ','.join('`' + name + '`' for name in columns)
rows = [dict(zip(columns, json.loads(line))) for line in prior.sql(
    'SELECT JSON_ARRAY(' + fields + ') FROM inventory WHERE character_id=29 ORDER BY slot_id;').splitlines()]
ids = sorted({int(row[key]) for row in rows for key in ('item_id', 'augment_one', 'augment_two',
              'augment_three', 'augment_four', 'augment_five', 'augment_six') if row[key]})
definitions = [json.loads(line) for line in prior.sql(
    "SELECT JSON_OBJECT('id',id,'name',Name,'icon',icon,'idfile',idfile,'augtype',augtype,"
    "'hero',herosforgemodel,'itemclass',itemclass) FROM items WHERE id IN (" + ','.join(map(str, ids)) + ');').splitlines()]
items = {int(row['id']): row for row in definitions}
socket_keys = ('augment_one', 'augment_two', 'augment_three', 'augment_four', 'augment_five', 'augment_six')
plan, excluded = [], []
targets = {2: 404301, 12: 404345, 17: 204852, 18: 404856, 19: 204917}
# November6 item-preimages.json records 940280 as empty-model/type22/icon517.
historical_icons = {940280: 517}
for row in rows:
    host = items[int(row['item_id'])]
    augments = [items[int(row[key])] for key in socket_keys if row[key]]
    if not augments or not row['ornament_icon']:
        continue
    genuine = [a for a in augments if int(a['augtype']) & ((1 << 19) | (1 << 20)) or int(a['hero'])]
    old_matches = [a for a in augments if a['idfile'] not in ('IT63', 'IT64') or int(a['augtype']) in (20, 21) or int(a['hero'])]
    first = old_matches[0] if old_matches else None
    # Owner identifies this character's changed equipment icons. Require the
    # precise known type22/empty-model bug afterimage and no genuine ornament.
    safe = (targets.get(int(row['slot_id'])) == int(row['item_id']) and
            first and not genuine and int(host['itemclass']) == 0 and
            int(first['augtype']) == 1 << 21 and first['idfile'] == '' and
            int(first['hero']) == int(host['hero']) == 0 and
            int(row['ornament_idfile']) == int(row['ornament_hero_model']) == 0 and
            int(row['ornament_icon']) in {int(first['icon']), historical_icons.get(int(first['id']))} and
            int(row['ornament_icon']) != int(host['icon']))
    summary = {'slot': int(row['slot_id']), 'item_id': int(row['item_id']), 'name': host['name'],
               'saved_icon': int(row['ornament_icon']), 'base_icon': int(host['icon']),
               'augments': [{'id': int(a['id']), 'name': a['name']} for a in augments]}
    if safe:
        plan.append({'before': row, 'after': {**row, 'ornament_icon': 0}, 'summary': summary})
    else:
        excluded.append(summary)
snapshot = {'captured_at': time.time(), 'columns': columns, 'rows': rows, 'definitions': definitions,
            'plan': plan, 'excluded': excluded, 'scope': 'Palwar29 only; change ornament_icon only'}
target = stage / ('capture-' + str(time.time_ns()) + '.json')
with target.open('x') as handle:
    json.dump(snapshot, handle, indent=2); handle.write('\n'); handle.flush(); os.fsync(handle.fileno())
print(json.dumps({'private_capture': str(target), 'inventory_rows': len(rows),
                  'candidates': [p['summary'] for p in plan], 'excluded_cosmetic_rows': excluded}, indent=2))
