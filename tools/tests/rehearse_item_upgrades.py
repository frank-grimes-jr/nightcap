"""Rehearse box/NPC installation and native combine SQL in disposable MariaDB."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import secrets
import subprocess


def run(release):
    checks = []

    def sql(schema, source, check=True):
        result = subprocess.run(['docker', 'exec', '-i', 'akk-stack-mariadb-1', 'sh', '-c',
            'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" exec mariadb -uroot --batch --raw --skip-column-names'],
            input=(f'USE `{schema}`;\n' if schema else '') + source,
            text=True, encoding='utf-8', capture_output=True, timeout=90)
        if check and result.returncode:
            raise RuntimeError(result.stderr[-3000:])
        return result

    def verify(condition, label):
        if not condition:
            raise AssertionError(label)
        checks.append(label)

    ddl = (release / 'install.sql').read_text()
    trace = json.loads((release / 'inventory-native.json').read_text())['upgrade_queries']
    for collision in (None, 'item', 'npc', 'spawn_reference', 'saved_state', 'recipe', 'disabled_spawn', 'respawn_timer'):
        schema = 'nightcap_item_upgrade_test_' + secrets.token_hex(6)
        assert re.fullmatch(r'nightcap_item_upgrade_test_[0-9a-f]{12}', schema)
        sql(None, f'CREATE DATABASE `{schema}`;')
        try:
            tables = ('items', 'npc_types', 'spawngroup', 'spawnentry', 'spawn2',
                      'zone_state_spawns', 'inventory', 'tradeskill_recipe_entries', 'spawn2_disabled', 'respawn_times')
            sql(schema, '\n'.join(f'CREATE TABLE `{t}` LIKE peq.`{t}`; ALTER TABLE `{t}` ENGINE=InnoDB;' for t in tables))
            sql(schema, '''INSERT INTO items SELECT * FROM peq.items WHERE id=17339;
INSERT INTO npc_types SELECT * FROM peq.npc_types WHERE id=22033;
CREATE TABLE character_advloot_claims (id INT PRIMARY KEY) ENGINE=InnoDB;
CREATE TABLE character_evolving_items (id INT PRIMARY KEY) ENGINE=InnoDB;''')
            collisions = {
                'item': "INSERT INTO items(id,Name) VALUES(900620,'Occupied');",
                'npc': "INSERT INTO npc_types(id,name) VALUES(999820,'Occupied');",
                'spawn_reference': 'INSERT INTO spawnentry(spawngroupID,npcID,chance) VALUES(1,999820,100);',
                'saved_state': 'INSERT INTO zone_state_spawns(npc_id,zone_id,instance_id,spawn2_id,spawngroup_id,x,y,z,heading,respawn_time,variance) VALUES(999820,22,0,0,0,0,0,0,0,60,0);',
                'recipe': 'INSERT INTO tradeskill_recipe_entries(recipe_id,item_id,iscontainer) VALUES(1,900620,1);',
                'disabled_spawn': 'INSERT INTO spawn2_disabled(spawn2_id,instance_id,disabled) VALUES(999820,0,1);',
                'respawn_timer': 'INSERT INTO respawn_times(id,start,duration,instance_id) VALUES(999820,1,600,0);',
            }
            if collision:
                sql(schema, collisions[collision])
                verify(sql(schema, ddl, False).returncode != 0, collision + ' collision refuses install')
                verify(sql(schema, 'SELECT COUNT(*) FROM nightcap_item_upgrade_state; SELECT COUNT(*) FROM spawn2;').stdout.strip() == '0\n0', collision + ' rejection leaves no feature activation or spawn')
                continue
            sql(schema, ddl)
            verify(sql(schema, 'SELECT Name,bagtype,bagslots,bagsize,price FROM items WHERE id=900620;').stdout.strip() == 'Reforging Box\t13\t4\t10\t0', 'free reusable four-slot box installed')
            verify(sql(schema, 'SELECT zone,x,y,z FROM spawn2 WHERE id=999820;').stdout.strip() == 'ecommons\t-385.000000\t-1818.000000\t3.750000', 'one NPC installed at verified tunnel workshop point')
            verify(sql(schema, 'SELECT enabled FROM nightcap_item_upgrade_state;').stdout.strip() == '0', 'installation remains disabled')
            verify(sql(schema, ddl, False).returncode != 0, 'repeat installation refuses ownership')
            sql(schema, (release / 'activate.sql').read_text())
            sql(schema, 'INSERT INTO inventory(character_id,slot_id,item_id,charges,guid) VALUES(77,23,900620,1,901);' +
                '\n'.join(f'INSERT INTO inventory(character_id,slot_id,item_id,charges,guid,instnodrop) VALUES(77,{slot},201001,1,{900+slot},{int(slot==252)});' for slot in range(251, 255)))

            def fingerprint():
                return hashlib.sha256(sql(schema, 'SELECT * FROM inventory ORDER BY character_id,slot_id; SELECT * FROM nightcap_item_upgrades ORDER BY request_id;').stdout.encode()).hexdigest()

            before = fingerprint()
            for index, query in enumerate(trace):
                if not query.startswith(('DELETE FROM inventory', 'INSERT INTO inventory', 'INSERT INTO nightcap_item_upgrades')):
                    continue
                sql(schema, ';\n'.join(trace[:index+1]) + ';\nROLLBACK;')
                verify(fingerprint() == before, f'rollback after native write {index} retains all ingredients and box')
            sql(schema, ';\n'.join(trace) + ';')
            verify(sql(schema, 'SELECT slot_id,item_id,instnodrop FROM inventory ORDER BY slot_id; SELECT COUNT(*) FROM nightcap_item_upgrades;').stdout.strip() == '23\t900620\t0\n251\t401001\t1\n1', 'native SQL commits one bound upgrade, reusable box and receipt')
            committed = fingerprint()
            verify(sql(schema, ';\n'.join(trace) + ';', False).returncode != 0 and fingerprint() == committed, 'duplicate receipt cannot award twice')
            sql(schema, (release / 'rollback.sql').read_text())
            verify(fingerprint() == committed, 'disable rollback retains awarded inventory and receipt')
            verify(sql(schema, 'SELECT enabled FROM nightcap_item_upgrade_state; SELECT COUNT(*) FROM items WHERE id=900620;').stdout.strip() == '0\n1', 'disabled feature retains owned box definition')
        finally:
            assert re.fullmatch(r'nightcap_item_upgrade_test_[0-9a-f]{12}', schema)
            sql(None, f'DROP DATABASE `{schema}`;')
    (release / 'mariadb.json').write_text(json.dumps({'status': 'passed',
        'scope': 'Disposable schemas only; no gameplay database writes',
        'install_sha256': hashlib.sha256(ddl.encode()).hexdigest(), 'checks': checks}, indent=2) + '\n')
    print(f'Passed {len(checks)} MariaDB checks.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--release', type=Path, required=True)
    run(parser.parse_args().release)
