"""Generate guarded candidate installation and explicit runtime content checks."""
import json
from pathlib import Path
from warhelm_content import OUT, ROOT, ENTRANCE, compile_rows, access_policy
from dungeon_catalog import items
from dungeon_contract import predicate as strict_predicate
from dungeon_migration import insert, ITEM_REFERENCES
from dungeon_prepare import sql

def predicate(row):
    # MariaDB FLOAT at Kael's ~2,500-unit coordinates has >0.0001 ULP.
    # One-thousandth tolerates round-trip quantization, not placement changes.
    return strict_predicate(row).replace('<0.0001','<0.001')

SCHEMA='''-- Schema only; disabled until a paired, verified activation.
CREATE TABLE nightcap_ashen_state (
 id TINYINT UNSIGNED PRIMARY KEY, revision BIGINT UNSIGNED NOT NULL,
 enabled TINYINT UNSIGNED NOT NULL DEFAULT 0, CHECK(id=1 AND enabled IN (0,1))
) ENGINE=InnoDB;
INSERT INTO nightcap_ashen_state VALUES(1,2026102401,0);
CREATE TABLE nightcap_ashen_characters (
 character_id INT UNSIGNED PRIMARY KEY, progress INT UNSIGNED NOT NULL DEFAULT 0,
 accepted_at INT UNSIGNED NOT NULL, completed_at INT UNSIGNED NOT NULL DEFAULT 0,
 helmet_drop_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 UNIQUE KEY helmet_receipt(helmet_drop_id), CHECK(progress<8192)
) ENGINE=InnoDB;
'''

def compile_migration():
    before=json.loads((OUT/'local-content.json').read_text())
    rows=compile_rows()
    rows['items'] += [r['values'] for r in items() if r['source']=='kael']
    hazards=json.loads((OUT/'secondary-content.json').read_text())
    checks=[]
    out=['-- Candidate based on LOCAL content. Re-capture/review production before deployment.',
        '-- Pair native binaries, quests and regenerated item cache; stop admissions first.',
        'DELIMITER //','CREATE PROCEDURE nightcap_warhelm_20261024()','BEGIN',
        'DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;',
        'SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;','START TRANSACTION;',
        "IF NOT EXISTS(SELECT 1 FROM nightcap_ashen_state WHERE id=1 AND revision=2026102401 AND enabled=0) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Disabled Compact schema required'; END IF;",
        'SELECT id FROM nightcap_ashen_state WHERE id=1 FOR UPDATE;']
    def require(condition,message):
        # MariaDB 10.5.4 crashes in negate_expression when simplifying nested
        # NOT EXISTS inside NOT(...). IS NOT TRUE also rejects SQL NULL safely.
        out.append(f"IF ({condition}) IS NOT TRUE THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT={sql(message)}; END IF;")
    tables=set(rows)|set(hazards)|{'zone','doors','zone_points','nightcap_ashen_state','nightcap_ashen_characters'}
    for t in sorted(tables):
        require(f"EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='{t}' AND engine='InnoDB') AND NOT EXISTS(SELECT 1 FROM information_schema.triggers WHERE trigger_schema=DATABASE() AND event_object_table='{t}')",'Unsafe storage '+t)
    scopes={'npc_types':'id BETWEEN 998860 AND 998899','spawngroup':'id BETWEEN 998860 AND 998899',
        'spawnentry':'npcID BETWEEN 998860 AND 998899 OR spawngroupID BETWEEN 998860 AND 998899',
        'spawn2':'id BETWEEN 9230000 AND 9230099',
        'items':'id BETWEEN 961020 AND 961039 OR id=990510 OR id BETWEEN 960420 AND 960425',
        'tasks':'id IN (9744,9745,9801)','task_activities':'taskid IN (9744,9745,9801)',
        'nightcap_dungeon_spawns':'zone_id=113 OR spawn_id BETWEEN 9230000 AND 9230099',
        'nightcap_waypoints':"zone='kael' OR zone_id=113"}
    for t,w in scopes.items():require(f'NOT EXISTS(SELECT 1 FROM `{t}` WHERE {w})','Reserved identity collision '+t)
    for t in ('character_tasks','character_activities','completed_tasks','tasksets'):
        require(f'NOT EXISTS(SELECT 1 FROM `{t}` WHERE taskid IN (9744,9745,9801))','Reserved task reference '+t)
    for table,columns in sorted(ITEM_REFERENCES.items()):
        for column in columns:
            out.append(f"IF EXISTS(SELECT 1 FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='{table}' AND column_name='{column}') THEN IF EXISTS(SELECT 1 FROM `{table}` WHERE `{column}` BETWEEN 961020 AND 961039 OR `{column}`=990510 OR `{column}` BETWEEN 960420 AND 960425) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Reserved item reference {table}.{column}'; END IF; END IF;")
    # Never delete saved player corpses, another zone or another instance.
    # Activation requires an operator-captured/cache-cleared public foyer.
    require("NOT EXISTS(SELECT 1 FROM zone_state_spawns WHERE zone_id=113 AND instance_id=0 AND is_corpse=0)",
            'Back up and invalidate Kael public non-corpse saved state first')
    # Public storage is compared completely, including disabled versions. No
    # unexpected source or cached living NPC may survive opening the zone.
    for t,values,w in [('spawn2',before['spawn2'],"zone='kael'"),('doors',before['doors'],"zone='kael'"),
                        ('zone',[z for z in before['zone'] if z['short_name']=='kael'],"short_name='kael' AND version=0")]:
        require(f'(SELECT COUNT(*) FROM `{t}` WHERE {w})={len(values)}','Preimage row count '+t)
        for r in values:require(f'EXISTS(SELECT 1 FROM `{t}` WHERE {predicate(r)})','Preimage drift '+t)
    zone=next(z for z in before['zone'] if z['short_name']=='kael')
    access=access_policy()
    fields=('bypass_expansion_check','min_status','min_level','canbind','safe_x','safe_y','safe_z','safe_heading')
    newzone=dict(zone,**{k:access[k] for k in fields})
    out.append('UPDATE zone SET '+','.join(k+'='+sql(access[k]) for k in fields)+" WHERE short_name='kael' AND version=0;")
    checks.append(dict(label='compact/zone',sql='SELECT COUNT(*) FROM zone WHERE '+predicate(newzone),expected='1'))
    out.append("UPDATE spawn2 SET min_expansion=2,content_flags='nightcap_kael_stock_disabled' WHERE zone='kael';")
    # Original doors remain geometry; every original outbound portal returns to
    # Classic commons. Key requirements cannot introduce later-era item errands.
    x,y,z,h=ENTRANCE
    out.append(f"UPDATE doors SET keyitem=0,lockpick=0,dest_zone=IF(dest_zone<>'NONE','commons','NONE'),dest_x=IF(dest_zone='commons',{x},dest_x),dest_y=IF(dest_zone='commons',{y},dest_y),dest_z=IF(dest_zone='commons',{z},dest_z),dest_heading=IF(dest_zone='commons',{h},dest_heading) WHERE zone='kael';")
    for t,entries in hazards.items():
        w={'zone_points':"zone='kael'",'ground_spawns':'zoneid=113','fishing':'zoneid=113','forage':'zoneid=113',
           'traps':"zone='kael'",'object':'zoneid=113'}[t]
        require(f'(SELECT COUNT(*) FROM `{t}` WHERE {w})={len(entries)}','Secondary source count '+t)
        for r in entries:require(f'EXISTS(SELECT 1 FROM `{t}` WHERE {predicate(r)})','Secondary source drift '+t)
        if t=='zone_points':
            out.append(f"UPDATE zone_points SET target_zone_id=21,target_x={x},target_y={y},target_z={z},target_heading={h},target_instance=0 WHERE zone='kael';")
        else:out.append(f'DELETE FROM `{t}` WHERE {w};')
    for t,values in rows.items():
        out.extend(insert(t,r) for r in values)
        for start in range(0,len(values),8):
            batch=values[start:start+8]
            checks.append(dict(label=f'compact/{t}/{start}',sql=f'SELECT COUNT(*) FROM `{t}` WHERE '+' OR '.join(predicate(r) for r in batch),expected=str(len(batch))))
    checks.extend([
        dict(label='compact/stock-flag-disabled',sql="SELECT COUNT(*) FROM content_flags WHERE flag_name='nightcap_kael_stock_disabled' AND enabled<>0",expected='0'),
        dict(label='compact/no-stock-spawns',sql="SELECT COUNT(*) FROM spawn2 WHERE zone='kael' AND spawngroupID NOT IN (998860,999240) AND (min_expansion<2 OR NOT(content_flags <=> 'nightcap_kael_stock_disabled'))",expected='0'),
        dict(label='compact/no-later-exits',sql="SELECT COUNT(*) FROM doors WHERE zone='kael' AND dest_zone NOT IN ('NONE','commons')",expected='0'),
        dict(label='compact/no-later-zonepoints',sql="SELECT COUNT(*) FROM zone_points WHERE zone='kael' AND target_zone_id<>21",expected='0')])
    for t,w in [('ground_spawns','zoneid=113'),('fishing','zoneid=113'),('forage','zoneid=113'),('traps',"zone='kael'"),('object','zoneid=113')]:
        checks.append(dict(label='compact/no-secondary-'+t,sql=f'SELECT COUNT(*) FROM `{t}` WHERE {w}',expected='0'))
    for c in checks:require('('+c['sql']+')='+c['expected'],'Postcondition '+c['label'])
    out+=['COMMIT;','END//','DELIMITER ;','CALL nightcap_warhelm_20261024();','DROP PROCEDURE nightcap_warhelm_20261024;','']
    (ROOT/'server-mods/sql/20261024_warhelm_schema.sql').write_text(SCHEMA)
    (ROOT/'server-mods/sql/20261024_warhelm_content.sql').write_text('\n'.join(out))
    (OUT/'install-rows.json').write_text(json.dumps(rows,indent=2)+'\n')
    (OUT/'runtime-checks.json').write_text(json.dumps(checks,indent=2)+'\n')
    print(json.dumps({t:len(v) for t,v in rows.items()}))

if __name__=='__main__':compile_migration()
