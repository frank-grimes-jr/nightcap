"""Capture Kael public content in read-only transactions; no player records."""
import json
from pathlib import Path
from dungeon_capture import query, rows

OUT=Path(__file__).resolve().parents[1]/'docs/quests/warhelm'

def capture():
    data={'environment':'local','zone':rows('zone',"short_name IN ('kael','everfrost') AND version=0"),
          'spawn2':rows('spawn2',"zone='kael'"),'doors':rows('doors',"zone='kael'"),
          'helmet':rows('items','id=990500')}
    groups=','.join(str(s['spawngroupID']) for s in data['spawn2'])
    data['spawnentry']=rows('spawnentry',f'spawngroupID IN ({groups})')
    ids=','.join(str(e['npcID']) for e in data['spawnentry'])
    data['npc_types']=rows('npc_types',f'id IN ({ids})')
    data['templates']={t:rows(t,w)[0] for t,w in [('npc_types','id=999228'),('spawngroup','id=999228'),('spawnentry','npcID=999228'),('spawn2',"zone='unrest' AND spawngroupID=999228")]}
    data['reservations']={}
    for t,w in [('npc_types','id BETWEEN 998860 AND 998899 '),('spawngroup','id BETWEEN 998860 AND 998899 '),('spawnentry','npcID BETWEEN 998860 AND 998899 '),('spawn2','id BETWEEN 9230000 AND 9230099'),('items','id BETWEEN 961020 AND 961039 OR id=990510 OR id BETWEEN 960420 AND 960425'),('tasks','id IN (9744,9745,9801)')]:
        data['reservations'][t]=query(f'SELECT COUNT(*) FROM `{t}` WHERE {w}')[0][0]
    hazards={}
    for t,w in [('zone_points',"zone='kael'"),('ground_spawns','zoneid=113'),('fishing','zoneid=113'),('forage','zoneid=113'),('traps',"zone='kael'"),('object','zoneid=113')]:
        cols=[r[0] for r in query('SHOW COLUMNS FROM `'+t+'`')]
        expr=','.join("'"+c+"',`"+c+'`' for c in cols)
        hazards[t]=[json.loads(r[0]) for r in query(f'SELECT JSON_OBJECT({expr}) FROM `{t}` WHERE {w}')]
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'local-content.json').write_text(json.dumps(data,indent=2)+'\n')
    (OUT/'secondary-content.json').write_text(json.dumps(hazards,indent=2)+'\n')
    print(json.dumps({'reservations':data['reservations'],'spawns':len(data['spawn2']), 'npcs':[(n['id'],n['name']) for n in data['npc_types'] if any(s in n['name'].lower() for s in ('vindicator','tormax','statue','idol','protector'))]}))

if __name__=='__main__':capture()
