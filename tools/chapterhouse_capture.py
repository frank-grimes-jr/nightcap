"""Capture local Chapterhouse content read-only; never copy character data."""
import datetime
import json
from pathlib import Path
from dungeon_capture import query, rows

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/quests/camil-chapterhouse'

def capture():
    result = dict(captured_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  environment='local', scope='Content only; production requires a fresh preimage')
    result['zone'] = rows('zone', "short_name IN ('chapterhouse','commons') AND version=0")
    result['spawn2'] = rows('spawn2', "zone='chapterhouse'")
    groups = ','.join(str(s['spawngroupID']) for s in result['spawn2'])
    result['spawnentry'] = rows('spawnentry', f'spawngroupID IN ({groups})')
    npcs = ','.join(str(s['npcID']) for s in result['spawnentry'])
    result['npc_types'] = rows('npc_types', f'id IN ({npcs})')
    result['doors'] = rows('doors', "zone='chapterhouse'")
    result['templates'] = {t: rows(t, w)[0] for t,w in (
        ('npc_types','id=999228'), ('spawngroup','id=999228'),
        ('spawnentry','npcID=999228'), ('spawn2',"zone='unrest' AND spawngroupID=999228"))}
    result['benchmarks'] = rows('npc_types','id IN (73103,32040,63092,66095)')
    result['helmet'] = rows('items','id=990500')
    result['reservations'] = {}
    for table, where in (
        ('npc_types','id BETWEEN 998820 AND 998859'),
        ('spawngroup','id BETWEEN 998820 AND 998859'),
        ('spawnentry','npcID BETWEEN 998820 AND 998859 OR spawngroupID BETWEEN 998820 AND 998859'),
        ('spawn2','id BETWEEN 9220000 AND 9220099'),
        ('items','id BETWEEN 961000 AND 961019'),
        ('tasks','id=9800'),('task_activities','taskid=9800')):
        result['reservations'][table] = query(f'SELECT COUNT(*) FROM `{table}` WHERE {where}')[0][0]
    for table in ('nightcap_waypoints','zone_points','ground_spawns','fishing','forage','global_loot'):
        result[table+'_schema'] = query('SHOW COLUMNS FROM `'+table+'`')
    result['waypoint'] = query("SELECT * FROM nightcap_waypoints WHERE zone='unrest'")
    result['zone_points'] = query("SELECT * FROM zone_points WHERE zone='chapterhouse'")
    result['global_loot'] = query('SELECT * FROM global_loot WHERE enabled=1')
    return result

if __name__ == '__main__':
    data = capture()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'local-content.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({k:len(v) for k,v in data.items() if isinstance(v,list)}))
    print(json.dumps(data['reservations']))
