"""Fresh-preimage Unrest placement patch; reuse reviewed content transaction mechanics."""
import copy
import json
import content_patch

KEYS={'spawn2':['id'],'nightcap_waypoints':['zone'],'zone_state_spawns':['id'],
      'npc_types':['id'],'spawnentry':['spawngroupID','npcID']}
SCOPES={'spawn2':"zone='unrest'",'nightcap_waypoints':"zone='unrest'",
        'zone_state_spawns':'zone_id=63','npc_types':'id IN (999240,999228)',
        'spawnentry':'spawngroupID IN (999240,999228)'}
OLD=(118,881,3.75,0)
NEW=(52,-38,3,0)
POSE=('x','y','z','heading')

def capture(query):return content_patch.capture(query,SCOPES)
def normalize(rows):return sorted(json.dumps(row,sort_keys=True) for row in rows)
def index(rows,table):
    result={tuple(row[key] for key in KEYS[table]):row for row in rows[table]}
    if len(result)!=len(rows[table]):raise ValueError('Duplicate identity: '+table)
    return result
def coordinates(row):return tuple(float(row[k]) for k in POSE)
def set_pose(row,pose,table):
    row.update({key:format(value,'.6f') if table=='spawn2' else format(value,'g') for key,value in zip(POSE,pose)})
def topology(rows):
    for table in KEYS:index(rows,table)
    spawns=index(rows,'spawn2')
    for ident,group in (('3266123','999240'),('3266037','999228')):
        spawn=spawns.get((ident,))
        if spawn is None or any(spawn.get(k)!=v for k,v in dict(zone='unrest',version='0',spawngroupID=group,pathgrid='0').items()):
            raise ValueError('Unrest spawn identity drift')
        if len([s for s in rows['spawn2'] if s['spawngroupID']==group])!=1:raise ValueError('Duplicate service spawn')
        entries=[e for e in rows['spawnentry'] if e['spawngroupID']==group]
        if len(entries)!=1 or entries[0]['npcID']!=group or entries[0]['chance']!='100':raise ValueError('Spawn group drift')
    waypoint=index(rows,'nightcap_waypoints').get(('unrest',))
    if waypoint is None or waypoint['zone_id']!='63':raise ValueError('Waypoint identity drift')
    return {999240:spawns[('3266123',)],999228:spawns[('3266037',)]}
def relocated_state(row,spawns):
    return all(row.get(k)==v for k,v in dict(zone_id='63',instance_id='0',is_corpse='0',is_zone='0',spawn2_id='3266123',spawngroup_id='999240').items()) and row.get('npc_id') in ('0','999240')
def desired(before):
    after=copy.deepcopy(before);rows=after['rows'];spawns=topology(rows)
    waypoint=rows['nightcap_waypoints'][0]
    if coordinates(spawns[999240])!=OLD or coordinates(waypoint)!=OLD or coordinates(spawns[999228])!=NEW or waypoint['is_dungeon']!='0':
        raise ValueError('Reviewed placement drift')
    set_pose(spawns[999240],NEW,'spawn2');set_pose(waypoint,NEW,'nightcap_waypoints')
    for row in rows['zone_state_spawns']:
        if relocated_state(row,spawns):set_pose(row,NEW,'zone_state_spawns')
    return after
def patch_sql(before,after):
    spawns=topology(before['rows']);topology(after['rows'])
    for table in KEYS:
        old=index(before['rows'],table);new=index(after['rows'],table)
        if old.keys()!=new.keys():raise ValueError('Insertion/deletion forbidden: '+table)
        for key,row in new.items():
            allowed=set()
            if table=='spawn2' and key==('3266123',):allowed=set(POSE)
            if table=='nightcap_waypoints' and key==('unrest',):allowed=set(POSE)
            if table=='zone_state_spawns' and relocated_state(old[key],spawns):allowed=set(POSE)
            if old[key].keys()!=row.keys() or {k for k in row if row[k]!=old[key][k]}-allowed:
                raise ValueError('Unowned mutation: '+table)
    target=coordinates(after['rows']['nightcap_waypoints'][0])
    if target not in (OLD,NEW) or coordinates(topology(after['rows'])[999240])!=target:raise ValueError('Unapproved destination')
    return content_patch.patch_sql(before,after,KEYS,SCOPES)
def rollback_target(original,current,expected):
    for table in KEYS:
        if table!='zone_state_spawns' and normalize(current['rows'][table])!=normalize(expected['rows'][table]):
            raise ValueError('Rollback static content drift: '+table)
    target=copy.deepcopy(current)
    for table in KEYS:
        if table!='zone_state_spawns':target['rows'][table]=copy.deepcopy(original['rows'][table])
    spawns=topology(target['rows'])
    for row in target['rows']['zone_state_spawns']:
        if relocated_state(row,spawns):set_pose(row,OLD,'zone_state_spawns')
    return target
