"""Compile explicit dungeon rows and guarded, transactional content SQL."""
import json
from pathlib import Path
from dungeon_prepare import sql

ROOT=Path(__file__).resolve().parents[1]

def insert(table,row):
    return 'INSERT INTO `'+table+'` ('+','.join('`'+k+'`' for k in row)+') VALUES ('+','.join(sql(v) for v in row.values())+');'

def generate():
    folder=ROOT/'docs/dungeons'
    catalog=json.loads((folder/'catalog.json').read_text())
    adapted=json.loads((folder/'classic-ct-adapted.json').read_text())
    snapshot=json.loads((folder/'local-content.json').read_text())
    tables=dict(adapted['tables'])
    tables['items']=[r['values'] for r in catalog['items']]
    tables['tasks']=[];tables['task_activities']=[]
    for d in catalog['dungeons']:
        for mode in ('grind','raid'):
            task=d['task_'+mode]
            tables['tasks'].append(dict(id=task,type=2,duration=43200,title=d['zone'].title()+' - '+mode.title(),
                description='Receive personal encounter credit for every required boss. The Keeper shows permanent completion counts and delivers your earned reward. Your mode and deadline are fixed for this run. No credit is given for missed kills.',
                reward_text='Claim your earned item from the Instance Keeper.',repeatable=1,enabled=1))
            for b in d['bosses']:
                tables['task_activities'].append(dict(taskid=task,activityid=b['boss_id']-1,step=0,activitytype=0,
                    target_name=b['name'],description_override='Receive encounter credit: '+b['name'],goalcount=1,zones=str(d['zone_id'])))
            tables['task_activities'].append(dict(taskid=task,activityid=len(d['bosses']),step=0,activitytype=0,
                target_name='Dungeon Journal',description_override='Keeper: Status / Claim Rewards. This journal remains until the run expires.',goalcount=1,zones=str(d['zone_id'])))
    out=['-- Offline candidate installation. Additive schema must already exist and be disabled.',
         '-- Rehearse against an isolated copy. Retain definitions, runs, and receipts on disable.',
         'DELIMITER //','CREATE PROCEDURE nightcap_dungeon_content_20261016()','BEGIN',
         "DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;",
         'START TRANSACTION;',
         "IF NOT EXISTS (SELECT 1 FROM nightcap_dungeon_state WHERE id=1 AND revision=2026101601 AND enabled=0) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Dungeon state/revision mismatch'; END IF;"]
    for table,data in tables.items():
        if not data:continue
        if table=='nightcap_dungeon_spawns':where='zone_id=48'
        elif table=='spawnentry':where='spawngroupID BETWEEN 985000 AND 985299'
        elif table=='loottable_entries':where='loottable_id BETWEEN 985000 AND 985299'
        elif table=='lootdrop_entries':where='lootdrop_id BETWEEN 985000 AND 985299'
        elif table=='npc_faction_entries':where='npc_faction_id BETWEEN 985000 AND 985299'
        elif table=='grid_entries':where='zoneid=48 AND gridid BETWEEN 9900 AND 9999'
        elif table=='grid':where='zoneid=48 AND id BETWEEN 9900 AND 9999'
        elif table=='task_activities':where='taskid BETWEEN 9700 AND 9713'
        else:where='id IN ('+','.join(str(r['id']) for r in data)+')'
        out.append(f"IF EXISTS (SELECT 1 FROM `{table}` WHERE {where}) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Reserved identity collision: {table}'; END IF;")
        out.append(f"IF NOT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='{table}' AND engine='InnoDB') OR EXISTS (SELECT 1 FROM information_schema.triggers WHERE trigger_schema=DATABASE() AND event_object_table='{table}') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Storage contract failed: {table}'; END IF;")
    # Bind existing objectives to the inspected source rather than overwriting
    # another target's changed NPC/spawn identities. FLOAT comparisons use the
    # same server cast as the row's storage precision.
    for d in catalog['dungeons']:
        if d['zone_id']==48:continue
        for b in d['bosses']:
            npc=next(n for n in snapshot['npc_types'] if n['id']==b['npc_id'])
            checks=' AND '.join('`'+k+'` <=> '+sql(npc[k]) for k in ('id','name','level','class','hp','mindmg','maxdmg','loottable_id','npc_spells_id','npc_faction_id','merchant_id'))
            out.append(f"IF NOT EXISTS (SELECT 1 FROM npc_types WHERE {checks}) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Objective NPC preimage mismatch: {b['npc_id']}'; END IF;")
            spawn=b['spawn']
            checks=' AND '.join('`'+k+'` <=> '+sql(spawn[k]) for k in ('id','zone','version','spawngroupID','respawntime','min_expansion','content_flags','content_flags_disabled'))
            out.append(f"IF NOT EXISTS (SELECT 1 FROM spawn2 WHERE {checks}) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Objective spawn preimage mismatch: {b['spawn_id']}'; END IF;")
    for table,data in tables.items():
        out.extend(insert(table,row) for row in data)
    out+=['COMMIT;','END//','DELIMITER ;','CALL nightcap_dungeon_content_20261016();','DROP PROCEDURE nightcap_dungeon_content_20261016;','']
    (ROOT/'server-mods/sql/20261016_dungeon_content.sql').write_text('\n'.join(out))
    (folder/'install-rows.json').write_text(json.dumps(tables,indent=2)+'\n')
    print({k:len(v) for k,v in tables.items()})

if __name__=='__main__':generate()
