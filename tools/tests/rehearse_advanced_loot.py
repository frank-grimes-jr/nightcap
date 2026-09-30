"""Rehearse candidate DDL and receipt atomicity in a disposable MariaDB schema.

This exercises SQL storage semantics, not the native Client/Corpse adapter.
PEQ is read only as a schema template; no live character rows are copied.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import secrets
import subprocess


def run(migration: Path, output: Path, container: str):
    schema = 'nightcap_advloot_test_' + secrets.token_hex(6)
    assert re.fullmatch(r'nightcap_advloot_test_[0-9a-f]{12}', schema)
    checks = []
    created = False

    def sql(source, *, use=True, check=True):
        command = ['docker', 'exec', '-i', container, 'sh', '-c',
                   'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" '
                   'exec mariadb -uroot --batch --raw --skip-column-names']
        result = subprocess.run(command, input=(f'USE `{schema}`;\n' if use else '') + source,
                                text=True, encoding='utf-8', capture_output=True, timeout=30)
        if check and result.returncode:
            raise RuntimeError(result.stderr[-2500:])
        return result

    def verify(ok, label):
        if not ok:
            raise AssertionError(label)
        checks.append(label)

    def fingerprint():
        source = '\n'.join(f'SELECT * FROM {table} ORDER BY {order};' for table, order in (
            ('inventory', 'character_id,slot_id'), ('character_currency', 'id'),
            ('character_advloot_claims', 'drop_id'), ('character_advloot_filters', 'character_id,item_id'),
            ('character_advloot_settings', 'character_id')))
        return hashlib.sha256(sql(source).stdout.encode()).hexdigest()

    ddl = migration.read_text(encoding='utf-8')
    claim = "INSERT INTO character_advloot_claims(drop_id,character_id,item_id,charges,inventory_after) VALUES ('11111111-1111-1111-1111-111111111111',77,13073,2,X'66697874757265');"
    insert_item = "INSERT INTO inventory(character_id,slot_id,item_id,charges,guid,custom_data) VALUES(77,23,13073,2,901,X'66697874757265');"
    try:
        sql(f'CREATE DATABASE `{schema}`;', use=False)
        created = True
        sql('CREATE TABLE inventory LIKE peq.inventory; CREATE TABLE character_currency LIKE peq.character_currency;')
        sql(ddl)
        engines = sql("SELECT TABLE_NAME,ENGINE FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() ORDER BY TABLE_NAME;").stdout.strip().splitlines()
        verify(len(engines) == 5 and all(line.endswith('\tInnoDB') for line in engines), 'all fixture transfer tables use InnoDB')
        before = fingerprint()
        verify(sql(ddl, check=False).returncode != 0, 'reapplying the migration fails on existing names')
        verify(fingerprint() == before, 'rejected migration replay preserves existing data')

        sql('INSERT INTO character_advloot_settings(character_id) VALUES(77);')
        verify(sql('SELECT settings FROM character_advloot_settings WHERE character_id=77;').stdout.strip() == '7', 'new character settings default to enabled, filters and auto-show')
        verify(sql('UPDATE character_advloot_settings SET settings=64 WHERE character_id=77;', check=False).returncode != 0, 'invalid setting bits rejected by database')
        sql('INSERT INTO character_advloot_filters VALUES(77,13073,2); INSERT INTO character_advloot_filters VALUES(88,13073,4);')
        sql('INSERT INTO character_advloot_filters VALUES(77,13073,3) ON DUPLICATE KEY UPDATE filter=VALUES(filter);')
        verify(sql('SELECT filter FROM character_advloot_filters ORDER BY character_id;').stdout.strip() == '3\n4', 'per-character filter update leaves the other character unchanged')
        verify(sql('UPDATE character_advloot_filters SET filter=5 WHERE character_id=77;', check=False).returncode != 0, 'invalid filter value rejected by database')
        sql('DELETE FROM character_advloot_filters WHERE character_id=77 AND item_id=13073;')
        verify(sql('SELECT COUNT(*) FROM character_advloot_filters WHERE character_id=77;').stdout.strip() == '0', 'Ask removes the saved automatic choice')

        original = fingerprint()
        sql('START TRANSACTION;' + insert_item + claim + 'ROLLBACK;')
        verify(fingerprint() == original, 'rollback removes both inventory change and drop receipt')
        sql('START TRANSACTION;' + insert_item + claim + 'COMMIT;')
        verify(sql("SELECT charges,HEX(custom_data) FROM inventory WHERE character_id=77 AND slot_id=23; SELECT COUNT(*) FROM character_advloot_claims;").stdout.strip() == '2\t66697874757265\n1', 'item metadata and receipt commit together')
        awarded = fingerprint()
        # The MariaDB client closes its connection on the duplicate-key error;
        # the uncommitted inventory update must roll back with that connection.
        replay = sql('START TRANSACTION; UPDATE inventory SET charges=charges+2 WHERE character_id=77 AND slot_id=23;' + claim + 'COMMIT;', check=False)
        verify(replay.returncode != 0 and fingerprint() == awarded, 'duplicate physical drop cannot commit a second inventory award')
        other = claim.replace(',77,13073,', ',88,13073,')
        verify(sql(other, check=False).returncode != 0 and fingerprint() == awarded, 'receipt uniqueness spans all characters')

        sql('INSERT INTO character_currency(id,copper,silver,gold,platinum) VALUES(77,10,20,30,40),(88,11,21,31,41);')
        money_before = fingerprint()
        sql('START TRANSACTION; UPDATE character_currency SET copper=copper+4 WHERE id=77; ROLLBACK;')
        verify(fingerprint() == money_before, 'interrupted split leaves every wallet unchanged')
        coin_claim = "INSERT INTO character_advloot_claims(drop_id,character_id,item_id,charges,inventory_after) VALUES('22222222-2222-2222-2222-222222222222',77,0,0,X'636f696e');"
        sql('START TRANSACTION; UPDATE character_currency SET copper=copper+4 WHERE id=77; UPDATE character_currency SET copper=copper+3 WHERE id=88;' + coin_claim + 'COMMIT;')
        verify(sql('SELECT copper FROM character_currency ORDER BY id;').stdout.strip() == '14\n14', 'coin split conserves all seven fixture copper, including the remainder')
        money_after = fingerprint()
        verify(sql('START TRANSACTION; UPDATE character_currency SET copper=copper+4 WHERE id=77;' + coin_claim + 'COMMIT;', check=False).returncode != 0 and fingerprint() == money_after, 'coin receipt prevents replay of a saved corpse purse')
        # Operational rollback disables the feature and retains all its data.
        verify(sql('SELECT COUNT(*) FROM character_advloot_claims; SELECT COUNT(*) FROM character_advloot_filters;').stdout.strip() == '2\n1', 'award receipts and player preferences remain available for rollback and recovery')
        evidence = {'status': 'passed', 'scope': 'isolated schema; SQL storage only, no native client or server execution',
                    'migration_sha256': hashlib.sha256(migration.read_bytes()).hexdigest(), 'checks': checks,
                    'schema_template_engines': engines}
    finally:
        if created:
            assert re.fullmatch(r'nightcap_advloot_test_[0-9a-f]{12}', schema)
            sql(f'DROP DATABASE `{schema}`;', use=False)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(evidence, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': evidence['status'], 'checks': len(checks), 'evidence': str(output)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--migration', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--container', default='akk-stack-mariadb-1')
    arguments = parser.parse_args()
    run(arguments.migration, arguments.output, arguments.container)
