"""Generate additive, guarded tunnel residents and a reviewed druid-ring catalog."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from generate_living_economy import guard, insert, rows
from pok_hub_migration import read_sql, sql_value, predicate

ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'docs/economy/residents'
RESIDENTS=[
    dict(id=999520,name='Sortre_Blackdragon',race=6,**{'class':1},level=50,template=22108,
         armor=[4173,4174,4176,4177,4178,4179,4180],weapons=[5500,5500],x=-340,y=-1645),
    dict(id=999521,name='Camil_Swiftwolf',race=5,**{'class':3},level=50,template=22116,
         armor=[3150,3151,3152,3153,3154,3155,3156],weapons=[5403,9004],x=-275,y=-1695),
    dict(id=999522,name='Rekk_Diver',race=11,**{'class':9},level=50,template=22014,
         armor=[0]*7,weapons=[7001,7001],black_chain=True,x=-185,y=-1645),
    dict(id=999523,name='Nalin_Shadowbane',race=5,**{'class':3},level=50,template=22116,
         armor=[4851,4852,4853,4854,4855,4856,4857],weapons=[5504,0],x=-115,y=-1695),
    dict(id=999524,name='Trift',race=1,**{'class':1},level=12,template=22033,
         armor=[4201,4204,4208,4209,4210,4211,4212],weapons=[0,0],x=-335,y=-1760),
    dict(id=999525,name='Khalure_Ser`Tiras',race=4,**{'class':6},level=50,template=22086,
         armor=[2001,2004,2008,2009,2010,2011,4407],weapons=[0,0],x=-55,y=-1750),
]

# P1999 coordinates are Y,X,Z; these fields deliberately use world X,Y,Z.
# Classic overrides avoid PEQ's replacement-zone ports. Later destinations are
# explicit and gated, not discovered from widened spell class columns at runtime.
RINGS=[
    dict(zone='northkarana',label='North Karana',era=0,spell=550,x=-1494,y=-2706,z=-4),
    dict(zone='commons',label='West Commonlands',era=0,spell=551,x=1427,y=478,z=-48),
    dict(zone='tox',label='Toxxulia Forest',era=0,spell=552,x=-357,y=1099,z=-53),
    dict(zone='butcher',label='Butcherblock Mountains',era=0,spell=553,x=1984,y=-2135,z=3),
    dict(zone='lavastorm',label='Lavastorm Mountains',era=0,spell=554,x=1389,y=1014,z=131),
    dict(zone='sro',label='South Ro',era=0,spell=555,x=317,y=-2034,z=-19),
    dict(zone='feerrott',label='The Feerrott',era=0,spell=556,x=-1885,y=367,z=16),
    dict(zone='steamfont',label='Steamfont Mountains',era=0,spell=557,x=1668,y=-1779,z=-104),
    dict(zone='misty',label='Misty Thicket',era=0,spell=558,x=-1896,y=-490,z=120),
    dict(zone='dreadlands',label='Dreadlands',era=1,spell=1517,x=7717,y=2484,z=1051),
    dict(zone='iceclad',label='Iceclad Ocean',era=2,spell=1434,x=4925,y=-630,z=113),
    dict(zone='greatdivide',label='Great Divide',era=2,spell=1438,x=3651,y=-3766,z=-237),
    dict(zone='wakening',label='Wakening Lands',era=2,spell=1398,x=-3032,y=-3040,z=28),
    dict(zone='cobaltscar',label='Cobalt Scar',era=2,spell=1440,x=-1634,y=-1065,z=299),
    dict(zone='qrg',label='Surefall Glade',era=2,spell=2020,x=-391,y=-209,z=9),
    dict(zone='grimling',label='Grimling Forest',era=3,spell=2419,x=-1170,y=-690,z=13),
    dict(zone='twilight',label='Twilight Sea',era=3,spell=2424,x=-125,y=-656,z=-22),
    dict(zone='dawnshroud',label='Dawnshroud Peaks',era=3,spell=2429,x=-996,y=325,z=121),
    dict(zone='nexus',label='The Nexus',era=3,spell=2432,x=0,y=0,z=-28),
]


def validate(residents,rings):
    if len({r['id'] for r in residents})!=len(residents) or len({r['name'] for r in residents})!=len(residents):
        raise ValueError('Duplicate resident identity')
    if len({r['zone'] for r in rings})!=len(rings) or any(not 0<=r['era']<=30 for r in rings):
        raise ValueError('Invalid ring catalog')
    if any(len(r['armor'])!=7 or len(r['weapons'])!=2 for r in residents):
        raise ValueError('Incomplete visible equipment')


def visual_rows(resident,items):
    r=resident
    npc=dict(id=r['id'],name=r['name'],lastname='',race=r['race'],**{'class':r['class']},level=r['level'],
        maxlevel=r['level'],gender=0,hp=100000,mana=0,loottable_id=0,merchant_id=0,alt_currency_id=0,
        npc_spells_id=0,npc_spells_effects_id=0,npc_faction_id=0,adventure_template_id=0,trap_template=0,
        special_abilities='19,1^20,1^24,1^35,1',npcspecialattks='',aggroradius=0,assistradius=0,
        npc_aggro=0,always_aggro=0,raid_target=0,spawn_limit=1,findable=1,emoteid=0,
        private_corpse=0,isquest=1,skip_global_loot=1,keeps_sold_items=0,is_parcel_merchant=0,
        multiquest_enabled=0,qglobal=0,unique_spawn_by_name=1,herosforgemodel=0,model=0,
        armortint_id=r['id'],armortint_red=0,armortint_green=0,armortint_blue=0,npc_tint_id=0)
    tint=dict(id=r['id'],tint_set_name='NightcapResident'+str(r['id']))
    fields=['helmtexture','texture','armtexture','bracertexture','handtexture','legtexture','feettexture']
    for index,(item_id,field,suffix) in enumerate(zip(r['armor'],fields,['1h','2c','3a','4b','5g','6l','7f'])):
        black=r.get('black_chain',False)
        npc[field]=2 if black else items[item_id]['material']
        color=0x0C0C0C if black else items[item_id]['color'] & 0xFFFFFF
        for prefix,shift in [('red',16),('grn',8),('blu',0)]:tint[prefix+suffix]=(color>>shift)&255
    for index,item_id in enumerate(r['weapons'],1):
        model=items[item_id]['idfile'] if item_id else 'IT0'
        if not re.fullmatch(r'IT\d+',model):raise ValueError('Unsupported weapon model')
        npc['d_melee_texture'+str(index)]=int(model[2:])
    npc.update(prim_melee_type=36 if r['class']==9 else 1,sec_melee_type=36 if r['class']==9 else 1)
    return npc,tint


def block(statements):
    return ('DELIMITER //\nBEGIN NOT ATOMIC\nDECLARE n BIGINT;\n'
            'DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;\nSTART TRANSACTION;\n'+
            '\n'.join(statements)+'\nCOMMIT;\nEND //\nDELIMITER ;\n')


def generate(refresh=False):
    validate(RESIDENTS,RINGS)
    if OUTPUT.exists() and not refresh:raise ValueError('Use --refresh for the owned generated package')
    fields=[line.split('\t')[0] for line in read_sql('SHOW COLUMNS FROM npc_types;').splitlines()]
    templates=rows('SELECT JSON_OBJECT('+','.join(sql_value(c)+',`'+c+'`' for c in fields)+
        ') FROM npc_types WHERE id IN('+','.join(str(r['template']) for r in RESIDENTS)+');')
    templates={r['id']:r for r in templates}
    ids=sorted({i for r in RESIDENTS for i in r['armor']+r['weapons'] if i})
    items=rows("SELECT JSON_OBJECT('id',id,'name',Name,'material',material,'color',color,'idfile',idfile,'slots',slots) "
               'FROM items WHERE id IN('+','.join(map(str,ids))+');')
    items={r['id']:r for r in items}
    if set(items)!=set(ids):raise ValueError('Missing appearance item')
    scopes={'npc_types':'id','npc_types_tint':'id','spawngroup':'id',
            'spawnentry':'spawngroupID','spawn2':'id'}
    collisions=[f'SELECT COUNT(*) FROM {table} WHERE {key} BETWEEN 999520 AND 999525'
                for table,key in scopes.items()]
    collisions+=['SELECT COUNT(*) FROM spawnentry WHERE npcID BETWEEN 999520 AND 999525',
        'SELECT COUNT(*) FROM npc_types WHERE armortint_id BETWEEN 999520 AND 999525',
        'SELECT COUNT(*) FROM spawn2 WHERE spawngroupID BETWEEN 999520 AND 999525',
        'SELECT COUNT(*) FROM zone_state_spawns WHERE npc_id BETWEEN 999520 AND 999525 '
        'OR spawngroup_id BETWEEN 999520 AND 999525 OR spawn2_id BETWEEN 999520 AND 999525',
        "SELECT COUNT(*) FROM npc_types WHERE name IN("+','.join(sql_value(r['name']) for r in RESIDENTS)+')']
    for query in collisions:
        if read_sql(query+';').strip()!='0':raise ValueError('Resident identity collision: '+query)
    tables=','.join(sql_value(t) for t in [*scopes,'zone_state_spawns'])
    engines=guard(f"SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME IN({tables}) AND ENGINE='InnoDB'",6,'Transactional resident tables required')
    triggers=guard(f'SELECT COUNT(*) FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() AND EVENT_OBJECT_TABLE IN({tables})',0,'Unexpected resident trigger')
    coordinates=guard("SELECT COUNT(*) FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='spawn2' AND COLUMN_NAME IN('x','y','z','heading') AND COLUMN_TYPE='float(14,6)'",4,'Spawn coordinate format changed')
    forward=[engines,triggers,coordinates]+[guard(q+' FOR UPDATE',0,'Resident identity collision') for q in collisions]
    for item in items.values():
        forward.append(guard('SELECT COUNT(*) FROM items WHERE '+predicate({k:v for k,v in item.items() if k!='name'}),1,'Appearance item changed'))
    rollback=[engines,triggers,coordinates]
    after={t:[] for t in scopes}
    for r in RESIDENTS:
        template=templates[r['template']]
        if template['race']!=r['race'] or template['gender']!=0:raise ValueError('Race template mismatch')
        npc,tint=visual_rows(r,items)
        npc={**template,**npc}
        bundle={'npc_types':npc,'npc_types_tint':tint,'spawngroup':dict(id=r['id'],name='NightcapResident'+str(r['id'])),
            'spawnentry':dict(spawngroupID=r['id'],npcID=r['id'],chance=100),
            'spawn2':dict(id=r['id'],spawngroupID=r['id'],zone='ecommons',version=0,
                x=f"{r['x']:.6f}",y=f"{r['y']:.6f}",z='3.750000',heading='128.000000',
                respawntime=60,variance=0,pathgrid=0,min_expansion=0,max_expansion=-1)}
        for table,row in bundle.items():
            forward.append(insert(table,row));after[table].append(row)
            rollback.append(guard(f'SELECT COUNT(*) FROM {table} WHERE '+predicate(row),1,'Resident row changed'))
    rollback += [guard('SELECT COUNT(*) FROM npc_types WHERE armortint_id BETWEEN 999520 AND 999525',6,'Extra tint reference'),
        guard('SELECT COUNT(*) FROM spawnentry WHERE spawngroupID BETWEEN 999520 AND 999525 OR npcID BETWEEN 999520 AND 999525',6,'Extra spawn reference'),
        guard('SELECT COUNT(*) FROM spawn2 WHERE spawngroupID BETWEEN 999520 AND 999525',6,'Extra placement'),
        'DELETE FROM zone_state_spawns WHERE zone_id=22 AND instance_id=0 AND is_corpse=0 AND is_zone=0 '
        'AND (npc_id BETWEEN 999520 AND 999525 OR spawngroup_id BETWEEN 999520 AND 999525 OR spawn2_id BETWEEN 999520 AND 999525);']
    rollback += [f'DELETE FROM {t} WHERE {k} BETWEEN 999520 AND 999525;' for t,k in reversed(list(scopes.items()))]
    rings=[]
    for ring in RINGS:
        matches=rows("SELECT JSON_OBJECT('zone_id',zoneidnumber,'zone_expansion',expansion,'min_status',min_status,'min_level',min_level,'map_file',COALESCE(NULLIF(map_file_name,''),short_name)) "
                     'FROM zone WHERE version=0 AND short_name='+sql_value(ring['zone'])+';')
        if len(matches)!=1 or matches[0]['zone_expansion']>ring['era'] or matches[0]['min_status']:
            raise ValueError('Unreviewed ring zone gate: '+ring['zone'])
        rings.append({**ring,**matches[0],'heading':0})
    OUTPUT.mkdir(parents=True,exist_ok=refresh)
    (OUTPUT/'forward.sql').write_text(block(forward))
    (OUTPUT/'rollback.sql').write_text(block(rollback))
    (OUTPUT/'source.json').write_text(json.dumps(dict(captured_at=datetime.now(timezone.utc).isoformat(),
        items=items,templates=templates,after=after),indent=2)+'\n')
    (OUTPUT/'rings.json').write_text(json.dumps(rings,indent=2)+'\n')
    (OUTPUT/'placement.json').write_text(json.dumps(RESIDENTS,indent=2)+'\n')
    (OUTPUT/'probe-input.json').write_text(json.dumps(dict(map='/home/eqemu/server/maps/base/ecommons.map',
        points=[dict(label=r['name'],x=r['x'],y=r['y'],z=3.75) for r in RESIDENTS]),indent=2)+'\n')
    for ring in rings:
        (OUTPUT/('probe-'+ring['zone']+'.json')).write_text(json.dumps(dict(map='/home/eqemu/server/maps/base/'+ring['map_file']+'.map',
            points=[dict(label=ring['label'],**{k:ring[k] for k in ('x','y','z')})]))+'\n')
    # Generated immutable data is loaded by the standard plugin loader.
    def perl(v):return str(v) if isinstance(v,(int,float)) else "'"+v.replace('\\','\\\\').replace("'","\\'")+"'"
    data='use strict;\nuse warnings;\nsub tunnel_ring_catalog { return [\n'
    data+='\n'.join('    {'+', '.join(k+' => '+perl(v) for k,v in r.items())+'},' for r in rings)
    data+='\n]; }\n1;\n'
    (ROOT/'server-mods/plugins/tunnel_resident_data.pl').write_text(data)
    print(json.dumps(dict(status='generated_not_applied',residents=6,rings=len(rings),classic_rings=9)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--refresh',action='store_true');generate(p.parse_args().refresh)
