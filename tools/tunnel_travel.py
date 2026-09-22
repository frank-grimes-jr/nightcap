"""Capture and generate the travel-alcove migration; never applies live SQL."""
import argparse
import copy
import json
import math
from pathlib import Path
from pok_hub_migration import read_sql, predicate, sql_value, insert
from tunnel_services import spawn_position

ROOT = Path(__file__).resolve().parents[1]
GUIDE = 999810
POSITION = dict(x=-335, y=-1537, z=3.75, heading=192)
PROPS = [('HANGLANT', -341, -1537, 60), ('BARREL3', -331, -1527, 100),
         ('CRATEA', -324, -1529, 100)]
ZONES = [('qeynos2',2,'North Qeynos'),('freportw',9,'West Freeport'),
         ('gfaydark',54,'Greater Faydark'),('butcher',68,'Butcherblock Mountains'),
         ('everfrost',30,'Everfrost'),('misty',33,'Misty Thicket'),
         ('nektulos',25,'Nektulos Forest'),('feerrott',47,'The Feerrott'),
         ('innothule',46,'Innothule Swamp'),('tox',38,'Toxxulia Forest')]
KEYS = {'npc_types':['id'], 'spawngroup':['id'], 'spawnentry':['spawngroupID','npcID'],
        'spawn2':['id'], 'doors':['id'], 'zone_state_spawns':['id']}
SCOPES = {
    'npc_types': f'id IN (22033,{GUIDE})',
    'spawngroup': f"id IN (999239,{GUIDE}) OR name='NightcapTunnelTravel'",
    'spawnentry': f'spawngroupID IN (999239,{GUIDE}) OR npcID IN (999239,{GUIDE})',
    'spawn2': f'id={GUIDE} OR spawngroupID IN (999239,{GUIDE})',
    'doors': "id BETWEEN 40600 AND 40621 OR (zone='ecommons' AND doorid BETWEEN 200 AND 210)",
    # Capture references globally; rollback validates a narrower deletion scope.
    # Unexpected instance/corpse references must block, not become dangling rows.
    'zone_state_spawns': f'npc_id={GUIDE} OR spawngroup_id={GUIDE} OR spawn2_id={GUIDE}',
}


def catalog():
    plan=json.loads((ROOT/'docs/ecommons-hub/plan.json').read_bytes())
    doors={d['dest_zone']:d for d in plan['doors'] if d['zone']=='ecommons' and d['id']<40610}
    return [dict(zone=zone,zone_id=ident,label=label,
                 **{k:doors[zone]['dest_'+k] for k in ('x','y','z','heading')})
            for zone,ident,label in ZONES]


def capture(query=read_sql):
    schemas={}; statements=['SET TRANSACTION ISOLATION LEVEL REPEATABLE READ; START TRANSACTION WITH CONSISTENT SNAPSHOT;']
    for table,scope in SCOPES.items():
        columns=[line.split('\t')[0] for line in query(f'SHOW COLUMNS FROM `{table}`;').splitlines()]
        schemas[table]={'create':query(f'SHOW CREATE TABLE `{table}`;').split('\t',1)[1].rstrip()}
        fields=','.join(sql_value(c)+f',CAST(`{c}` AS CHAR)' for c in columns)
        statements.append(f'SELECT {sql_value(table)},JSON_OBJECT({fields}) FROM `{table}` WHERE {scope};')
    statements.append('ROLLBACK;');rows={t:[] for t in SCOPES}
    for line in query('\n'.join(statements)).splitlines():
        table,payload=line.split('\t',1); rows[table].append(json.loads(payload))
    return dict(schemas=schemas,rows=rows)


def desired(before):
    rows=before['rows']
    if {int(r['id']) for r in rows['doors']}!=set(range(40600,40622)) or len(rows['doors'])!=22:
        raise ValueError('Travel door identity/version collision')
    if len(rows['npc_types'])!=1 or rows['npc_types'][0]['id']!='22033':
        raise ValueError('Guide identity occupied or native template missing')
    for table,key in [('spawngroup','id'),('spawnentry','spawngroupID'),('spawn2','spawngroupID')]:
        if len(rows[table])!=1 or rows[table][0][key]!='999239':
            raise ValueError('Guide identity/reference collision: '+table)
    if rows['spawnentry'][0]['npcID']!='999239' or rows['spawnentry'][0]['chance']!='100':
        raise ValueError('Shared template spawn group')
    if rows['zone_state_spawns']:
        raise ValueError('Reserved guide saved state already exists')
    templates={int(d['id']):d for d in rows['doors']}
    approved=json.loads((ROOT/'docs/ecommons-hub/plan.json').read_bytes())
    for planned in approved['doors']:
        if planned['id']>=40610:continue
        door=templates[planned['id']]
        for field,value in planned.items():
            if field=='template_id':continue
            same=(math.isclose(float(door[field]),value,rel_tol=0,abs_tol=0.0001)
                  if isinstance(value,(int,float)) else door[field]==value)
            if not same:raise ValueError('Approved stone geometry/identity drift: '+field)
        if door['size']!='100':raise ValueError('Approved stone size drift')
    for i,route in enumerate(catalog()):
        door=templates[40600+i]
        if door['zone']!='ecommons' or door['version']!='0' or door['opentype']!='58' or door['dest_zone']!=route['zone'] or door['dest_instance']!='0':
            raise ValueError('Travel route drift')
        if any(float(door['dest_'+k])!=float(route[k]) for k in ('x','y','z','heading')):
            raise ValueError('Travel landing drift')
    after=copy.deepcopy(before);out=after['rows']
    out['doors']=[d for d in out['doors'] if int(d['id'])>=40610]
    for i,(model,x,y,size) in enumerate(PROPS):
        door=copy.deepcopy(templates[40600+i])
        door.update(name=model,pos_x=str(x),pos_y=str(y),pos_z='0',heading='0',size=str(size),
                    opentype='9',dest_zone='NONE',dest_x='0',dest_y='0',dest_z='0',dest_heading='0',
                    dest_instance='0',door_param='0',triggerdoor='0',triggertype='0',doorisopen='0',
                    guild='0',lockpick='0',keyitem='0',nokeyring='0',invert_state='0',incline='0',
                    is_ldon_door='0',dz_switch_id='0',disable_timer='0')
        out['doors'].append(door)
    npc=copy.deepcopy(rows['npc_types'][0])
    npc.update({k:str(v) for k,v in dict(id=GUIDE,name='Merrin',lastname='Tunnel Travel',
        level=50,maxlevel=50,hp=100000,mana=0,loottable_id=0,merchant_id=0,alt_currency_id=0,
        npc_spells_id=0,npc_spells_effects_id=0,npc_faction_id=0,adventure_template_id=0,trap_template=0,
        special_abilities='19,1^20,1^24,1^35,1',npcspecialattks='',aggroradius=0,assistradius=0,
        npc_aggro=0,always_aggro=0,raid_target=0,spawn_limit=1,findable=1,emoteid=0,isquest=1,
        skip_global_loot=1,keeps_sold_items=0,is_parcel_merchant=0,multiquest_enabled=0,qglobal=0,
        unique_spawn_by_name=1,armortint_id=0,npc_tint_id=0,herosforgemodel=0).items()})
    npc['class']='1';out['npc_types'].append(npc)
    group=dict(rows['spawngroup'][0],id=str(GUIDE),name='NightcapTunnelTravel')
    entry=dict(rows['spawnentry'][0],spawngroupID=str(GUIDE),npcID=str(GUIDE),chance='100')
    spawn=dict(rows['spawn2'][0],id=str(GUIDE),spawngroupID=str(GUIDE),zone='ecommons',version='0',
               pathgrid='0',respawntime='60',variance='0',min_expansion='0',max_expansion='-1',
               content_flags=None,content_flags_disabled=None,**spawn_position(POSITION))
    out['spawngroup'].append(group);out['spawnentry'].append(entry);out['spawn2'].append(spawn)
    return after


def indexed(table,row):
    return ' AND '.join(f'`{k}` <=> {sql_value(row[k])}' for k in KEYS[table])+' AND '+predicate(row)


def patch_sql(before,after):
    sql=[]
    for table in KEYS:
        sql += [f"SELECT COUNT(*) INTO n FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='{table}' AND ENGINE='InnoDB';",
                f"IF n<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Travel engine drift: {table}'; END IF;",
                f"SELECT COUNT(*) INTO n FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() AND EVENT_OBJECT_TABLE='{table}';",
                f"IF n<>0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Travel trigger drift: {table}'; END IF;",
                f'SELECT COUNT(*) INTO n FROM `{table}` WHERE {SCOPES[table]} FOR UPDATE;',
                f"IF n<>{len(before['rows'][table])} THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Travel count drift: {table}'; END IF;"]
        for row in before['rows'][table]:
            sql += [f'SELECT COUNT(*) INTO n FROM `{table}` WHERE {indexed(table,row)};',
                    f"IF n<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Travel row drift: {table}'; END IF;"]
    for table,keys in KEYS.items():
        old={tuple(r[k] for k in keys):r for r in before['rows'][table]}
        new={tuple(r[k] for k in keys):r for r in after['rows'][table]}
        for key,row in old.items():
            if key not in new:sql.append(f'DELETE FROM `{table}` WHERE {indexed(table,row)};')
            elif row!=new[key]:
                changes=','.join('`'+k+'`='+sql_value(v) for k,v in new[key].items() if row[k]!=v)
                sql.append(f'UPDATE `{table}` SET {changes} WHERE {indexed(table,row)};')
        sql += [insert(table,row) for key,row in new.items() if key not in old]
    return ('-- Stop zones and back up before applying. No player data is written.\nDELIMITER //\nBEGIN NOT ATOMIC\n'
            'DECLARE n BIGINT;\nDECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;\n'
            'SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;\nSTART TRANSACTION;\n'+'\n'.join(sql)+'\nCOMMIT;\nEND //\nDELIMITER ;\n')


def rollback_target(original,current,expected):
    for table in KEYS:
        if table=='zone_state_spawns':continue
        order=lambda r:tuple(r[k] for k in KEYS[table])
        if sorted(current['rows'][table],key=order)!=sorted(expected['rows'][table],key=order):
            raise ValueError('Rollback content drift: '+table)
    for row in current['rows']['zone_state_spawns']:
        if any(row[k]!=str(GUIDE) for k in ('npc_id','spawngroup_id','spawn2_id')) or any(
                row[k]!=v for k,v in dict(zone_id='22',instance_id='0',is_corpse='0',is_zone='0').items()):
            raise ValueError('Ambiguous guide saved state; preserve and investigate')
    target=copy.deepcopy(original);target['rows']['zone_state_spawns']=[]
    return target


def write_catalog(path):
    def perl(v):return str(v) if isinstance(v,(int,float)) else "'"+v.replace("'","\\'")+"'"
    path.write_text('use strict;\nuse warnings;\n# Generated from docs/ecommons-hub/plan.json by tools/tunnel_travel.py.\n'
        'sub tunnel_travel_catalog { return [\n'+'\n'.join('    {'+', '.join(k+' => '+perl(v) for k,v in r.items())+'},' for r in catalog())+'\n]; }\n1;\n')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path);p.add_argument('--capture',action='store_true')
    p.add_argument('--output',type=Path);p.add_argument('--write-catalog',action='store_true')
    p.add_argument('--rollback-from',type=Path)
    a=p.parse_args()
    if a.write_catalog:write_catalog(ROOT/'server-mods/plugins/tunnel_travel_data.pl');return
    if not a.output or a.output.exists():raise ValueError('Choose a new output directory')
    before=capture() if a.capture else json.loads(a.source.read_bytes())
    if a.rollback_from:
        original=json.loads((a.rollback_from/'before.json').read_bytes())
        expected=json.loads((a.rollback_from/'after.json').read_bytes())
        after=rollback_target(original,before,expected)
    else:after=desired(before)
    a.output.mkdir(parents=True)
    for name,data in [('before',before),('after',after)]:
        (a.output/(name+'.json')).write_text(json.dumps(data,indent=2)+'\n')
    (a.output/'forward.sql').write_text(patch_sql(before,after))
    (a.output/'immediate-rollback.sql').write_text(patch_sql(after,before))
    print(json.dumps(dict(generated_not_applied=True,output=str(a.output))))


if __name__=='__main__':main()
