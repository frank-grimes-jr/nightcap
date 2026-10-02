"""Scoped follow-up to the installed social tunnel; never applies generated SQL."""
import copy
import json
import content_patch
from pok_hub_migration import read_sql
from tunnel_services import pos, spawn_position
from tunnel_social import safe_states
from tunnel_social_layout import RING as PREVIOUS_RING, RING_CENTER

NAMES = {999520:'Sortre_Blackdragon',999521:'Camil_Swiftwolf',999522:'Rekk_Diver',
         999523:'Nalin_Shadowbane',999524:'Trift',999526:'Glorphyndel'}
RING = {999520:(-286,-1700),999521:(-275,-1693),999522:(-262,-1701),
        999523:(-262,-1714),999524:(-275,-1720),999526:(-287,-1713)}
FIRE_ID, FIRE_DOOR, DONOR = 999606, 211, 1451
IDS = ','.join(map(str,NAMES))
GROUP = f'spawngroupID IN (SELECT spawngroupID FROM spawnentry WHERE npcID IN ({IDS}))'
SCOPES = {
    'npc_types':f'id IN ({IDS})', 'npc_types_tint':f'id IN ({IDS})',
    'spawngroup':f'id IN (SELECT spawngroupID FROM spawnentry WHERE npcID IN ({IDS}))',
    'spawnentry':f'npcID IN ({IDS}) OR {GROUP}', 'spawn2':GROUP,
    'doors':f"id IN ({DONOR},{FIRE_ID}) OR (zone='ecommons' AND doorid={FIRE_DOOR})",
    'items':'id IN (4851,4852,4853,4854,4855,4856,4857,5504,5379,9403)',
    'zone_state_spawns':f'npc_id IN ({IDS}) OR spawngroup_id IN (SELECT spawngroupID FROM spawnentry WHERE npcID IN ({IDS})) OR spawn2_id IN (SELECT id FROM spawn2 WHERE {GROUP})',
}
KEYS = {t:['id'] for t in SCOPES}
KEYS['spawnentry'] = ['spawngroupID','npcID']

def capture(query=read_sql):return content_patch.capture(query,SCOPES)
def positions():return {i:pos(*xy,*RING_CENTER) for i,xy in RING.items()}
def normalized(rows):return sorted(json.dumps(r,sort_keys=True) for r in rows)

def topology(rows):
    npcs = {int(r['id']):r for r in rows['npc_types']}
    if len(rows['npc_types'])!=6 or set(npcs)!=set(NAMES) or any(npcs[i]['name']!=n for i,n in NAMES.items()):
        raise ValueError('Resident identity drift')
    entries=rows['spawnentry']; groups={e['spawngroupID']:int(e['npcID']) for e in entries}
    if len(entries)!=6 or len(groups)!=6 or set(groups.values())!=set(NAMES) or any(e['chance']!='100' for e in entries):
        raise ValueError('Shared resident spawn group/reference')
    if len(rows['spawngroup'])!=6 or {r['id'] for r in rows['spawngroup']}!=set(groups):
        raise ValueError('Resident group drift')
    spawns=rows['spawn2']
    if len(spawns)!=6 or {r['spawngroupID'] for r in spawns}!=set(groups):raise ValueError('Shared resident spawn')
    if any(any(s[k]!=v for k,v in dict(zone='ecommons',version='0',pathgrid='0',animation='0').items()) for s in spawns):
        raise ValueError('Resident zone/path/standing pose drift')
    safe_states(rows['zone_state_spawns'],spawns,entries)
    return npcs,groups

def fire(donor):
    result=dict(donor)
    result.update(id=str(FIRE_ID),doorid=str(FIRE_DOOR),zone='ecommons',pos_x=str(RING_CENTER[0]),
                  pos_y=str(RING_CENTER[1]),pos_z='0',heading='0',size='65')
    return result

def desired(before):
    after=copy.deepcopy(before); rows=after['rows']; npcs,groups=topology(rows)
    for s in rows['spawn2']:
        ident=groups[s['spawngroupID']]
        if any(s[k]!=v for k,v in spawn_position(pos(*PREVIOUS_RING[ident],*RING_CENTER)).items()):
            raise ValueError('Resident position drift or already installed')
        s.update(spawn_position(positions()[ident]))
    if len(rows['doors'])!=1 or rows['doors'][0]['id']!=str(DONOR):raise ValueError('Campfire ID/door collision')
    donor=rows['doors'][0]
    if any(donor[k]!=v for k,v in dict(name='CAMPFIRE',zone='misty',version='0',opentype='58',size='100',dest_zone='NONE',triggerdoor='0').items()):
        raise ValueError('Campfire template drift')
    rows['doors'].append(fire(donor))
    tints={int(r['id']):r for r in rows['npc_types_tint']}
    armor=('texture','helmtexture','armtexture','bracertexture','handtexture','legtexture','feettexture')
    for ident in (999523,999526):
        n=npcs[ident]
        if n['gender']!='0' or n['armortint_id']!=str(ident) or any(n[k]!='3' for k in armor):
            raise ValueError('Valorium costume drift')
        if ident not in tints or any(tints[ident][color+part]!=value for part in ('1h','2c','3a','4b','5g','6l','7f') for color,value in (('red','115'),('grn','135'),('blu','250'))):
            raise ValueError('Valorium color drift')
    if any(npcs[999526][k]!=v for k,v in dict(race='3',d_melee_texture1='42',d_melee_texture2='202').items()):raise ValueError('Glorphyndel appearance drift')
    if any(npcs[999523][k]!=v for k,v in dict(race='5',d_melee_texture1='62',d_melee_texture2='0',prim_melee_type='1').items()):raise ValueError('Nalin appearance drift')
    items={int(r['id']):r for r in rows['items']}
    for ident in range(4851,4858):
        if items[ident]['material']!='3' or items[ident]['color']!='4285761530':raise ValueError('Valorium item visual drift')
    for ident,model,kind in ((5504,'IT62','1'),(5379,'IT42','0'),(9403,'IT202','8')):
        if items[ident]['idfile']!=model or items[ident]['itemtype']!=kind:raise ValueError('Weapon item visual drift')
    npcs[999526]['race']='5'  # High Elf; race 3 is Erudite.
    npcs[999523]['prim_melee_type']='3'  # SoulFire: Skill2HSlashing; display model is unchanged.
    rows['zone_state_spawns']=[]
    return after

def patch_sql(before,after):
    topology(before['rows']);topology(after['rows'])
    for table,keys in KEYS.items():
        old={tuple(r[k] for k in keys):r for r in before['rows'][table]}
        new={tuple(r[k] for k in keys):r for r in after['rows'][table]}
        if table=='zone_state_spawns':
            if new:raise ValueError('Never restore saved states')
            continue
        if table=='doors':
            donor=old.get((str(DONOR),))
            if not donor or new.get((str(DONOR),))!=donor:raise ValueError('Donor mutation')
            a={k:v for k,v in old.items() if k!=(str(DONOR),)}
            b={k:v for k,v in new.items() if k!=(str(DONOR),)}
            own={(str(FIRE_ID),):fire(donor)}
            if not ((a=={} and b==own) or (a==own and b=={})):raise ValueError('Unexpected fire mutation')
            continue
        if old.keys()!=new.keys():raise ValueError('Unexpected row insertion/deletion: '+table)
        for key,row in old.items():
            changed={k for k,v in row.items() if new[key][k]!=v}
            allowed={'x','y','z','heading'} if table=='spawn2' else set()
            if table=='npc_types':allowed={'race'} if key==('999526',) else {'prim_melee_type'} if key==('999523',) else set()
            if changed-allowed:raise ValueError('Unapproved mutation: '+table)
    return content_patch.patch_sql(before,after,KEYS,SCOPES)

def rollback_target(original,current,expected):
    for table in KEYS:
        if table!='zone_state_spawns' and normalized(current['rows'][table])!=normalized(expected['rows'][table]):
            raise ValueError('Rollback content drift: '+table)
    topology(current['rows'])
    result=copy.deepcopy(original);result['rows']['zone_state_spawns']=[]
    return result
