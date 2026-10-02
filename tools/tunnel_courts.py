"""Plan readable tunnel courts and generate guarded content-only migrations.

Never applies SQL. Capture a stopped target before deployment; a live read-only
capture is suitable for rehearsal only. Stock, player data and rules are untouched.
"""
import argparse
import copy
import json
import re
import content_patch
from pathlib import Path
from pok_hub_migration import read_sql
from tunnel_services import spawn_position

ROOT=Path(__file__).resolve().parents[1]
KHALEID=999527
CLASSES=['Warrior','Cleric','Paladin','Ranger','Shadow Knight','Druid','Monk','Bard',
         'Rogue','Shaman','Necromancer','Wizard','Magician','Enchanter','Beastlord','Berserker']
# race, armor material, RGB, size: recognizable Classic playable races, not a
# claim of measured player popularity. Gender never changes a school's uniform.
CLASS_STYLES={
    1:(2,3,0x8999AB,6.5), 2:(5,3,0xDDD5BC,6), 3:(1,3,0xC5A35D,6),
    4:(4,2,0x51794D,5), 5:(6,3,0x55536F,5), 6:(4,1,0x79915A,5),
    7:(1,1,0xBCA277,6), 8:(7,3,0x973F54,5.5), 9:(11,2,0x626B70,3.5),
    10:(2,2,0x548B8B,6.5), 11:(3,11,0x765582,6), 12:(6,15,0xAF0A32,5),
    13:(12,10,0x668DC0,3), 14:(5,12,0x9565AC,6),
    15:(2,1,0x99734E,6.5), 16:(2,2,0xA05343,6.5),
}
# Two adjacent class pairs per court. Orientation follows the wall; small gaps
# between courts leave a usable frontage and a clear central circulation area.
COURTS=[
    ('Steel', (1,16), -387,-1766,128),
    ('Discipline',(7,9),-360,-1637,128),
    ('Light',(2,3),-203,-1517,256),
    ('Shadow',(5,11),-33,-1588,384),
    ('Arcane',(12,13),-23,-1684,384),
    ('Song and Illusion',(14,8),-9,-1778,384),
    ('Wilds',(4,6),-208,-1860,0),
    ('Spirits',(10,15),-150,-1826,0),
]
SUPPLIES={
    'Smithing':(8,3,0x8C8073,4), 'Pottery':(1,1,0xA88767,6),
    'Baking':(11,1,0xD3BA8D,3.5), 'Brewing':(8,1,0x997144,4),
    'Tailoring':(4,1,0x739087,5), 'Jewelcrafting':(5,12,0xAB8C60,6),
    'Fletching':(4,2,0x647E51,5), 'Tinkering':(12,1,0x9A805B,3),
    'Alchemy':(2,1,0x668A80,6.5), 'Poison':(6,2,0x66606E,5),
    'Research':(3,12,0x6E799F,6), 'Fishing':(1,1,0x789196,6),
}
TRADE_POSITIONS={
    999601:(-375,-1800,64),999602:(-359,-1814,64),999603:(-343,-1828,64),
    999604:(-315,-1851,0),999605:(-94,-1820,0),999606:(-78,-1820,0),
    999607:(-54,-1795,384),999608:(-362,-1565,256),999609:(-369,-1600,128),
    999610:(-201,-1825,0),999611:(-18,-1735,384),
    999612:(-23,-1623,384),999613:(-23,-1641,384),
    999614:(-3,-1623,384),999615:(-3,-1641,384),
    999616:(-397,-1699,128),999617:(-397,-1717,128),
    999618:(-89,-1537,320),999619:(-71,-1550,320),999620:(-53,-1563,320),
    999621:(-53,-1735,384),
}
IDS=set(range(997900,997916))|set(range(999650,999666))|set(range(999600,999622))|{999525,999527,999225}
ID_SQL=','.join(map(str,sorted(IDS)))
KEYS={'npc_types':['id'],'npc_types_tint':['id'],'spawngroup':['id'],
      'spawnentry':['spawngroupID','npcID'],'spawn2':['id'],'zone_state_spawns':['id']}
SCOPES={
    'npc_types':f"id IN ({ID_SQL}) OR name='Khaleid'",
    'npc_types_tint':f'id={KHALEID}',
    'spawngroup':f"id IN ({ID_SQL}) OR name='NightcapKhaleid'",
    'spawnentry':f'spawngroupID IN ({ID_SQL}) OR npcID IN ({ID_SQL})',
    'spawn2':f'id IN ({ID_SQL}) OR spawngroupID IN ({ID_SQL})',
    'zone_state_spawns':f'npc_id IN ({ID_SQL}) OR spawngroup_id IN ({ID_SQL}) OR spawn2_id IN ({ID_SQL})',
}

def class_members():return {c:(999649+c,997899+c) for c in range(1,17)}

def roman_title(title):
    match=re.search(r' (\d+)$',title)
    if not match:return title
    n=int(match[1])
    if not 1<=n<=39:raise ValueError('Unsupported merchant page')
    suffix=''
    for value,token in [(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')]:
        count,n=divmod(n,value);suffix+=token*count
    return title[:match.start()]+' '+suffix

def appearance(style,gender):
    race,material,color,size=style
    return dict(race=race,gender=gender,size=size,texture=material,helmtexture=0,
        armtexture=material if material<4 else 0,bracertexture=material if material<4 else 0,
        handtexture=material if material<4 else 0,legtexture=material if material<4 else 0,
        feettexture=material if material<4 else 0,armortint_id=0,npc_tint_id=0,
        armortint_red=(color>>16)&255,armortint_green=(color>>8)&255,armortint_blue=color&255,
        d_melee_texture1=0,d_melee_texture2=0,herosforgemodel=0,model=0,face=0,
        luclin_hairstyle=0,luclin_haircolor=0,luclin_beard=0,luclin_beardcolor=0,
        luclin_eyecolor=0,luclin_eyecolor2=0,drakkin_heritage=0,drakkin_tattoo=0,drakkin_details=0)

def placements():
    result={}
    for name,classes,x,y,heading in COURTS:
        for offset,ident in zip((-26,-10,10,26),[i for c in classes for i in class_members()[c]]):
            result[ident]=dict(x=x+offset if heading in (0,256) else x,
                              y=y if heading in (0,256) else y+offset,z=3.75,heading=heading)
    result.update({i:dict(x=x,y=y,z=3.75,heading=h) for i,(x,y,h) in TRADE_POSITIONS.items()})
    result[999525]=dict(x=-311,y=-1561,z=3.75,heading=256)
    result[KHALEID]=dict(x=-279,y=-1567,z=3.75,heading=256)
    return result

def capture(query=read_sql):return content_patch.capture(query,SCOPES)

def safe_states(rows,spawns):
    topology={int(s['id']):int(s['spawngroupID']) for s in spawns}
    for row in rows:
        ids=[int(row[k]) for k in ('npc_id','spawngroup_id','spawn2_id')]
        if not (ids[0] in IDS and ids[0]==ids[1] and topology.get(ids[2])==ids[0] and all(row[k]==v for k,v in
            dict(zone_id='22',instance_id='0',is_corpse='0',is_zone='0').items())):
            raise ValueError('Ambiguous saved state: preserve and investigate')

def desired(before):
    out=copy.deepcopy(before);rows=out['rows'];expected=IDS-{KHALEID}
    if {int(n['id']) for n in rows['npc_types']}!=expected or len(rows['npc_types'])!=len(expected):
        raise ValueError('Missing court roster or Khaleid identity/name collision')
    if any(n['name'].lower()=='khaleid' for n in rows['npc_types']):
        raise ValueError('Khaleid name already used')
    if rows['npc_types_tint']:raise ValueError('Khaleid tint collision')
    for table,key in [('spawn2','spawngroupID'),('spawngroup','id'),('spawnentry','npcID')]:
        if {int(r[key]) for r in rows[table]}!=expected or len(rows[table])!=len(expected):
            raise ValueError('Shared or missing spawn topology: '+table)
    if any(r['name'].lower()=='nightcapkhaleid' for r in rows['spawngroup']):
        raise ValueError('Khaleid group name already used')
    for s in rows['spawn2']:
        if (s['id']!=s['spawngroupID'] and (s['id'],s['spawngroupID'])!=('3266027','999225')) or s['zone']!='ecommons' or s['version']!='0' or s['pathgrid']!='0':
            raise ValueError('Unexpected court placement')
    for e in rows['spawnentry']:
        if e['spawngroupID']!=e['npcID'] or e['chance']!='100':raise ValueError('Shared court spawn entry')
    safe_states(rows['zone_state_spawns'],rows['spawn2'])
    npcs={int(n['id']):n for n in rows['npc_types']}
    def update(ident,changes):npcs[ident].update({k:str(v) for k,v in changes.items()})
    for cls,(trainer,merchant) in class_members().items():
        if npcs[trainer]['class']!=str(cls+19) or npcs[merchant]['class']!='41':
            raise ValueError('Trainer or merchant function changed')
        for ident,gender in [(trainer,0),(merchant,1)]:
            update(ident,appearance(CLASS_STYLES[cls],gender))
    for ident in range(999600,999622):
        npc=npcs[ident]
        if npc['class']!='41':raise ValueError('Supply merchant function changed')
        npc['lastname']=roman_title(npc['lastname'])
        skill=npc['lastname'].split(' Supplies')[0]
        style=SUPPLIES.get(skill,(1,1,0x9C927C,6))
        update(ident,appearance(style,ident%2))
    update(999225,appearance((11,1,0x917957,3.5),0))
    update(999525,dict(lastname='Druid Rings'))
    # Display-only Classic Carmine Robe (1226) and Blue Crystal Staff (14337).
    # No loot/equipped item instance is created, so these cannot enter the economy.
    npc=copy.deepcopy(npcs[999525]);npc.update({k:str(v) for k,v in appearance((6,15,0xAF0A32,5),0).items()})
    npc.update(id=str(KHALEID),name='Khaleid',lastname='Wizard Spires',**{'class':'12'},
        level='50',maxlevel='50',d_melee_texture1='122',prim_melee_type='0',loottable_id='0',
        merchant_id='0',npc_spells_id='0',npc_spells_effects_id='0',skip_global_loot='1')
    rows['npc_types'].append(npc)
    for table,key in [('spawngroup','id'),('spawnentry','npcID'),('spawn2','id')]:
        row=copy.deepcopy(next(r for r in rows[table] if r[key]=='999525'))
        for field in KEYS[table]:row[field]=str(KHALEID)
        if 'spawngroupID' in row:row['spawngroupID']=str(KHALEID)
        if table=='spawngroup':row['name']='NightcapKhaleid'
        rows[table].append(row)
    positions=placements()
    for s in rows['spawn2']:
        if int(s['id']) in positions:s.update(spawn_position(positions[int(s['id'])]))
    rows['zone_state_spawns']=[]
    return out

def indexed(table,row):return content_patch.indexed(table,row,KEYS)

def patch_sql(before,after):return content_patch.patch_sql(before,after,KEYS,SCOPES)

def rollback_target(original,current,expected):
    for table in KEYS:
        if table=='zone_state_spawns':continue
        order=lambda r:tuple(r[k] for k in KEYS[table])
        if sorted(current['rows'][table],key=order)!=sorted(expected['rows'][table],key=order):
            raise ValueError('Rollback content drift: '+table)
    safe_states(current['rows']['zone_state_spawns'],current['rows']['spawn2'])
    result=copy.deepcopy(original);result['rows']['zone_state_spawns']=[]
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path);parser.add_argument('--capture',action='store_true')
    parser.add_argument('--rollback-from',type=Path,help='Original generation directory; source/capture must be current stopped-target content')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if bool(args.source)==bool(args.capture):parser.error('Choose exactly one of --source or --capture')
    if args.output.exists():raise ValueError('Choose a new output directory')
    before=capture() if args.capture else json.loads(args.source.read_bytes())
    if args.rollback_from:
        original=json.loads((args.rollback_from/'before.json').read_bytes())
        expected=json.loads((args.rollback_from/'after.json').read_bytes())
        after=rollback_target(original,before,expected)
    else:after=desired(before)
    args.output.mkdir(parents=True)
    for name,data in [('before',before),('after',after)]:
        (args.output/(name+'.json')).write_text(json.dumps(data),encoding='utf-8')
    (args.output/'forward.sql').write_text(patch_sql(before,after),encoding='utf-8')
    (args.output/'rollback.sql').write_text(patch_sql(after,before),encoding='utf-8')
    print(json.dumps(dict(npcs=len(after['rows']['npc_types']),class_courts=len(COURTS),status='generated_not_applied')))

if __name__=='__main__':main()
