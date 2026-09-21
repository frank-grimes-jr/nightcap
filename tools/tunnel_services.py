"""Plan tunnel services and generate guarded content SQL; never applies it."""
import argparse
import copy
import json
import math
import struct
from pathlib import Path
from pok_hub_migration import predicate, sql_value
from generate_living_economy import insert

ROOT = Path(__file__).resolve().parents[1]
CLASSES = ['Warrior','Cleric','Paladin','Ranger','Shadow Knight','Druid','Monk','Bard',
           'Rogue','Shaman','Necromancer','Wizard','Magician','Enchanter','Beastlord','Berserker']
STATS = ['astr','awis','astr','astr','aint','awis','astr','adex','adex','awis','aint','aint','aint','aint','awis','astr']
TRAINERS = ['Garran','Elowen','Aldric','Maren','Veyra','Thalen','Joren','Liora',
            'Silas','Korra','Velis','Orwen','Mirel','Sarina','Torren','Brakka']
TRADE_SKILLS = ['Smithing','Pottery','Baking','Brewing','Tailoring','Jewelcrafting',
                'Fletching','Tinkering','Alchemy','Poison','Research','Fishing']
PORTABLE = {'Baking':17906, 'Tailoring':17880, 'Jewelcrafting':17912, 'Fletching':17910,
            'Tinkering':17902, 'Alchemy':17901, 'Poison':17904, 'Research':17903, 'Fishing':17048}
# Plains Pebble is a foraged reagent with no baseline vendor price. Its base price
# becomes 100 copper; native SellRate/CHA/faction still determine the shop quote.
REAGENT_PRICES = {12832:100}
KEYS = {'npc_types':['id'], 'spawngroup':['id'], 'spawnentry':['spawngroupID','npcID'],
        'spawn2':['id'], 'merchantlist':['merchantid','slot'], 'object':['id'],
        'grid':['id','zoneid'], 'grid_entries':['gridid','zoneid','number'],
        'items':['id'], 'nightcap_market_actors':['npc_id'], 'zone_state_spawns':['id']}


def indexed_predicate(table, row):
    key = ' AND '.join(f'`{column}` <=> {sql_value(row[column])}' for column in KEYS[table])
    return key + ' AND ' + predicate(row)


def pos(x, y, face_x=None, face_y=None):
    heading = 128 if face_x is None else math.atan2(face_x-x, face_y-y)*256/math.pi % 512
    return dict(x=x, y=y, z=3.75, heading=round(heading, 5))


def stock_catalog(source):
    items = {int(i['id']):i for i in source['items']}
    reagents = sorted({int(s[f'components{i}']) for s in source['spells'] for i in range(1,5)
                       if int(s[f'components{i}']) > 0})
    if any(i not in items for i in reagents):
        raise ValueError('Missing spell component')
    # The baseline hub's approved spell pool owns access, including non-consumed
    # components and Bard instruments. Never interpret instrument category IDs as items.
    general = sorted(set(reagents) | {13005,13006,13009,13000,13001,13011,13012})
    if any(i not in items or REAGENT_PRICES.get(i,int(items[i]['price']))<=0 for i in general):
        raise ValueError('Unpriced spell component or general supply requires review')
    merchants = {m['merchant_id']:m['lastname'].removesuffix(' Supplies') for m in source['merchants']}
    catalog = {skill:set() for skill in TRADE_SKILLS}
    for row in source['stock']:
        skill = merchants.get(row['merchantid'])
        if skill not in catalog:
            continue
        if int(row['min_expansion'])>0:
            continue
        # Copy ordinary always-available vendor stock, not gated quest purchases.
        if int(row['min_status']) or int(row['level_required'])>1 or row['bucket_name'] or int(row['alt_currency_cost']):
            continue
        if row['content_flags'] or row['content_flags_disabled']:
            continue
        catalog[skill].add(int(row['item']))
    for skill,item in PORTABLE.items():
        if item not in catalog[skill]:
            raise ValueError(f'{skill} portable container missing: {item}')
    return dict(reagents=reagents, general=general, price_overrides=REAGENT_PRICES,
                tradeskills={k:sorted(v) for k,v in catalog.items()})


def starter_items(source):
    items = {int(i['id']):i for i in source['items']}
    result=[]
    for cls, (name,stat) in enumerate(zip(CLASSES,STATS),1):
        robe=copy.deepcopy(items[1060])
        robe.update(id=str(998599+cls), Name=f'Initiate {name} Robe', ac='10', classes=str(1<<(cls-1)),
                    races='65535', deity='0', nodrop='0', price='0', reqlevel='0', reclevel='0', weight='10')
        robe[stat]='5'
        # All weapon types are native skills for their primary class; use a club
        # for Monks/Beastlords, a two-handed slashing template for Berserkers.
        template=5023 if cls==16 else 9998 if cls in (1,3,4,5,8) else 9999 if cls in (2,6,7,10,15) else 9997
        weapon=copy.deepcopy(items[template])
        damage,delay=(11,45) if cls==16 else (6,28) if template==9998 else (6,30) if template==9999 else (5,24)
        weapon.update(id=str(998619+cls), Name=f'Initiate {name} '+('Greatsword' if cls==16 else 'Blade' if template==9998 else 'Club' if template==9999 else 'Dagger'),
                      classes=str(1<<(cls-1)), races='65535', deity='0', damage=str(damage), delay=str(delay),
                      nodrop='0', price='0', slots='8192', reqlevel='0', reclevel='0', weight='10')
        result.extend((robe,weapon))
    return result


def plan(source):
    stock=stock_catalog(source)
    npcs=[]; relocations={}; stations=[]; paths={}
    # Each small school has four irregular pairs facing into shared conversation.
    clusters=[((-337,-1680),(1,7,9,16)),((-245,-1565),(2,3,5,10)),
              ((-240,-1780),(4,6,8,15)),((-72,-1595),(11,12,13,14))]
    offsets=[ [(-25,-16),(-5,22),(26,9),(11,-29)],
              [(-22,-12),(-8,19),(29,4),(8,-25)],
              [(-28,-15),(0,20),(24,12),(9,-30)],
              [(-19,-17),(-6,25),(27,8),(8,-27)] ]
    for group,((cx,cy),classes) in enumerate(clusters):
        for index,cls in enumerate(classes):
            dx,dy=offsets[group][index]; x,y=cx+dx,cy+dy
            relocations[997899+cls]=pos(x,y,cx,cy)
            npcs.append(dict(id=999649+cls,name=TRAINERS[cls-1],title=CLASSES[cls-1]+' Trainer',
                             role='trainer',class_id=cls+19,position=pos(x+10,y-7,cx,cy)))
    utility=[(999220,-210,-1655),(999225,-160,-1690),(999226,-305,-1800),
             (999237,-197,-1584),(999238,-180,-1570),(999239,-115,-1535)]
    for ident,x,y in utility:relocations[ident]=pos(x,y,x+15,y-10)
    npcs.append(dict(id=999600,name='Tessa',title='Food and Spell Components',role='merchant',
                     stock=stock['general'],position=pos(-153,-1710,-170,-1700)))
    # Tradeskill neighbors share six functioning fixed stations. Each page has a
    # separate merchant so no RoF2 merchant inventory silently truncates the stock.
    anchors={'Smithing':(-360,-1802),'Pottery':(-310,-1840),'Baking':(-100,-1835),
        'Brewing':(-54,-1795),'Tailoring':(-357,-1560),'Jewelcrafting':(-340,-1590),
        'Fletching':(-195,-1825),'Tinkering':(-29,-1710),'Alchemy':(-45,-1657),
        'Poison':(-392,-1714),'Research':(-133,-1587),'Fishing':(-69,-1744)}
    names=[['Berrin','Torvik','Haldra','Kerrik'],['Pella','Uma','Tilda','Kel'],
           ['Odel','Mara','Tobin','Fala'],['Fenna','Urris','Brellin','Ona'],
           ['Aven','Sella','Rani','Tess'],['Della','Gemrin','Ora','Kess'],
           ['Corin','Falen','Selva','Garth'],['Nelli','Cogrin','Pip','Binna'],
           ['Yara','Fenrik','Mosslin','Usha'],['Rusk','Vessa','Kellar','Nera'],
           ['Ilyen','Meris','Davin','Oryn'],['Finn','Willa','Tarn','Bessa']]
    ident=999601
    for index,skill in enumerate(TRADE_SKILLS):
        x,y=anchors[skill]; inventory=stock['tradeskills'][skill]
        for page,start in enumerate(range(0,len(inventory),150)):
            npcs.append(dict(id=ident,name=names[index][page],
                title=skill+' Supplies'+(f' {page+1}' if len(inventory)>150 else ''),role='merchant',
                skill=skill,stock=inventory[start:start+150],position=pos(x+page*10,y+(page%2)*13,x+15,y+8)))
            ident+=1
    if ident>999640:raise ValueError('Merchant ID reservation exhausted')
    for index,(obj_id,label,x,y) in enumerate([(103173,'Loom',-379,-1575),(103174,'Oven',-116,-1817),
        (103175,'Forge',-372,-1822),(103180,'Brewing Barrel',-32,-1812),
        (103183,'Pottery Wheel',-326,-1857),(103187,'Kiln',-288,-1854)]):
        stations.append(dict(id=999600+index,template=obj_id,name=label,x=x,y=y,z=0,heading=128))
    # Traders form small groups instead of a straight sales line.
    trade_positions=[(-278,-1660),(-258,-1670),(-227,-1690),(-200,-1697),(-138,-1642),(-118,-1657),
                     (-104,-1720),(-121,-1737),(-292,-1730),(-279,-1744),(-171,-1796),(-153,-1780),
                     (-51,-1770),(-24,-1777),(-365,-1742),(-347,-1755)]
    trade_ids=list(range(999500,999510))+list(range(999680,999686))
    for ident,(x,y) in zip(trade_ids,trade_positions):
        if ident<999600:relocations[ident]=pos(x,y,x+15,y-4)
        else:npcs.append(dict(id=ident,name=['Doran','Mella','Kavin','Brinna','Osric','Tyra'][ident-999680],
                             title='Tunnel Trader',role='trader',kind='sell' if ident<999684 else 'buy',position=pos(x,y,x-12,y+10)))
    for ident,(x,y) in zip(range(999520,999526),[(-370,-1650),(-278,-1596),(-303,-1723),(-212,-1540),(-184,-1756),(-85,-1530)]):
        relocations[ident]=pos(x,y,x+12,y+5)
    # Eight walkers cross the open aisles and pause beside conversation groups.
    routes=[ [(-320,-1635),(-270,-1628),(-210,-1635),(-168,-1655)],
             [(-294,-1710),(-255,-1720),(-203,-1736),(-160,-1745)],
             [(-145,-1608),(-155,-1650),(-172,-1695),(-195,-1738)],
             [(-310,-1760),(-283,-1764),(-214,-1745),(-159,-1760)],
             [(-380,-1620),(-372,-1650),(-388,-1690),(-371,-1723)],
             [(-87,-1640),(-80,-1678),(-64,-1712),(-88,-1740)],
             [(-277,-1530),(-230,-1530),(-181,-1544),(-134,-1550)],
             [(-305,-1810),(-260,-1830),(-213,-1840),(-155,-1838)] ]
    for index,route in enumerate(routes):
        ident=999700+index; points=[pos(x,y) for x,y in route]
        paths[ident]=points
        npcs.append(dict(id=ident,name=['Alwen','Borin','Cassia','Darik','Esme','Galen','Hessa','Iven'][index],
                         title='',role='walker',position=points[0]))
    return dict(stock=stock,npcs=npcs,relocations=relocations,stations=stations,paths=paths,
                starter_items=starter_items(source),traders=trade_ids)


def stringify(row):
    return {k:str(v) if v is not None else None for k,v in row.items()}


def spawn_position(position):
    # spawn2 FLOAT(14,6) returns fixed precision after single-precision storage.
    return {k:format(struct.unpack('f',struct.pack('f',float(v)))[0],'.6f') for k,v in position.items()}


def desired(before, layout):
    out=copy.deepcopy(before['rows'])
    for table,rows in out.items():
        if table=='zone_state_spawns':continue
        for row in rows:
            if table=='items' and int(row['id']) in REAGENT_PRICES:
                if int(row['price'])!=0:raise ValueError('Reagent price baseline changed')
                row['price']=str(REAGENT_PRICES[int(row['id'])])
                continue
            if table in ('object','grid','grid_entries','items','merchantlist'):
                raise ValueError('Reserved content collision: '+table)
            identity=int(row.get('id',row.get('npc_id',row.get('npcID',0))))
            if 999600<=identity<=999799:raise ValueError('Reserved identity collision: '+table)
    if {int(r['id']) for r in out['items']}!=set(REAGENT_PRICES):
        raise ValueError('Missing reagent price preimage')
    existing={int(n['id']):n for n in out['npc_types']}
    if set(existing)!=set(layout['relocations']):raise ValueError('Existing service roster changed')
    if len(out['spawn2'])!=len(existing) or len(out['spawnentry'])!=len(existing):raise ValueError('Shared service spawn topology')
    for row in out['spawn2']:
        npc=int(row['spawngroupID'])
        if npc not in existing or row['zone']!='ecommons' or row['version']!='0' or row['pathgrid']!='0':
            raise ValueError('Unexpected existing placement')
        row.update(spawn_position(layout['relocations'][npc]))
    templates=before['source']['templates']
    spawn_template=before['rows']['spawn2'][0]
    group_template=before['rows']['spawngroup'][0]
    entry_template=before['rows']['spawnentry'][0]
    stock_template=before['source']['stock'][0]
    for index,npc in enumerate(layout['npcs']):
        ident=npc['id']; merchant=npc['role']=='merchant'
        row=copy.deepcopy(templates[index%len(templates)])
        row.update(stringify(dict(id=ident,name=npc['name'],lastname=npc['title'],level=50,maxlevel=50,
            **{'class':41 if merchant else npc.get('class_id',1)},hp=100000,mana=0,loottable_id=0,
            merchant_id=ident if merchant else 0,alt_currency_id=0,npc_spells_id=0,npc_spells_effects_id=0,
            npc_faction_id=0,adventure_template_id=0,trap_template=0,
            special_abilities='19,1^20,1^24,1^35,1',npcspecialattks='',aggroradius=0,assistradius=0,
            npc_aggro=0,always_aggro=0,raid_target=0,spawn_limit=1,findable=0 if npc['role']=='walker' else 1,
            emoteid=0,private_corpse=0,isquest=1,skip_global_loot=1,keeps_sold_items=0,is_parcel_merchant=0,
            multiquest_enabled=0,qglobal=0,unique_spawn_by_name=1,walkspeed=0.55,runspeed=0.8,
            armortint_id=0,npc_tint_id=0,herosforgemodel=0)))
        out['npc_types'].append(row)
        group=copy.deepcopy(group_template);group.update(stringify(dict(id=ident,name='NightcapTunnel'+str(ident))))
        entry=copy.deepcopy(entry_template);entry.update(stringify(dict(spawngroupID=ident,npcID=ident,chance=100)))
        spawn=copy.deepcopy(spawn_template);spawn.update(stringify(dict(id=ident,spawngroupID=ident,
            zone='ecommons',version=0,**npc['position'],pathgrid=ident if npc['role']=='walker' else 0,
            respawntime=60,variance=0,min_expansion=0,max_expansion=-1)))
        spawn.update(spawn_position(npc['position']))
        out['spawngroup'].append(group);out['spawnentry'].append(entry);out['spawn2'].append(spawn)
        if merchant:
            for slot,item in enumerate(npc['stock'],1):
                stock=copy.deepcopy(stock_template)
                stock.update(stringify(dict(merchantid=ident,slot=slot,item=item,faction_required=-100,
                    level_required=0,min_status=0,max_status=255,alt_currency_cost=0,classes_required=65535,
                    probability=100,bucket_name='',bucket_value='',bucket_comparison=0,
                    min_expansion=0,max_expansion=-1,content_flags=None,content_flags_disabled=None)))
                out['merchantlist'].append(stock)
        if npc['role']=='trader':out['nightcap_market_actors'].append(stringify(dict(npc_id=ident,zone_id=22,kind=npc['kind'])))
    objects={int(o['id']):o for o in before['source']['objects']}
    for station in layout['stations']:
        row=copy.deepcopy(objects[station['template']])
        row.update(stringify(dict(id=station['id'],zoneid=22,version=0,xpos=station['x'],ypos=station['y'],
            zpos=station['z'],heading=station['heading'],display_name=station['name'])))
        out['object'].append(row)
    for ident,points in layout['paths'].items():
        out['grid'].append(stringify(dict(id=ident,zoneid=22,type=3,type2=1)))
        for number,point in enumerate(points,1):
            out['grid_entries'].append(stringify(dict(gridid=ident,zoneid=22,number=number,**point,pause=12+number*5,centerpoint=0)))
    out['items']+=layout['starter_items']
    out['zone_state_spawns']=[]
    return dict(before,rows=out,status='expected_after_not_applied')


def rollback_target(before,after):
    rollback=copy.deepcopy(before)
    # Keep definitions players may own; restore the original native reagent price.
    rollback['rows']['items'] += [r for r in after['rows']['items'] if 998600<=int(r['id'])<=998639]
    rollback['rows']['zone_state_spawns']=[]
    return rollback


def patch_sql(before, after):
    sql=[]
    for table,keys in KEYS.items():
        old=before['rows'][table];new=after['rows'][table]
        sql += [f"SELECT COUNT(*) INTO n FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='{table}' AND ENGINE='InnoDB';",
                f"IF n<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Tunnel engine drift: {table}'; END IF;",
                f"SELECT COUNT(*) INTO n FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() AND EVENT_OBJECT_TABLE='{table}';",
                f"IF n<>0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Tunnel trigger drift: {table}'; END IF;",
                f"SELECT COUNT(*) INTO n FROM `{table}` WHERE {before['scopes'][table]} FOR UPDATE;",
                f"IF n<>{len(old)} THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Tunnel count drift: {table}'; END IF;"]
        for row in old:
            sql += [f'SELECT COUNT(*) INTO n FROM `{table}` WHERE '+indexed_predicate(table,row)+';',
                    f"IF n<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Tunnel row drift: {table}'; END IF;"]
    # All guards precede writes: collisions/drift leave the complete preimage intact.
    for table,keys in KEYS.items():
        old={tuple(r[k] for k in keys):r for r in before['rows'][table]}
        new={tuple(r[k] for k in keys):r for r in after['rows'][table]}
        for key,row in old.items():
            if key not in new:sql.append(f'DELETE FROM `{table}` WHERE '+indexed_predicate(table,row)+';')
            elif row!=new[key]:
                changes={k:v for k,v in new[key].items() if row[k]!=v}
                sql.append(f'UPDATE `{table}` SET '+','.join('`'+k+'`='+sql_value(v) for k,v in changes.items())+' WHERE '+indexed_predicate(table,row)+';')
        for key,row in new.items():
            if key not in old:sql.append(insert(table,row))
    return ('-- Stop world/zones, capture fresh preimages and back up before applying.\n'
        'DELIMITER //\nBEGIN NOT ATOMIC\nDECLARE n BIGINT;\n'
        'DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;\n'
        'SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;\nSTART TRANSACTION;\n'+'\n'.join(sql)+
        '\nCOMMIT;\nEND //\nDELIMITER ;\n')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',required=True,type=Path)
    p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    if a.output.exists():raise ValueError('Refusing to overwrite generation')
    before=json.loads(a.source.read_bytes());layout=plan(before['source']);after=desired(before,layout)
    rollback=rollback_target(before,after)
    a.output.mkdir(parents=True)
    (a.output/'plan.json').write_text(json.dumps(layout,indent=2)+'\n')
    (a.output/'after.json').write_text(json.dumps(after,separators=(',',':'))+'\n')
    (a.output/'forward.sql').write_text(patch_sql(before,after))
    (a.output/'rollback.sql').write_text(patch_sql(after,rollback))
    points=[dict(label=str(i),**p) for i,p in layout['relocations'].items()]
    points += [dict(label=n['name'],**n['position']) for n in layout['npcs']]
    points += [dict(label=s['name'],x=s['x'],y=s['y'],z=3.75) for s in layout['stations']]
    segments=[]
    for ident,route in layout['paths'].items():
        points += [dict(label=f'path-{ident}-{i}',**p) for i,p in enumerate(route)]
        for a1,b in zip(route,route[1:]):
            segments.append({'from':[a1['x'],a1['y'],a1['z']+3], 'to':[b['x'],b['y'],b['z']+3]})
            steps=math.ceil(math.hypot(b['x']-a1['x'],b['y']-a1['y'])/10)
            for step in range(1,steps):
                points.append(dict(label=f'path-{ident}-sample-{len(points)}',
                    x=a1['x']+(b['x']-a1['x'])*step/steps,y=a1['y']+(b['y']-a1['y'])*step/steps,z=3.75))
    (a.output/'probe-input.json').write_text(json.dumps(dict(map='/home/eqemu/server/maps/base/ecommons.map',points=points,segments=segments)))
    print(json.dumps(dict(new_npcs=len(layout['npcs']),merchants=sum(n['role']=='merchant' for n in layout['npcs']),
        trainers=16,walkers=8,stations=6,reagents=len(layout['stock']['reagents']),starter_items=32,status='generated_not_applied')))


if __name__=='__main__':main()
