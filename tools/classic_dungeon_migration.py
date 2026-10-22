"""Compile an additive, fail-closed Classic dungeon expansion; never apply it."""
import json
from pathlib import Path
from classic_dungeon_catalog import ADDED_DUNGEONS, SKY_PRIVATE, SKY_SERVICES, SKY_KEY_SERVICE, sky_respawn
from dungeon_contract import predicate
from dungeon_migration import insert
from dungeon_prepare import sql

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/dungeons/classic-expansion-20261022'

def compile_rows():
    capture=json.loads((OUT/'content.json').read_text())
    placements=json.loads((OUT/'placements.json').read_text())
    catalog=json.loads((ROOT/'docs/dungeons/catalog.json').read_text())
    templates=capture['templates']
    rows={k:[] for k in ('npc_types','spawngroup','spawnentry','spawn2','tasks','task_activities','nightcap_dungeon_spawns')}
    for i,(short,zone,keeper,band,roster) in enumerate(ADDED_DUNGEONS):
        pose=placements[short]['selected']['pose']
        npc=dict(templates['npc_types'],id=keeper,name='Instance_Keeper',lastname=short,
                 race=108,gender=2,size=3,texture=0,helmtexture=0,bodytype=1,untargetable=0)
        rows['npc_types'].append(npc)
        rows['spawngroup'].append(dict(templates['spawngroup'],id=keeper,name='nightcap_'+short+'_keeper'))
        rows['spawnentry'].append(dict(templates['spawnentry'],spawngroupID=keeper,npcID=keeper))
        rows['spawn2'].append(dict(templates['spawn2'],id=9100000+i,zone=short,version=0,
            spawngroupID=keeper,**pose,heading=0,pathgrid=0,_condition=0,cond_value=0,
            min_expansion=0,max_expansion=-1,content_flags=None,content_flags_disabled=None))
    rows['npc_types'].append(dict(templates['sky_key_service'],id=SKY_KEY_SERVICE,
        lastname='Island keys',npc_faction_id=0,loottable_id=0,npc_spells_id=0,
        aggroradius=0,assistradius=0,npc_aggro=0,always_aggro=0,
        special_abilities='14,1^15,1^16,1^17,1^19,1^20,1^24,1^25,1^35,1^46,1^47,1^48,1^57,1'))
    for spawn,group,npc,x,y,z,heading in SKY_PRIVATE+SKY_SERVICES:
        rows['spawngroup'].append(dict(templates['spawngroup'],id=group,name='nightcap_sky_'+str(npc)+'_'+str(group)))
        rows['spawnentry'].append(dict(templates['spawnentry'],spawngroupID=group,npcID=npc))
        rows['nightcap_dungeon_spawns'].append(dict(zone_id=71,spawn_id=spawn,group_id=group,npc_id=npc,
            x=x,y=y,z=z,heading=heading,respawn=sky_respawn(npc),grid_id=0))
    for d in catalog['dungeons'][7:]:
        for mode in ('grind','raid'):
            task=d['task_'+mode]
            rows['tasks'].append(dict(id=task,type=2,duration=43200,title=d['zone'].title()+' - '+mode.title(),
                description='Earn personal encounter credit for every required boss. Mode and deadline are fixed for this run.',
                reward_text='Claim your earned item from the Instance Keeper.',repeatable=1,enabled=1))
            for b in d['bosses']:
                rows['task_activities'].append(dict(taskid=task,activityid=b['boss_id']-1,step=0,activitytype=0,
                    target_name=b['name'],description_override='Receive encounter credit: '+b['name'],goalcount=1,zones=str(d['zone_id'])))
            rows['task_activities'].append(dict(taskid=task,activityid=len(d['bosses']),step=1,activitytype=0,
                target_name='Dungeon Journal',description_override='Keeper: Status / Claim Rewards.',goalcount=1,zones=str(d['zone_id'])))
    return rows,capture,catalog

def checks_for(rows,capture,catalog):
    checks=[]
    for table,values in rows.items():
        for offset in range(0,len(values),8):
            batch=values[offset:offset+8]
            checks.append(dict(label=f'classic/{table}/{offset}',sql=f'SELECT COUNT(*) FROM `{table}` WHERE '+' OR '.join(predicate(r) for r in batch),expected=str(len(batch))))
    npcs={r['id']:r for r in capture['npc_types']}
    for d in catalog['dungeons'][7:]:
        for b in d['bosses']:
            fields=('id','name','level','class','hp','mindmg','maxdmg','loottable_id','npc_spells_id','npc_faction_id','merchant_id')
            checks.append(dict(label='classic/objective/'+str(b['npc_id']),sql='SELECT COUNT(*) FROM npc_types WHERE '+predicate({k:npcs[b['npc_id']][k] for k in fields}),expected='1'))
            if b['spawn'].get('managed_private'):continue
            fields=('id','zone','version','spawngroupID','respawntime','min_expansion','content_flags','content_flags_disabled')
            checks.append(dict(label='classic/spawn/'+str(b['spawn_id']),sql='SELECT COUNT(*) FROM spawn2 WHERE '+predicate({k:b['spawn'][k] for k in fields}),expected='1'))
    return checks

def main():
    rows,capture,catalog=compile_rows();checks=checks_for(rows,capture,catalog)
    out=['-- Candidate only. Stop admissions and runtime; back up and rehearse before paired activation.',
         '-- Adds service/content definitions. Never deletes/rewrites existing runs, players, items or receipts.',
         'DELIMITER //','CREATE PROCEDURE nightcap_classic_dungeons_20261022()','BEGIN',
         'DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;',
         'START TRANSACTION;',
         "IF NOT EXISTS (SELECT 1 FROM nightcap_dungeon_state WHERE id=1 AND revision=2026101601) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Original dungeon release required'; END IF;",
         'SELECT id FROM nightcap_dungeon_state WHERE id=1 FOR UPDATE;']
    for table in rows:
        out.append(f"IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='{table}' AND engine='InnoDB') OR EXISTS (SELECT 1 FROM information_schema.triggers WHERE trigger_schema=DATABASE() AND event_object_table='{table}') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Unsafe storage: {table}'; END IF;")
    guards={
        'npc_types':'id BETWEEN 998800 AND 998814',
        'spawngroup':'id BETWEEN 998800 AND 998813 OR id BETWEEN 986000 AND 986011',
        'spawnentry':'npcID BETWEEN 998800 AND 998814 OR spawngroupID BETWEEN 998800 AND 998813 OR spawngroupID BETWEEN 986000 AND 986011',
        'spawn2':'id BETWEEN 9100000 AND 9100013 OR id BETWEEN 9200000 AND 9200011 OR spawngroupID BETWEEN 998800 AND 998813 OR spawngroupID BETWEEN 986000 AND 986011',
        'tasks':'id BETWEEN 9714 AND 9741','task_activities':'taskid BETWEEN 9714 AND 9741',
        'nightcap_dungeon_spawns':'zone_id=71 OR spawn_id BETWEEN 9100000 AND 9100013 OR spawn_id BETWEEN 9200000 AND 9200011'}
    for table,where in guards.items():
        out.append(f"IF EXISTS (SELECT 1 FROM `{table}` WHERE {where}) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Reserved identity collision: {table}'; END IF;")
    for table in ('character_tasks','character_activities','completed_tasks','tasksets'):
        out.append(f"IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='{table}' AND column_name='taskid') THEN IF EXISTS (SELECT 1 FROM `{table}` WHERE taskid BETWEEN 9714 AND 9741) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Reserved task reference collision: {table}'; END IF; END IF;")
    for check in checks:
        if check['label'].startswith(('classic/objective/','classic/spawn/')):
            out.append('IF NOT (('+check['sql']+') <=> '+sql(check['expected'])+") THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT="+sql(check['label'])+'; END IF;')
    for table,values in rows.items():out.extend(insert(table,r) for r in values)
    out+=['COMMIT;','END//','DELIMITER ;','CALL nightcap_classic_dungeons_20261022();','DROP PROCEDURE nightcap_classic_dungeons_20261022;','']
    (ROOT/'server-mods/sql/20261022_classic_dungeons.sql').write_text('\n'.join(out),encoding='utf-8',newline='\n')
    (OUT/'install-rows.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8',newline='\n')
    (OUT/'runtime-checks.json').write_text(json.dumps(checks,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({table:len(values) for table,values in rows.items()}))

if __name__=='__main__':main()
