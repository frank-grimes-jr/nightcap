"""Capture and generate the approved EC hub migration. Never applies live SQL."""
import argparse,copy,json,math
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from pok_compact_hub import PLAN as SERVICES
from pok_hub_migration import read_sql,sql_value,predicate

ROOT=Path(__file__).resolve().parents[1]
RECALL=42604
NEW_DOORS=range(40600,40622)
ROUTES=[('qeynos2',2049,5996),('freportw',2052,5783),('gfaydark',2041,4969),
        ('butcher',2042,12913),('everfrost',2043,3415),('misty',2040,4139),
        ('nektulos',17151,12283),('feerrott',2058,5337),('innothule',2056,5070),('tox',2045,9)]
KEYS={'npc_types':['id'],'spawn2':['id'],'spawngroup':['id'],'spawnentry':['spawngroupID','npcID'],
      'merchantlist':['merchantid','slot'],'zone_state_spawns':['id'],'doors':['id'],
      'start_zones':['player_choice','player_race','player_class','player_deity'],
      'rule_values':['ruleset_id','rule_name'],'zone':['id'],'spells_new':['id'],
      'aa_ability':['id'],'aa_ranks':['id']}
FIELDS={'spawn2':{'zone','x','y','z','heading'},'doors':set(),
        'start_zones':{'zone_id','start_zone','bind_id','x','y','z','heading','bind_x','bind_y','bind_z'},
        'rule_values':{'rule_value'},'zone':{'safe_x','safe_y','safe_z','safe_heading','map_file_name'},
        'aa_ability':{'type','category'},'aa_ranks':{'spell','title_sid','desc_sid','upper_hotkey_sid'}}

def scopes():
    ids=','.join(map(str,sorted(SERVICES)))
    zones=','.join(sql_value(z) for z,_,_ in ROUTES)
    doors=','.join(str(i) for _,a,b in ROUTES for i in (a,b))
    return {'npc_types':f'id IN ({ids})','spawn2':f'spawngroupID IN ({ids})',
      'spawngroup':f'id IN ({ids})','spawnentry':f'spawngroupID IN ({ids}) OR npcID IN ({ids})',
      'merchantlist':f'merchantid IN (SELECT merchant_id FROM npc_types WHERE id IN ({ids}) AND merchant_id<>0)',
      'zone_state_spawns':f'zone_id IN(22,202) AND instance_id=0 AND is_corpse=0 AND is_zone=0 AND (npc_id IN({ids}) OR spawngroup_id IN({ids}) OR spawn2_id IN(SELECT id FROM spawn2 WHERE spawngroupID IN({ids})))',
      'doors':f'id IN({doors}) OR id BETWEEN 40600 AND 40621 OR (zone IN({zones},\'ecommons\',\'poknowledge\') AND doorid BETWEEN 200 AND 211)',
      'start_zones':'1=1',
      'rule_values':"rule_name IN('World:SoFStartZoneID','World:TitaniumStartZoneID','World:StartZoneSameAsBindOnCreation','World:EnableTutorialButton','World:TutorialZoneID','Expansion:CurrentExpansion','Character:MaxLevel') AND ruleset_id IN(1,10)",
      'zone':f'version=0 AND short_name IN({zones},\'ecommons\',\'poknowledge\')',
      'spells_new':'id IN(3134,99001,42604)','aa_ability':'id=2220','aa_ranks':'id=22200'}

def reference_guards():
    spell=RECALL
    checks={'items':f'SELECT COUNT(*) FROM items WHERE scrolleffect={spell} OR clickeffect={spell} OR proceffect={spell} OR worneffect={spell} OR focuseffect={spell}',
      'other_aa':f'SELECT COUNT(*) FROM aa_ranks WHERE id<>22200 AND (spell={spell} OR title_sid=22200 OR desc_sid=22200 OR upper_hotkey_sid=22200 OR lower_hotkey_sid=22200)',
      'npc_spells':f'SELECT COUNT(*) FROM npc_spells_entries WHERE spellid={spell}',
      'spellbook':f'SELECT COUNT(*) FROM character_spells WHERE spell_id={spell}',
      'memorized':f'SELECT COUNT(*) FROM character_memmed_spells WHERE spell_id={spell}',
      'disciplines':f'SELECT COUNT(*) FROM character_disciplines WHERE disc_id={spell}',
      'npc_effects':f'SELECT COUNT(*) FROM npc_spells_effects_entries WHERE se_base={spell} OR se_limit={spell} OR se_max={spell}'}
    fields=['RecourseLink']+[f'effect_{part}_value{i}' for part in ('base','limit') for i in range(1,13)]
    checks['indirect_spells']='SELECT COUNT(*) FROM spells_new WHERE '+' OR '.join(f'`{f}`={spell}' for f in fields)
    ids=','.join(map(str,SERVICES))
    checks['respawn_controls']=f'SELECT COUNT(*) FROM respawn_times WHERE instance_id=0 AND id IN(SELECT id FROM spawn2 WHERE spawngroupID IN({ids}))'
    checks['disabled_controls']=f'SELECT COUNT(*) FROM spawn2_disabled WHERE instance_id=0 AND spawn2_id IN(SELECT id FROM spawn2 WHERE spawngroupID IN({ids}))'
    return checks

def capture():
    scope=scopes()
    def schema(table):
        cols=[l.split('\t')[0] for l in read_sql(f'SHOW COLUMNS FROM `{table}`;').splitlines()]
        create=read_sql(f'SHOW CREATE TABLE `{table}`;').split('\t',1)[1].rstrip()
        return table,{'columns':cols,'create':create}
    with ThreadPoolExecutor(max_workers=4) as pool: schemas=dict(pool.map(schema,scope))
    queries=['SET TRANSACTION ISOLATION LEVEL REPEATABLE READ; START TRANSACTION WITH CONSISTENT SNAPSHOT;']
    for table,where in scope.items():
        fields=','.join(sql_value(c)+f',CAST(`{c}` AS CHAR)' for c in schemas[table]['columns'])
        queries.append(f'SELECT {sql_value(table)},JSON_OBJECT({fields}) FROM `{table}` WHERE {where};')
    for key,query in reference_guards().items():queries.append(f"SELECT 'guard',JSON_OBJECT('name',{sql_value(key)},'count',({query}));")
    queries.append('ROLLBACK;');rows={t:[] for t in scope};guards={}
    for line in read_sql('\n'.join(queries)).splitlines():
        table,payload=line.split('\t',1);r=json.loads(payload)
        if table=='guard':guards[r['name']]=r['count']
        else:rows[table].append(r)
    return {'status':'read_only_preimage','schemas':schemas,'scopes':scope,'rows':rows,'reference_guards':guards}

def one(rows,key,value):
    found=[r for r in rows if str(r[key])==str(value)]
    if len(found)!=1:raise ValueError(f'Expected one {key}={value}')
    return found[0]

def desired(before,plan):
    rows=before['rows'];ids=set(SERVICES)
    if any(int(v) for v in before['reference_guards'].values()):raise ValueError('Recall/reference/control collision')
    if any('ENGINE=InnoDB' not in s['create'] for s in before['schemas'].values()):raise ValueError('InnoDB required')
    for table in ('npc_types','spawngroup'):
        if {int(r['id']) for r in rows[table]}!=ids or len(rows[table])!=22:raise ValueError('Service topology drift')
    if len(rows['spawnentry'])!=22 or any(r['spawngroupID']!=r['npcID'] or r['chance']!='100' for r in rows['spawnentry']):raise ValueError('Mixed service group')
    if len(rows['spawn2'])!=22 or {int(r['spawngroupID']) for r in rows['spawn2']}!=ids or any(r['zone']!='poknowledge' or r['version']!='0' or r['pathgrid']!='0' for r in rows['spawn2']):raise ValueError('Unexpected service spawn')
    if len(rows['doors'])!=20 or {int(r['id']) for r in rows['doors']}!={i for _,a,b in ROUTES for i in(a,b)}:raise ValueError('Door reservation collision')
    if len(rows['start_zones'])!=411 or any(r['zone_id']!='202' or r['bind_id']!='202' or r['start_zone']!='202' for r in rows['start_zones']):raise ValueError('Start policy drift')
    if {r['id'] for r in rows['spells_new']}!={'3134','99001'}:raise ValueError('Recall spell collision')
    ability=one(rows['aa_ability'],'id',2220)
    if ability['type']!='0' or ability['category']!='-1':raise ValueError('Recall ability changed')
    rank=one(rows['aa_ranks'],'id',22200)
    if rank['upper_hotkey_sid']!='-1' or rank['lower_hotkey_sid']!='-1':raise ValueError('Recall hotkey changed')
    if rank['spell']!='99001' or rank['recast_time']!='600' or rank['title_sid']!='-1' or rank['desc_sid']!='-1':raise ValueError('Recall rank changed')
    if any(r['is_zone']!='0' or r['is_corpse']!='0' or r['instance_id']!='0' or r['zone_id'] not in('22','202') for r in rows['zone_state_spawns']):raise ValueError('Unsafe state scope')
    after=copy.deepcopy(before);out=after['rows'];arrival=plan['arrival']
    for row in out['spawn2']:
        p=plan['services'][row['spawngroupID']]
        row.update(zone='ecommons',**{k:f'{float(p[k]):.6f}' for k in ('x','y','z','heading')})
    for row in out['start_zones']:
        row.update(zone_id='22',start_zone='22',bind_id='22',**{k:str(arrival[k]) for k in ('x','y','z','heading')},**{'bind_'+k:str(arrival[k]) for k in('x','y','z')})
    sof=[r for r in out['rule_values'] if r['rule_name']=='World:SoFStartZoneID']
    if len(sof)!=2 or any(r['rule_value']!='202' for r in sof):raise ValueError('Start override drift')
    for r in sof:r['rule_value']='22'
    for name,value in [('Expansion:CurrentExpansion','0'),('Character:MaxLevel','50'),('World:EnableTutorialButton','false'),('World:StartZoneSameAsBindOnCreation','true')]:
        if one([r for r in out['rule_values'] if r['ruleset_id']=='1'],'rule_name',name)['rule_value']!=value:raise ValueError('Era drift')
    ec=one(out['zone'],'short_name','ecommons');ec.update({'safe_'+k:str(arrival[k]) for k in('x','y','z','heading')})
    nek=one(out['zone'],'short_name','nektulos')
    if nek['map_file_name']!='nektulos_v0':raise ValueError('Legacy Nektulos map override changed')
    nek['map_file_name']='nektulos_classic'
    for p in plan['doors']:
        row=copy.deepcopy(one(rows['doors'],'id',p['template_id']))
        row.update({k:(format(v,'.10g') if isinstance(v,(int,float)) else str(v)) for k,v in p.items() if k!='template_id'})
        row.update(version='0',opentype='58',size='100',dest_instance='0',min_expansion='0',max_expansion='-1',content_flags=None,content_flags_disabled=None)
        for key in ('guild','lockpick','keyitem','triggerdoor','triggertype','doorisopen','door_param','nokeyring','incline','invert_state','is_ldon_door','dz_switch_id','disable_timer'):row[key]='0'
        if not 0<int(row['doorid'])<256 or int(row['id']) not in NEW_DOORS:raise ValueError('Invalid door identity')
        out['doors'].append(row)
    if {int(r['id']) for r in out['doors']} - {int(r['id']) for r in rows['doors']} != set(NEW_DOORS):raise ValueError('Incomplete travel network')
    spell=copy.deepcopy(one(rows['spells_new'],'id',3134));old=one(rows['spells_new'],'id',99001)
    if spell['effectid1']!='83' or any(spell[f'effectid{i}']!='254' for i in range(2,13)) or spell['buffduration']!='0' or spell['targettype']!='6':raise ValueError('Recall template changed')
    spell.update(id=str(RECALL),name='Ancient Attunement',teleport_zone='ecommons',cast_time=old['cast_time'],recast_time=old['recast_time'],recovery_time=old['recovery_time'],mana=old['mana'])
    for i,value in enumerate((arrival['y'],arrival['x'],math.ceil(arrival['z']),arrival['heading']),1):spell[f'effect_base_value{i}']=str(value)
    for i in range(1,17):spell[f'classes{i}']='255'
    out['spells_new'].append(spell);one(out['aa_ranks'],'id',22200).update(spell=str(RECALL),title_sid='22200',desc_sid='22200',upper_hotkey_sid='22200')
    one(out['aa_ability'],'id',2220).update(type='1',category='9')
    out['zone_state_spawns']=[];after['status']='expected_after_not_applied'
    return after

def key(table,row):return tuple(row[k] for k in KEYS[table])
def where(table,row):return ' AND '.join(f'`{k}`<=>{sql_value(row[k])}' for k in KEYS[table])+' AND '+predicate(row)
def insert(table,row):return f'INSERT INTO `{table}` ('+','.join('`'+k+'`' for k in row)+') VALUES ('+','.join(sql_value(v) for v in row.values())+');'

def patch_sql(before,after):
    statements=[]
    for table in KEYS:
        statements += [f"SELECT COUNT(*) INTO n FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='{table}' AND ENGINE='InnoDB';",f"IF n<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Hub engine changed: {table}'; END IF;",f"SELECT COUNT(*) INTO n FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() AND EVENT_OBJECT_TABLE='{table}';",f"IF n<>0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Hub triggers changed: {table}'; END IF;"]
        statements += [f'SELECT COUNT(*) INTO n FROM `{table}` WHERE {before["scopes"][table]} FOR UPDATE;',f"IF n<>{len(before['rows'][table])} THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Hub count drift: {table}'; END IF;"]
        for row in before['rows'][table]:statements += [f'SELECT COUNT(*) INTO n FROM `{table}` WHERE {where(table,row)};',f"IF n<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Hub row drift: {table}'; END IF;"]
    for name,query in reference_guards().items():
        statements += [query.replace('SELECT COUNT(*)','SELECT COUNT(*) INTO n',1)+' FOR UPDATE;',f"IF n<>0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Hub reference drift: {name}'; END IF;"]
    for table in KEYS:
        old={key(table,r):r for r in before['rows'][table]};new={key(table,r):r for r in after['rows'][table]}
        for k,row in old.items():
            if k not in new:
                if not(table=='zone_state_spawns' or table=='doors' and int(row['id']) in NEW_DOORS or table=='spells_new' and int(row['id'])==RECALL):raise ValueError('Unapproved delete')
                statements.append(f'DELETE FROM `{table}` WHERE {where(table,row)};')
            elif row!=new[k]:
                changes={c:v for c,v in new[k].items() if row[c]!=v}
                if not changes.keys()<=FIELDS.get(table,set()):raise ValueError('Unapproved mutation: '+table+str(changes))
                statements.append(f'UPDATE `{table}` SET '+','.join('`'+c+'`='+sql_value(v) for c,v in changes.items())+f' WHERE {where(table,row)};')
        for k,row in new.items():
            if k not in old:
                if not(table=='doors' and int(row['id']) in NEW_DOORS or table=='spells_new' and int(row['id'])==RECALL):raise ValueError('Unapproved insert')
                statements.append(insert(table,row))
    return """-- Fresh captured preimages; stop world/zones and back up PEQ before applying.
DELIMITER //
BEGIN NOT ATOMIC
DECLARE n BIGINT;
DECLARE held INT DEFAULT 0;
DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; IF held=1 THEN DO RELEASE_LOCK('nightcap_ecommons_hub'); END IF; RESIGNAL; END;
SELECT GET_LOCK('nightcap_ecommons_hub',0) INTO held;
IF held<>1 OR held IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Hub operation already running'; END IF;
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
START TRANSACTION;
"""+'\n'.join(statements)+"\nCOMMIT;\nDO RELEASE_LOCK('nightcap_ecommons_hub');\nEND //\nDELIMITER ;\n"

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--before',required=True,type=Path);p.add_argument('--capture',action='store_true');p.add_argument('--plan',type=Path,default=ROOT/'docs/ecommons-hub/plan.json');p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    if a.output.exists():raise ValueError('Refusing to overwrite generation')
    if a.capture:
        if a.before.exists():raise ValueError('Refusing to overwrite preimage')
        a.before.parent.mkdir(parents=True,exist_ok=True);a.before.write_text(json.dumps(capture(),separators=(',',':'))+'\n')
    before=json.loads(a.before.read_bytes());plan=json.loads(a.plan.read_bytes());after=desired(before,plan)
    rollback=copy.deepcopy(before);rollback['rows']['zone_state_spawns']=[]
    a.output.mkdir(parents=True)
    for name,data in [('before.json',before),('after.json',after)]: (a.output/name).write_text(json.dumps(data,separators=(',',':'))+'\n')
    (a.output/'forward.sql').write_text(patch_sql(before,after));(a.output/'rollback.sql').write_text(patch_sql(after,rollback))
    print(json.dumps({'generated_not_applied':True,'services':22,'new_doors':22,'states':len(before['rows']['zone_state_spawns']),'recall_spell':RECALL}))
if __name__=='__main__':main()
