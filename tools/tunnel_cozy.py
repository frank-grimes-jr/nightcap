"""Guarded pose-only workshop revision. Capture/generation never applies SQL."""
import copy
import json
import content_patch
from pok_hub_migration import read_sql
from tunnel_services import spawn_position
from tunnel_cozy_layout import placements, STATIONS, ORNAMENTS

IDS = set(placements())
ID_SQL = ','.join(map(str, sorted(IDS)))
GROUPS = f"spawngroupID IN (SELECT spawngroupID FROM spawn2 WHERE zone='ecommons') OR npcID IN ({ID_SQL})"
KEYS = {'npc_types':['id'], 'spawngroup':['id'], 'spawnentry':['spawngroupID','npcID'],
        'spawn2':['id'], 'object':['id'], 'doors':['id'], 'grid':['id','zoneid'],
        'grid_entries':['gridid','zoneid','number'], 'zone_state_spawns':['id']}
SCOPES = {
    'npc_types':f'id IN (SELECT npcID FROM spawnentry WHERE {GROUPS}) OR id IN ({ID_SQL})',
    'spawngroup':f'id IN (SELECT spawngroupID FROM spawnentry WHERE {GROUPS})',
    'spawnentry':f'({GROUPS}) OR spawngroupID IN (SELECT spawngroupID FROM spawnentry WHERE npcID IN ({ID_SQL}))',
    'spawn2':f"zone='ecommons' OR spawngroupID IN (SELECT spawngroupID FROM spawnentry WHERE npcID IN ({ID_SQL}))",
    'object':'zoneid=22 OR id BETWEEN 999600 AND 999605',
    'doors':"zone='ecommons' OR id BETWEEN 999611 AND 999613",
    'grid':'zoneid=22', 'grid_entries':'zoneid=22',
    'zone_state_spawns':f'zone_id=22 OR npc_id IN ({ID_SQL})',
}

def capture(query=read_sql):
    return content_patch.capture(query, SCOPES)

def normalize(rows):
    return sorted(json.dumps(row, sort_keys=True) for row in rows)

def index(rows, table):
    result = {tuple(row[key] for key in KEYS[table]): row for row in rows[table]}
    if len(result) != len(rows[table]):
        raise ValueError('Duplicate row key: '+table)
    return result

def topology(rows):
    for table in KEYS:
        index(rows, table)
    npcs = {int(n['id']): n for n in rows['npc_types']}
    result = {}
    for ident in IDS:
        if ident not in npcs:
            raise ValueError('Missing NPC: '+str(ident))
        entries = [e for e in rows['spawnentry'] if int(e['npcID']) == ident]
        if len(entries) != 1 or entries[0]['chance'] != '100':
            raise ValueError('Shared/missing NPC group: '+str(ident))
        group = entries[0]['spawngroupID']
        if len([e for e in rows['spawnentry'] if e['spawngroupID'] == group]) != 1:
            raise ValueError('Shared spawn group')
        if len([g for g in rows['spawngroup'] if g['id'] == group]) != 1:
            raise ValueError('Missing group')
        spawns = [s for s in rows['spawn2'] if s['spawngroupID'] == group]
        if len(spawns) != 1 or any(spawns[0][key] != value for key, value in
                dict(zone='ecommons',version='0',pathgrid='0').items()):
            raise ValueError('Shared/moving/cross-zone spawn: '+str(ident))
        result[ident] = spawns[0]
    return result

def relocated_state(state, spawns):
    # Preserve corpses, metadata and other instances, even if the IDs match.
    if any(state[key] != value for key, value in
           dict(zone_id='22',instance_id='0',is_corpse='0',is_zone='0').items()):
        return False
    related = [s for ident,s in spawns.items() if state['npc_id'] == str(ident)
               or state['spawn2_id'] == s['id'] or state['spawngroup_id'] == s['spawngroupID']]
    if not related:
        return False
    if len(related) != 1:
        raise ValueError('Ambiguous saved-state identity')
    spawn = related[0]
    ident = next(i for i,s in spawns.items() if s is spawn)
    if (state['spawn2_id'] != spawn['id'] or state['spawngroup_id'] != spawn['spawngroupID']
            or state['npc_id'] not in ('0',str(ident))):
        raise ValueError('Ambiguous saved-state identity')
    return True

def ornaments(rows):
    doors = index(rows, 'doors')
    result = []
    for ident, (doorid, donor, name, x, y, heading, size) in ORNAMENTS.items():
        source = doors.get((str(donor),))
        if source is None or any(source[k] != v for k,v in
                dict(zone='ecommons',version='0',name=name,dest_zone='NONE').items()):
            raise ValueError('Ornament donor drift: '+str(donor))
        # Native doors process dynamic-zone/adventure switches before opentype.
        if any(source.get(k, '0') != '0' for k in ('dz_switch_id','is_ldon_door',
                'triggerdoor','triggertype','door_param','guild','lockpick','keyitem',
                'nokeyring','dest_instance')):
            raise ValueError('Interactive ornament donor: '+str(donor))
        result.append(dict(source,id=str(ident),doorid=str(doorid),pos_x=str(x),pos_y=str(y),
                           pos_z='0',heading=str(heading),size=str(size),opentype='58',
                           triggerdoor='0',door_param='0'))
    return result

def desired(before):
    after = copy.deepcopy(before)
    rows = after['rows']; spawns = topology(rows)
    for ident, pose in placements().items():
        spawns[ident].update(spawn_position(pose))
    objects = index(rows, 'object')
    for ident, (name,x,y,heading) in STATIONS.items():
        obj = objects.get((str(ident),))
        if obj is None or obj['zoneid'] != '22' or obj['display_name'] != name:
            raise ValueError('Station identity drift')
        obj.update(xpos=str(x),ypos=str(y),zpos='0',heading=str(heading))
    doorids = {v[0] for v in ORNAMENTS.values()}
    if any(int(d['id']) in ORNAMENTS or (d['zone']=='ecommons' and int(d['doorid']) in doorids) for d in rows['doors']):
        raise ValueError('Ornament collision or already installed')
    rows['doors'] += ornaments(rows)
    rows['zone_state_spawns'] = [s for s in rows['zone_state_spawns'] if not relocated_state(s,spawns)]
    return after

def patch_sql(before, after):
    spawns = topology(before['rows']); topology(after['rows'])
    spawnids = {s['id'] for s in spawns.values()}
    for table in KEYS:
        old = index(before['rows'],table); new = index(after['rows'],table)
        if table == 'doors':
            owned = {(str(i),) for i in ORNAMENTS}
            expected = {(d['id'],):d for d in ornaments(before['rows'])}
            a = {k:v for k,v in old.items() if k in owned}
            b = {k:v for k,v in new.items() if k in owned}
            if not ((not a and b == expected) or (a == expected and not b)):
                raise ValueError('Unapproved ornament mutation')
            if {k:v for k,v in old.items() if k not in owned} != {k:v for k,v in new.items() if k not in owned}:
                raise ValueError('Existing door mutation')
            continue
        if table == 'zone_state_spawns':
            if new.keys()-old.keys() or any(old[k]!=v for k,v in new.items()):
                raise ValueError('Never restore/mutate saved state')
            if any(not relocated_state(row,spawns) for k,row in old.items() if k not in new):
                raise ValueError('Unrelated saved-state deletion')
            continue
        if old.keys() != new.keys():
            raise ValueError('Content insertion/deletion: '+table)
        for key,row in new.items():
            allowed = set()
            if table == 'spawn2' and row['id'] in spawnids:
                allowed = {'x','y','z','heading'}
            if table == 'object' and int(row['id']) in STATIONS:
                allowed = {'xpos','ypos','zpos','heading'}
            if row.keys()!=old[key].keys() or {k for k in row if row[k]!=old[key][k]}-allowed:
                raise ValueError('Unapproved content mutation: '+table)
    return content_patch.patch_sql(before,after,KEYS,SCOPES)

def rollback_target(original, current, expected):
    for table in KEYS:
        if table != 'zone_state_spawns' and normalize(current['rows'][table]) != normalize(expected['rows'][table]):
            raise ValueError('Rollback static content drift: '+table)
    spawns = topology(current['rows'])
    target = copy.deepcopy(original)
    target['rows']['zone_state_spawns'] = [s for s in current['rows']['zone_state_spawns'] if not relocated_state(s,spawns)]
    return target
