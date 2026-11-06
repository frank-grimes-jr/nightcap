"""Rehearse on a new local-only MariaDB schema. Does not modify peq or player rows."""
import hashlib
import json
from pathlib import Path
import subprocess
import uuid
from augment_audit import OUT, literal

DB = 'nightcap_augment_audit_20261106_' + uuid.uuid4().hex[:8]


def sql(text, database=None, success=True):
    args = ['docker', 'exec', '-i', 'akk-stack-mariadb-1', 'sh', '-c',
            'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" exec mariadb -uroot --batch --raw' + (' ' + database if database else '')]
    p = subprocess.run(args, input=text, text=True, capture_output=True, timeout=120)
    if success and p.returncode:
        raise RuntimeError(p.stderr[-1500:])
    if not success and not p.returncode:
        raise RuntimeError('Expected preimage rejection')
    return p


def insert(table, row):
    return f'INSERT INTO `{table}` (' + ','.join('`' + k + '`' for k in row) + ') VALUES (' + ','.join(map(literal, row.values())) + ');'


def main():
    capture = json.loads((OUT / 'production.json').read_text())
    rows = json.loads((OUT / 'item-preimages.json').read_text())
    initialize = [f'CREATE DATABASE `{DB}`;', f'USE `{DB}`;']
    for key in ('item_schema', 'zone_schema', 'spell_schema'):
        initialize.append(capture[key][0]['Create Table'] + ';')
    initialize += ['CREATE TABLE rule_values(ruleset_id INT,rule_name VARCHAR(128),rule_value VARCHAR(128)) ENGINE=InnoDB;',
                   'CREATE TABLE nightcap_zone_hunt_state(id TINYINT PRIMARY KEY,revision BIGINT,enabled TINYINT) ENGINE=InnoDB;']
    initialize += [insert('nightcap_zone_hunt_state', r) for r in capture['state']]
    initialize += [insert('items', r) for r in capture['items']]
    initialize += [insert('spells_new', r) for r in capture['effects']]
    initialize += [insert('rule_values', r) for r in capture['rules']]
    initialize += [insert('nightcap_zone_hunt_zones', {k: v for k, v in r.items() if k not in ('short_name', 'long_name')}) for r in capture['zones']]
    sql('\n'.join(initialize))
    fingerprint = 'CHECKSUM TABLE items,spells_new,nightcap_zone_hunt_zones,rule_values,nightcap_zone_hunt_state;'
    before = sql(fingerprint, DB).stdout
    forward = (OUT / 'forward.sql').read_text()
    rollback = (OUT / 'rollback.sql').read_text()
    checks = []
    sql(forward, DB)
    for r in rows:
        predicates = ' AND '.join(f'BINARY `{k}` <=> {literal(v)}' for k, v in r['after'].items())
        count = sql(f'SELECT COUNT(*) FROM items WHERE {predicates};', DB).stdout.splitlines()[-1]
        if count != '1':
            raise RuntimeError('Afterimage mismatch ' + r['after']['id'])
    checks.append('all 232 full afterimages match')
    after = sql(fingerprint, DB).stdout
    sql(forward, DB, success=False)
    if sql(fingerprint, DB).stdout != after:
        raise RuntimeError('Replay changed content')
    sql('DROP PROCEDURE nightcap_augments_20261106_forward;', DB)
    checks.append('replay rejected with all tables unchanged')
    sql(rollback, DB)
    if sql(fingerprint, DB).stdout != before:
        raise RuntimeError('Rollback does not restore exact content')
    checks.append('inverse restores all five table checksums exactly')
    # Fail late in the item loop: none of the 231 earlier updates may survive.
    sql("UPDATE items SET hp=hp+1 WHERE id=961023;", DB)
    drift = sql(fingerprint, DB).stdout
    rejected = sql(forward, DB, success=False)
    if 'Augment preimage drift' not in rejected.stderr or sql(fingerprint, DB).stdout != drift:
        raise RuntimeError('Late failure did not roll back completely')
    sql('DROP PROCEDURE nightcap_augments_20261106_forward;', DB)
    sql('UPDATE items SET hp=hp-1 WHERE id=961023;', DB)
    checks.append('last-row drift rolls back all earlier item updates')
    sql('UPDATE nightcap_zone_hunt_zones SET gear_chance=51 WHERE zone_id=186;', DB)
    drift = sql(fingerprint, DB).stdout
    rejected = sql(forward, DB, success=False)
    if 'Zone enable preimage drift' not in rejected.stderr or sql(fingerprint, DB).stdout != drift:
        raise RuntimeError('Zone drift did not roll back items')
    sql('DROP PROCEDURE nightcap_augments_20261106_forward;', DB)
    sql('UPDATE nightcap_zone_hunt_zones SET gear_chance=50 WHERE zone_id=186;', DB)
    checks.append('zone preimage drift rolls back the complete item migration')
    sql("UPDATE rule_values SET rule_value='2' WHERE rule_name='Spells:AdditiveBonusWornType';", DB)
    drift = sql(fingerprint, DB).stdout
    rejected = sql(forward, DB, success=False)
    if 'Unreviewed worn stacking rule' not in rejected.stderr or sql(fingerprint, DB).stdout != drift:
        raise RuntimeError('Additive worn rule not rejected safely')
    checks.append('additive worn rule rejected before writes')
    sql('DROP PROCEDURE nightcap_augments_20261106_forward;', DB)
    sql("UPDATE rule_values SET rule_value='0' WHERE rule_name='Spells:AdditiveBonusWornType'; UPDATE nightcap_zone_hunt_state SET enabled=0;", DB)
    drift = sql(fingerprint, DB).stdout
    rejected = sql(forward, DB, success=False)
    if 'Hunt state drift' not in rejected.stderr or sql(fingerprint, DB).stdout != drift:
        raise RuntimeError('Hunt state guard failed')
    checks.append('disabled Hunt feature state rejected before writes')
    evidence = dict(status='PASS', schema=DB, environment='local disposable MariaDB; no peq/player writes',
        checks=checks, forward_sha256=hashlib.sha256(forward.encode()).hexdigest(),
        rollback_sha256=hashlib.sha256(rollback.encode()).hexdigest())
    (OUT / 'mariadb-rehearsal.json').write_text(json.dumps(evidence, indent=2) + '\n')
    print(json.dumps(evidence))


if __name__ == '__main__':
    main()
