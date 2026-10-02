"""Guarded, reversible social tunnel revision; generation never applies SQL."""
import copy
import json
from pathlib import Path
import content_patch
from pok_hub_migration import read_sql, sql_value
from tunnel_courts import class_members, CLASSES
from tunnel_services import spawn_position
from tunnel_social_layout import placements, paths, STATIONS, MERCHANT_NAMES

NATIVES={22033,22073,22081,22082,22083,22084,22085,22086,22087,22088,22089,
         22104,22105,22106,22107,22108,22109,22110,22111,22112,22114,22115,
         22116,22117,22118,22119}
IDS=set(placements())|set(paths())|NATIVES
ORIGINAL_MERCHANT_NAMES={997899+c:CLASSES[c-1].replace(' ','_')+
    ('_Discipline_Merchant' if c in (1,7,9,16) else '_Song_Merchant' if c==8 else '_Spell_Merchant')
    for c in range(1,17)}
ID_SQL=','.join(map(str,sorted(IDS)))
GROUP_SCOPE=f'spawngroupID IN (SELECT spawngroupID FROM spawnentry WHERE npcID IN ({ID_SQL}))'
KEYS={'npc_types':['id'],'spawngroup':['id'],'spawnentry':['spawngroupID','npcID'],
      'spawn2':['id'],'grid':['id','zoneid'],'grid_entries':['gridid','zoneid','number'],
      'object':['id'],'zone_state_spawns':['id']}
SCOPES={
    'npc_types':f'id IN ({ID_SQL}) OR name IN ('+','.join(sql_value(n) for n in MERCHANT_NAMES.values())+')',
    'spawngroup':f'id IN (SELECT spawngroupID FROM spawnentry WHERE npcID IN ({ID_SQL}))',
    'spawnentry':f'npcID IN ({ID_SQL}) OR {GROUP_SCOPE}',
    'spawn2':f'({GROUP_SCOPE}) OR pathgrid BETWEEN 999700 AND 999707',
    'grid':'id BETWEEN 999700 AND 999707',
    'grid_entries':'gridid BETWEEN 999700 AND 999707',
    'object':'id BETWEEN 999600 AND 999605',
    'zone_state_spawns':f'npc_id IN ({ID_SQL}) OR spawngroup_id IN (SELECT spawngroupID FROM spawnentry WHERE npcID IN ({ID_SQL})) OR spawn2_id IN (SELECT id FROM spawn2 WHERE {GROUP_SCOPE})',
}

def capture(query=read_sql):return content_patch.capture(query,SCOPES)
def indexed(table,row):return content_patch.indexed(table,row,KEYS)

def safe_states(rows,spawns,entries):
    groups={e['spawngroupID']:e['npcID'] for e in entries}
    topology={s['id']:(s['spawngroupID'],groups[s['spawngroupID']]) for s in spawns}
    for r in rows:
        if (topology.get(r['spawn2_id'])!=(r['spawngroup_id'],r['npc_id']) or
            any(r[k]!=v for k,v in dict(zone_id='22',instance_id='0',is_corpse='0',is_zone='0').items())):
            raise ValueError('Ambiguous saved state: preserve and investigate')

def desired(before):
    after=copy.deepcopy(before);r=after['rows'];npcs={int(n['id']):n for n in r['npc_types']}
    if set(npcs)!=IDS or len(r['npc_types'])!=len(IDS):raise ValueError('Roster/name collision')
    entries=r['spawnentry'];groups={e['spawngroupID']:int(e['npcID']) for e in entries}
    if (len(entries)!=len(IDS) or set(groups.values())!=IDS or len(groups)!=len(IDS) or
        any(e['chance']!='100' for e in entries)):
        raise ValueError('Shared spawn group or NPC reference')
    if {s['id'] for s in r['spawngroup']}!=set(groups) or len(r['spawngroup'])!=len(IDS):
        raise ValueError('Missing spawn group')
    if len(r['spawn2'])!=len(IDS) or {s['spawngroupID'] for s in r['spawn2']}!=set(groups):
        raise ValueError('Shared or missing spawn location')
    for s in r['spawn2']:
        ident=groups[s['spawngroupID']]
        if s['zone']!='ecommons' or s['version']!='0' or int(s['pathgrid'])!=(ident if ident in paths() else 0):
            raise ValueError('Zone, instance, or path topology changed')
    safe_states(r['zone_state_spawns'],r['spawn2'],entries)
    for cls,(trainer,merchant) in class_members().items():
        if npcs[trainer]['class']!=str(cls+19) or npcs[merchant]['class']!='41':
            raise ValueError('Class service function changed')
        if npcs[merchant]['name']==MERCHANT_NAMES[merchant]:raise ValueError('Social layout already installed')
        if npcs[merchant]['name']!=ORIGINAL_MERCHANT_NAMES[merchant] or npcs[merchant]['merchant_id']!=str(99299+cls):
            raise ValueError('Class merchant identity or stock link drift')
        npcs[merchant]['name']=MERCHANT_NAMES[merchant]
    positions=placements()
    for ident,route in paths().items():positions[ident]={k:route[0][k] for k in ('x','y','z','heading')}
    for s in r['spawn2']:
        ident=groups[s['spawngroupID']]
        if ident in positions:s.update(spawn_position(positions[ident]))
    if len(r['grid'])!=8 or {int(g['id']) for g in r['grid']}!=set(paths()):raise ValueError('Missing walking grid')
    for g in r['grid']:
        if g['zoneid']!='22' or g['type']!='3' or g['type2']!='1':raise ValueError('Walking mode drift')
        g['type2']='0'  # native Random Half: pause for 50–100% of the waypoint duration
    if len(r['grid_entries'])!=32:raise ValueError('Walking route drift')
    expected={(i,j) for i in paths() for j in range(1,5)}
    if {(int(p['gridid']),int(p['number'])) for p in r['grid_entries']}!=expected:raise ValueError('Walking points changed')
    for p in r['grid_entries']:
        if p['zoneid']!='22':raise ValueError('Shared walking grid')
        waypoint=paths()[int(p['gridid'])][int(p['number'])-1]
        p.update({k:str(round(v)) if k=='heading' else str(v) for k,v in waypoint.items()})
    if len(r['object'])!=6 or {int(o['id']) for o in r['object']}!=set(STATIONS):raise ValueError('Station roster drift')
    for o in r['object']:
        label,x,y,h=STATIONS[int(o['id'])]
        if o['zoneid']!='22' or o['display_name']!=label:raise ValueError('Station identity changed')
        o.update(xpos=str(x),ypos=str(y),zpos='0',heading=str(h))
    # Keep all untouched native states. Invalidate only relocated actors, after
    # proving the entire referenced scope contains no corpse/instance ambiguity.
    r['zone_state_spawns']=[s for s in r['zone_state_spawns'] if int(s['npc_id']) not in positions]
    return after

FIELDS={'npc_types':{'name'},'spawn2':{'x','y','z','heading'},'grid':{'type2'},
        'grid_entries':{'x','y','z','heading','pause'},'object':{'xpos','ypos','zpos','heading'}}

def patch_sql(before,after):
    safe_states(before['rows']['zone_state_spawns'],before['rows']['spawn2'],before['rows']['spawnentry'])
    for table,keys in KEYS.items():
        old={tuple(r[k] for k in keys):r for r in before['rows'][table]}
        new={tuple(r[k] for k in keys):r for r in after['rows'][table]}
        if table=='zone_state_spawns':
            if new.keys()-old.keys():raise ValueError('Never restore stale saved states')
            if any(row!=new[k] for k,row in old.items() if k in new):raise ValueError('Saved state mutation')
            moved=set(placements())|set(paths())
            if any(int(r['npc_id']) not in moved for k,r in old.items() if k not in new):
                raise ValueError('Untouched NPC saved state deletion')
        elif old.keys()!=new.keys():raise ValueError('No content insertion/deletion in social revision')
        for key,row in new.items():
            if {k for k in row if row[k]!=old[key][k]}-FIELDS.get(table,set()):raise ValueError('Unapproved content mutation: '+table)
            if table=='npc_types' and row!=old[key] and int(row['id']) not in MERCHANT_NAMES:
                raise ValueError('Only class merchant names may change')
    return content_patch.patch_sql(before,after,KEYS,SCOPES)

def rollback_target(original,current,expected):
    for table,keys in KEYS.items():
        if table=='zone_state_spawns':continue
        normalize=lambda rows:sorted(json.dumps(r,sort_keys=True) for r in rows)
        if normalize(current['rows'][table])!=normalize(expected['rows'][table]):raise ValueError('Rollback content drift: '+table)
    safe_states(current['rows']['zone_state_spawns'],current['rows']['spawn2'],current['rows']['spawnentry'])
    result=copy.deepcopy(original)
    moved=set(placements())|set(paths())
    result['rows']['zone_state_spawns']=[r for r in current['rows']['zone_state_spawns'] if int(r['npc_id']) not in moved]
    return result
