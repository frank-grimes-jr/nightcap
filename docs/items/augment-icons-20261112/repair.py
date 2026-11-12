"""Exact one-column repair. Import with an authenticated SQL transport, not a CLI."""
import hashlib
import json
import secrets

TARGETS = {2: 404301, 12: 404345, 17: 204852, 18: 404856, 19: 204917}


def fields(columns, after=False):
    assert columns and all(c.replace('_', '').isalnum() for c in columns)
    return ','.join('0' if after and c == 'ornament_icon' else '`' + c + '`' for c in columns)


def inventory(sql, database='peq'):
    columns = [line.split('\t')[0] for line in sql('SHOW COLUMNS FROM inventory;', database).splitlines()]
    rows = [dict(zip(columns, json.loads(line))) for line in sql(
        'SELECT JSON_ARRAY(' + fields(columns) + ') FROM inventory WHERE character_id=29 ORDER BY slot_id;', database).splitlines()]
    return columns, rows


def outside(sql, columns, database='peq'):
    # Hash all inventory rows outside the five keys, including other characters.
    scope = 'NOT (character_id=29 AND slot_id IN (2,12,17,18,19))'
    rows = sql('SELECT SHA2(JSON_ARRAY(' + fields(columns) + '),256) FROM inventory WHERE ' +
               scope + ' ORDER BY character_id,slot_id;', database).splitlines()
    return {'rows': len(rows), 'sha256': hashlib.sha256('\n'.join(rows).encode()).hexdigest()}


def prepare(sql, capture):
    columns, rows = inventory(sql)
    assert columns == capture['columns'] and rows == capture['rows'], 'Fresh stopped inventory differs from reviewed incident capture'
    assert {p['summary']['slot']: p['summary']['item_id'] for p in capture['plan']} == TARGETS
    plan = []
    for item in capture['plan']:
        row = item['before']; slot = int(row['slot_id'])
        assert row['character_id'] == 29 and row['item_id'] == TARGETS[slot]
        assert row['ornament_icon'] in (517, 945, 956) and row['ornament_idfile'] == row['ornament_hero_model'] == 0
        assert item['after'] == {**row, 'ornament_icon': 0}
        line = sql('SELECT SHA2(JSON_ARRAY(' + fields(columns) + '),256),SHA2(JSON_ARRAY(' +
                   fields(columns, True) + '),256) FROM inventory WHERE character_id=29 AND slot_id=' + str(slot) + ';').strip()
        before, after = line.split('\t')
        assert len(before) == len(after) == 64
        plan.append({'slot': slot, 'item_id': TARGETS[slot], 'before_sha256': before, 'after_sha256': after})
    return {'columns': columns, 'plan': plan, 'before_rows': rows, 'outside': outside(sql, columns)}


def statement(prepared, fail_after=None):
    name = 'nightcap_aug_icon_' + secrets.token_hex(8)
    columns = prepared['columns']
    checks = []
    for index, item in enumerate(prepared['plan']):
        where = 'character_id=29 AND slot_id=' + str(item['slot']) + ' AND item_id=' + str(item['item_id'])
        checks += ["SET current_hash=NULL;",
                   'SELECT SHA2(JSON_ARRAY(' + fields(columns) + '),256) INTO current_hash FROM inventory WHERE ' + where + ' FOR UPDATE;',
                   "IF NOT (current_hash <=> '" + item['before_sha256'] + "') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Exact inventory preimage changed'; END IF;",
                   'UPDATE inventory SET ornament_icon=0 WHERE ' + where + ';',
                   "IF ROW_COUNT()<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Inventory repair row count'; END IF;",
                   'SELECT SHA2(JSON_ARRAY(' + fields(columns) + '),256) INTO current_hash FROM inventory WHERE ' + where + ';',
                   "IF NOT (current_hash <=> '" + item['after_sha256'] + "') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Non-icon inventory data changed'; END IF;"]
        if fail_after == index:
            checks.append("SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Injected rollback check';")
    return ('DELIMITER $$\nCREATE PROCEDURE `' + name + '`() SQL SECURITY INVOKER\nBEGIN\n'
            'DECLARE current_hash CHAR(64);\nDECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;\n'
            'START TRANSACTION;\n' + '\n'.join(checks) + '\nCOMMIT;\nEND$$\n'
            'DELIMITER ;\nCALL `' + name + '`();\nDROP PROCEDURE `' + name + '`;\n')


def verify(sql, prepared, database='peq'):
    columns, actual = inventory(sql, database)
    assert columns == prepared['columns']
    expected = [{**row, 'ornament_icon': 0} if int(row['slot_id']) in TARGETS else row for row in prepared['before_rows']]
    assert actual == expected, 'Inventory differs beyond the five icon-only afterimages'
    assert outside(sql, columns, database) == prepared['outside'], 'Unrelated inventory changed'
    return {'repaired_rows': 5, 'preserved_character_rows': len(actual), 'unchanged_fields_except_ornament_icon': True,
            'unrelated_inventory_unchanged': True, 'augments_preserved': True}
