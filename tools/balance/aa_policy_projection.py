"""Project diagnostic AA caps into native loader data, with isolated-only SQL.

This is not a live installer. Production requires a complete offering and owned-AA
reconciliation. Original rank data must be restored before applying another pool.
"""
import re

from aa_policy_preflight import build_preflight


DATABASE = 'nightcap_balance_20260912'
FIELDS = {'aa_ability': 'enabled', 'aa_ranks': 'next_id'}


def project(snapshot, specification, policy_id):
    report = build_preflight(snapshot, specification)
    matches = [p for p in report['policies'] if p['id'] == policy_id]
    if len(matches) != 1:
        raise ValueError('Unknown AA policy')
    policy = matches[0]
    if not policy['prerequisites_closed']:
        raise ValueError('Cannot project a policy with prerequisite gaps')
    caps = {int(a): n for a, n in policy['caps'].items()}
    changes = {table: [] for table in FIELDS}
    for ability in snapshot['abilities']:
        value = ability['enabled'] if ability['id'] in caps else 0
        if value != ability['enabled']:
            changes['aa_ability'].append([ability['id'], ability['enabled'], value])
    original_ranks = {r['id']: r for r in snapshot['ranks']}
    for rank in policy['ranks']:
        if rank['rank'] == caps[rank['ability_id']]:
            original = original_ranks[rank['rank_id']]
            if original['next_id'] != -1:
                changes['aa_ranks'].append([rank['rank_id'], original['next_id'], -1])
    return {'policy': policy_id, 'source_sha256': report['source_sha256'],
            'allowed_rank_ids': policy['allowed_rank_ids'],
            'row_counts': {'aa_ability': len(snapshot['abilities']), 'aa_ranks': len(snapshot['ranks'])},
            'changes': {table: sorted(rows) for table, rows in changes.items()}}


def transaction_sql(plan, database, procedure, restore=False):
    if database != DATABASE or not re.fullmatch(r'[a-z][a-z0-9_]{1,63}', procedure):
        raise ValueError('Only the isolated database and safe procedure names are allowed')
    statements = [
        'DELIMITER //', f'CREATE PROCEDURE `{procedure}`()', 'BEGIN',
        ' DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;',
        ' START TRANSACTION;',
        f" IF DATABASE() <> '{DATABASE}' THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Wrong database'; END IF;",
        " IF EXISTS(SELECT 1 FROM account) OR EXISTS(SELECT 1 FROM character_data) OR EXISTS(SELECT 1 FROM character_alternate_abilities) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Fixture has real ownership rows'; END IF;",
    ]
    for table, field in FIELDS.items():
        count = plan['row_counts'][table]
        if type(count) is not int or count < 1:
            raise ValueError('Invalid original table size')
        statements.append(f" IF (SELECT COUNT(*) FROM `{table}`) <> {count} THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='AA table size changed'; END IF;")
        rows = plan['changes'][table]
        if not rows:
            continue
        if len({r[0] for r in rows}) != len(rows):
            raise ValueError('Duplicate changed row')
        for row in rows:
            if len(row) != 3 or any(type(v) is not int for v in row) or row[0] < 0 or row[1] == row[2]:
                raise ValueError('Invalid projected row')
        pairs = [(rid, after, before) if restore else (rid, before, after) for rid, before, after in rows]
        guard = ','.join(f'({rid},{before})' for rid, before, after in pairs)
        cases = ' '.join(f'WHEN {rid} THEN {after}' for rid, before, after in pairs)
        condition = f'(`id`,`{field}`) IN ({guard})'
        statements.extend([
            f" IF (SELECT COUNT(*) FROM `{table}` WHERE {condition}) <> {len(rows)} THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='AA original values changed'; END IF;",
            f' UPDATE `{table}` SET `{field}`=CASE `id` {cases} ELSE `{field}` END WHERE {condition};',
            f" IF ROW_COUNT() <> {len(rows)} THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='AA update count differs'; END IF;",
        ])
    statements.extend([' COMMIT;', 'END//', f'CALL `{procedure}`()//', f'DROP PROCEDURE `{procedure}`//', 'DELIMITER ;'])
    return '\n'.join(statements) + '\n'
