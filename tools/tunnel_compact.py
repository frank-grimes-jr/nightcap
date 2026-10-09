"""Guarded compact-service layout; generation is separate from deployment."""
import copy
import json
import content_patch
from pok_hub_migration import read_sql
from tunnel_courts import class_members
from tunnel_services import spawn_position
from tunnel_social import IDS, ID_SQL, GROUP_SCOPE, safe_states, MERCHANT_NAMES
from tunnel_compact_layout import placements, paths, STATIONS, CLASS_FIRES

KEYS={'npc_types':['id'],'spawngroup':['id'],'spawnentry':['spawngroupID','npcID'],
      'spawn2':['id'],'grid':['id','zoneid'],'grid_entries':['gridid','zoneid','number'],
      'object':['id'],'doors':['id'],'zone_state_spawns':['id']}
SCOPES={
    'npc_types':f'id IN ({ID_SQL})',
    'spawngroup':f'id IN (SELECT spawngroupID FROM spawnentry WHERE npcID IN ({ID_SQL}))',
    'spawnentry':f'npcID IN ({ID_SQL}) OR {GROUP_SCOPE}',
    'spawn2':f'({GROUP_SCOPE}) OR pathgrid BETWEEN 999700 AND 999707',
    'grid':'id BETWEEN 999700 AND 999707','grid_entries':'gridid BETWEEN 999700 AND 999707',
    'object':'zoneid=22 OR id BETWEEN 999600 AND 999605',
    'doors':"zone='ecommons' OR id BETWEEN 999606 AND 999610",
    'zone_state_spawns':f'npc_id IN ({ID_SQL}) OR spawngroup_id IN (SELECT spawngroupID FROM spawnentry WHERE npcID IN ({ID_SQL})) OR spawn2_id IN (SELECT id FROM spawn2 WHERE {GROUP_SCOPE})',
}

def capture(query=read_sql):return content_patch.capture(query,SCOPES)
def normalize(rows):return sorted(json.dumps(r,sort_keys=True) for r in rows)

def topology(rows):
    npcs={int(n['id']):n for n in rows['npc_types']}
    if len(npcs)!=len(IDS) or len(rows['npc_types'])!=len(IDS) or set(npcs)!=IDS:raise ValueError('Roster drift')
    entries=rows['spawnentry'];groups={e['spawngroupID']:int(e['npcID']) for e in entries}
    if len(entries)!=len(IDS) or len(groups)!=len(IDS) or set(groups.values())!=IDS or any(e['chance']!='100' for e in entries):raise ValueError('Shared NPC/group reference')
    if len(rows['spawngroup'])!=len(IDS) or {g['id'] for g in rows['spawngroup']}!=set(groups):raise ValueError('Group drift')
    if len(rows['spawn2'])!=len(IDS) or {s['spawngroupID'] for s in rows['spawn2']}!=set(groups):raise ValueError('Shared spawn location')
    for s in rows['spawn2']:
        if s['zone']!='ecommons' or s['version']!='0' or int(s['pathgrid'])!=(groups[s['spawngroupID']] if groups[s['spawngroupID']] in paths() else 0):raise ValueError('Zone/path topology drift')
    safe_states(rows['zone_state_spawns'],rows['spawn2'],entries)
    return npcs,groups

def fires(donor):
    return [dict(donor,id=str(i),doorid=str(door),pos_x=str(x),pos_y=str(y),pos_z='0',heading='0',size='45')
            for i,(door,x,y) in CLASS_FIRES.items()]

def moved(before,after):
    old=before['rows'];new=after['rows'];_,groups=topology(old)
    spawns={s['id']:s for s in new['spawn2']}
    result={groups[s['spawngroupID']] for s in old['spawn2'] if any(s[k]!=spawns[s['id']][k] for k in ('x','y','z','heading'))}
    for ident in paths():
        if normalize([p for p in old['grid_entries'] if int(p['gridid'])==ident])!=normalize([p for p in new['grid_entries'] if int(p['gridid'])==ident]):result.add(ident)
    return result

def desired(before):
    after=copy.deepcopy(before);r=after['rows'];npcs,groups=topology(r)
    for cls,(trainer,merchant) in class_members().items():
        if npcs[trainer]['class']!=str(cls+19) or npcs[merchant]['class']!='41' or npcs[merchant]['name']!=MERCHANT_NAMES[merchant] or npcs[merchant]['merchant_id']!=str(99299+cls):raise ValueError('Class service identity drift')
    positions=placements()
    for ident,route in paths().items():positions[ident]={k:route[0][k] for k in ('x','y','z','heading')}
    for s in r['spawn2']:
        ident=groups[s['spawngroupID']]
        if ident in positions:s.update(spawn_position(positions[ident]))
    if len(r['grid'])!=8 or {int(g['id']) for g in r['grid']}!=set(paths()) or any(g['zoneid']!='22' or g['type']!='3' or g['type2']!='0' for g in r['grid']):raise ValueError('Walking grid drift')
    if len(r['grid_entries'])!=32 or {(int(p['gridid']),int(p['number'])) for p in r['grid_entries']}!={(i,j) for i in paths() for j in range(1,5)}:raise ValueError('Walking route drift')
    for p in r['grid_entries']:
        if p['zoneid']!='22':raise ValueError('Shared walking grid')
        p.update({k:str(round(v)) if k=='heading' else str(v) for k,v in paths()[int(p['gridid'])][int(p['number'])-1].items()})
    stations={int(o['id']):o for o in r['object'] if int(o['id']) in STATIONS}
    if set(stations)!=set(STATIONS):raise ValueError('Missing crafting station')
    for ident,(label,x,y,h) in STATIONS.items():
        o=stations[ident]
        if o['zoneid']!='22' or o['display_name']!=label:raise ValueError('Station identity drift')
        o.update(xpos=str(x),ypos=str(y),zpos='0',heading=str(h))
    if any(int(d['id']) in CLASS_FIRES or (d['zone']=='ecommons' and int(d['doorid']) in {v[0] for v in CLASS_FIRES.values()}) for d in r['doors']):raise ValueError('Class fire ID/door collision or already installed')
    donors=[d for d in r['doors'] if d['id']=='999606']
    if len(donors)!=1 or any(donors[0][k]!=v for k,v in dict(zone='ecommons',version='0',name='CAMPFIRE',size='65',opentype='58',dest_zone='NONE',pos_x='-274',pos_y='-1707',pos_z='0').items()):raise ValueError('Accepted resident fire drift')
    r['doors']+=fires(donors[0])
    changed=moved(before,after)
    r['zone_state_spawns']=[s for s in r['zone_state_spawns'] if int(s['npc_id']) not in changed]
    return after

FIELDS={'spawn2':{'x','y','z','heading'},'grid_entries':{'x','y','z','heading','pause'},'object':{'xpos','ypos','zpos','heading'}}

def patch_sql(before,after):
    topology(before['rows']);topology(after['rows']);changed=moved(before,after)
    for table,keys in KEYS.items():
        old={tuple(r[k] for k in keys):r for r in before['rows'][table]}
        new={tuple(r[k] for k in keys):r for r in after['rows'][table]}
        if table=='doors':
            donor=old.get(('999606',))
            if not donor or donor!=new.get(('999606',)):raise ValueError('Accepted fire mutation')
            owned={(d['id'],):d for d in fires(donor)}
            a={k:v for k,v in old.items() if int(k[0]) in CLASS_FIRES};b={k:v for k,v in new.items() if int(k[0]) in CLASS_FIRES}
            if not ((not a and b==owned) or (a==owned and not b)):raise ValueError('Unapproved class fire mutation')
            if {k:v for k,v in old.items() if k not in owned}!={k:v for k,v in new.items() if k not in owned}:raise ValueError('Unrelated door mutation')
            continue
        if table=='zone_state_spawns':
            if new.keys()-old.keys() or any(row!=new[k] for k,row in old.items() if k in new):raise ValueError('Never restore/mutate saved states')
            if any(int(row['npc_id']) not in changed for k,row in old.items() if k not in new):raise ValueError('Unchanged NPC cache deletion')
            continue
        if old.keys()!=new.keys():raise ValueError('Unexpected insertion/deletion: '+table)
        for key,row in new.items():
            if {k for k in row if row[k]!=old[key][k]}-FIELDS.get(table,set()):raise ValueError('Unapproved mutation: '+table)
            if table=='object' and row!=old[key] and int(row['id']) not in STATIONS:raise ValueError('Unowned station mutation')
    if not changed<=(set(placements())|set(paths())):raise ValueError('Preserved resident/native movement')
    return content_patch.patch_sql(before,after,KEYS,SCOPES)

def rollback_target(original,current,expected):
    for table in KEYS:
        if table!='zone_state_spawns' and normalize(current['rows'][table])!=normalize(expected['rows'][table]):raise ValueError('Rollback content drift: '+table)
    topology(current['rows']);result=copy.deepcopy(original);changed=moved(original,expected)
    result['rows']['zone_state_spawns']=[s for s in current['rows']['zone_state_spawns'] if int(s['npc_id']) not in changed]
    return result
