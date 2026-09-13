"""Capture PoK content read-only and generate guarded forward/rollback SQL.

No command in this tool applies SQL. Run generated files only through the release
procedure after reviewing their preimages and taking a database backup.
"""
import argparse
import copy
import json
from pathlib import Path
import subprocess

from pok_hub import build_plan


OLD_NPCS = [999220,999221,999222,999223,999224,999225,999226,999234,999235,999236,999237,999238,999239]
OLD_MERCHANTS = [99221,99222,99223,99224,99251,99252,99253]
NEW_IDS = range(997900, 997916)
NEW_MERCHANTS = range(99300, 99316)
NPC_SET = ','.join(map(str, OLD_NPCS))
MERCHANT_SET = ','.join(map(str, OLD_MERCHANTS))
SCOPES = {
    'npc_types': f'id IN ({NPC_SET}) OR id BETWEEN 997900 AND 997915 OR merchant_id BETWEEN 99300 AND 99315',
    'spawngroup': f'id IN ({NPC_SET}) OR id BETWEEN 997900 AND 997915 OR name LIKE \'Nightcap_Class_Hub_%\'',
    'spawnentry': f'spawngroupID IN ({NPC_SET}) OR npcID IN ({NPC_SET}) OR spawngroupID BETWEEN 997900 AND 997915 OR npcID BETWEEN 997900 AND 997915',
    'spawn2': f'spawngroupID IN ({NPC_SET}) OR spawngroupID BETWEEN 997900 AND 997915 OR id BETWEEN 997900 AND 997915',
    'merchantlist': f'merchantid IN ({MERCHANT_SET}) OR merchantid BETWEEN 99300 AND 99315',
}
KEYS = {'npc_types': ['id'], 'spawngroup': ['id'], 'spawnentry': ['spawngroupID','npcID'],
        'spawn2': ['id'], 'merchantlist': ['merchantid','slot']}
UTILITIES = [
    (999225, 'Bags & Containers', -337, -232),
    (999226, 'Epic Ascension', -311, -232),
    (999237, 'Blessings', -285, -232),
    (999238, 'Premium Blessings', -259, -232),
    (999239, 'Waypoint Travel', -233, -232),
]


def sql_value(value):
    # Hex strings avoid SQL-mode-dependent quote/backslash handling.
    return 'NULL' if value is None else "CONVERT(X'" + str(value).encode('utf-8').hex() + "' USING utf8mb4)"


def read_sql(query):
    result = subprocess.run(['docker','exec','-i','akk-stack-mariadb-1','mysql',
                             '-ueqemu','-peqemu','peq','--batch','--raw','--skip-column-names'],
                            input=query, text=True, encoding='utf-8', capture_output=True, timeout=90)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return result.stdout


def capture(audit):
    schemas = {}
    queries = ['SET TRANSACTION ISOLATION LEVEL REPEATABLE READ; START TRANSACTION WITH CONSISTENT SNAPSHOT;']
    scopes = {**SCOPES, 'items': 'id IN (' + ','.join(str(i['item_id']) for i in audit['stock']) + ')',
              'rule_values': "ruleset_id=1 AND rule_name IN ('Character:MaxLevel','Expansion:CurrentExpansion')"}
    for table, scope in scopes.items():
        columns = [line.split('\t')[0] for line in read_sql(f'SHOW COLUMNS FROM `{table}`;').splitlines()]
        create = read_sql(f'SHOW CREATE TABLE `{table}`;').split('\t',1)[1].rstrip()
        schemas[table] = {'columns': columns, 'create': create}
        # Preserve native numeric formatting as text for exact drift checks.
        fields = ','.join(sql_value(c) + f',CAST(`{c}` AS CHAR)' for c in columns)
        queries.append(f'SELECT {sql_value(table)},JSON_OBJECT({fields}) FROM `{table}` WHERE {scope};')
    queries.append('ROLLBACK;')
    rows = {table: [] for table in scopes}
    for line in read_sql('\n'.join(queries)).splitlines():
        table, payload = line.split('\t',1)
        rows[table].append(json.loads(payload))
    # Item rows only need the fields whose identity and pricing this change relies on.
    fields = ['id','Name','scrolleffect','itemtype','price']
    rows['items'] = [{k:r[k] for k in fields} for r in rows['items']]
    return {'status':'read_only_preimage', 'schemas':schemas, 'scopes':scopes, 'rows':rows}


def key(table, row):
    return tuple(row[c] for c in KEYS[table])


def assert_original(snapshot, audit):
    rows = snapshot['rows']
    for table in SCOPES:
        if 'ENGINE=InnoDB' not in snapshot['schemas'][table]['create']:
            raise ValueError('Transactional InnoDB tables required')
    if {int(n['id']) for n in rows['npc_types']} != set(OLD_NPCS):
        raise ValueError('Missing source NPC or occupied new NPC/merchant range')
    if any(int(r['id']) in NEW_IDS for r in rows['spawn2']):
        raise ValueError('New spawn IDs occupied')
    if {int(g['id']) for g in rows['spawngroup']} != set(OLD_NPCS):
        raise ValueError('Unexpected source or occupied new spawn groups')
    if len(rows['spawnentry']) != len(OLD_NPCS) or any(
            r['spawngroupID'] != r['npcID'] or int(r['npcID']) not in OLD_NPCS or r['chance'] != '100'
            for r in rows['spawnentry']):
        raise ValueError('Expected exclusively owned, deterministic source spawn groups')
    if any(int(r['merchantid']) in NEW_MERCHANTS for r in rows['merchantlist']):
        raise ValueError('New merchant range occupied')
    expected = {str(i['item_id']):i for i in audit['stock']}
    if {r['item'] for r in rows['merchantlist']} != set(expected):
        raise ValueError('Current merchant stock differs from audited inventory')
    if {i['id'] for i in rows['items']} != set(expected):
        raise ValueError('Audited items missing')
    for item in rows['items']:
        original = expected[item['id']]
        for column, field in [('Name','item_name'),('scrolleffect','spell_id'),('itemtype','item_type'),('price','price')]:
            if item[column] != str(original[field]):
                raise ValueError('Audited item identity or price changed')
    if next(r['rule_value'] for r in rows['rule_values'] if r['rule_name']=='Character:MaxLevel') != '50':
        raise ValueError('This migration was designed for the current level-50 inventory')
    for npc in OLD_NPCS:
        spawns = [r for r in rows['spawn2'] if r['spawngroupID']==str(npc)]
        if len(spawns) != (5 if npc == 999226 else 1):
            raise ValueError('Unexpected source spawn multiplicity')
        if any(r['zone']!='poknowledge' or r['version']!='0' or r['pathgrid']!='0' for r in spawns):
            raise ValueError('Only stationary PoK version-0 source spawns are supported')
        if any({k:v for k,v in r.items() if k!='id'} != {k:v for k,v in spawns[0].items() if k!='id'} for r in spawns):
            raise ValueError('Forgemaster spawns differ beyond their IDs')


def desired(snapshot, audit):
    assert_original(snapshot, audit)
    after = copy.deepcopy(snapshot)
    rows = after['rows']
    plan = build_plan(audit)
    npcs = {int(n['id']):n for n in rows['npc_types']}
    stock = {}
    for row in rows['merchantlist']:
        attributes = {k:v for k,v in row.items() if k not in ('merchantid','slot')}
        if row['item'] in stock and stock[row['item']] != attributes:
            raise ValueError('Conflicting merchant restrictions for one item require review')
        stock[row['item']] = attributes
    for merchant in plan['merchants']:
        new_id = str(merchant['npc_id'])
        template_id = str(merchant['template_npc_id'])
        npc = copy.deepcopy(npcs[int(template_id)])
        npc.update(id=new_id, name=merchant['name'], lastname=merchant['lastname'],
                   merchant_id=str(merchant['merchant_id']), findable='1')
        if npc['class'] != '41' or npc['npc_faction_id'] != '0':
            raise ValueError('Expected the existing factionless merchant template')
        rows['npc_types'].append(npc)
        group = copy.deepcopy(next(g for g in rows['spawngroup'] if g['id']==template_id))
        group.update(id=new_id, name='Nightcap_Class_Hub_' + str(merchant['class_id']))
        rows['spawngroup'].append(group)
        entry = copy.deepcopy(next(e for e in rows['spawnentry'] if e['npcID']==template_id))
        entry.update(spawngroupID=new_id, npcID=new_id)
        rows['spawnentry'].append(entry)
        spawn = copy.deepcopy(next(s for s in rows['spawn2'] if s['spawngroupID']==template_id))
        spawn.update(id=new_id, spawngroupID=new_id, **{k:format(v,'.6f') for k,v in merchant['position'].items()})
        rows['spawn2'].append(spawn)
        for item in merchant['items']:
            rows['merchantlist'].append(dict(stock[str(item['item_id'])], merchantid=str(merchant['merchant_id']), slot=str(item['slot'])))
    retire = set(map(str, plan['retire_vendor_spawn_npc_ids']))
    rows['spawn2'] = [s for s in rows['spawn2'] if s['spawngroupID'] not in retire]
    moves = [(plan['guide']['npc_id'], plan['guide']['lastname'], plan['guide']['position'])]
    moves += [(npc, label, {'x':x,'y':y,'z':-158.875,'heading':0}) for npc,label,x,y in UTILITIES]
    for npc_id, label, position in moves:
        npcs[npc_id].update(lastname=label, findable='1')
        matches = sorted([s for s in rows['spawn2'] if s['spawngroupID']==str(npc_id)], key=lambda r:int(r['id']))
        remove = {s['id'] for s in matches[1:]}
        rows['spawn2'] = [s for s in rows['spawn2'] if s['id'] not in remove]
        matches[0].update({k:format(v,'.6f') for k,v in position.items()})
    after['status'] = 'expected_after_migration_not_applied'
    return after


def predicate(row):
    return ' AND '.join(f'BINARY CAST(`{c}` AS CHAR) <=> BINARY {sql_value(v)}' for c,v in row.items())


def indexed_predicate(table, row):
    columns = KEYS.get(table, ['id'] if table=='items' else ['ruleset_id','rule_name'])
    index = ' AND '.join(f'`{c}` <=> {sql_value(row[c])}' for c in columns)
    return index + ' AND ' + predicate(row)


def insert(table, row):
    return f'INSERT INTO `{table}` (' + ','.join(f'`{c}`' for c in row) + ') VALUES (' + ','.join(sql_value(v) for v in row.values()) + ');'


def patch_sql(before, after):
    statements = []
    for table in SCOPES:
        statements += [f"SELECT COUNT(*) INTO n FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='{table}' AND ENGINE='InnoDB';",
                       f"IF n <> 1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='PoK table must remain InnoDB: {table}'; END IF;",
                       f"SELECT COUNT(*) INTO n FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() AND EVENT_OBJECT_TABLE='{table}';",
                       f"IF n <> 0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Review PoK table triggers: {table}'; END IF;"]
    # Refuse every preimage difference before writing anything. Lock ranges as
    # well as rows so a concurrent insertion cannot sneak past the count checks.
    for table, scope in before['scopes'].items():
        rows = before['rows'][table]
        statements += [f'SELECT COUNT(*) INTO n FROM `{table}` WHERE {scope} FOR UPDATE;',
                       f"IF n <> {len(rows)} THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='PoK preimage count drift: {table}'; END IF;"]
        for row in rows:
            statements += [f'SELECT COUNT(*) INTO n FROM `{table}` WHERE {indexed_predicate(table,row)};',
                           f"IF n <> 1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='PoK preimage row drift: {table}'; END IF;"]
    for table in SCOPES:
        old = {key(table,r):r for r in before['rows'][table]}
        new = {key(table,r):r for r in after['rows'][table]}
        for k, row in old.items():
            if k not in new:
                statements.append(f'DELETE FROM `{table}` WHERE {indexed_predicate(table,{c:row[c] for c in KEYS[table]})};')
            elif row != new[k]:
                changes = ','.join(f'`{c}`={sql_value(v)}' for c,v in new[k].items() if row[c]!=v)
                statements.append(f'UPDATE `{table}` SET {changes} WHERE {indexed_predicate(table,{c:row[c] for c in KEYS[table]})};')
        statements += [insert(table,r) for k,r in new.items() if k not in old]
    return """-- Generated PoK content migration. Review, back up PEQ, then use mysql without --force.
-- No zone restart or quest deployment is performed by this SQL.
DELIMITER //
BEGIN NOT ATOMIC
DECLARE n BIGINT;
DECLARE held INT DEFAULT 0;
DECLARE EXIT HANDLER FOR SQLEXCEPTION
BEGIN
ROLLBACK;
IF held = 1 THEN DO RELEASE_LOCK('nightcap_pok_hub'); END IF;
RESIGNAL;
END;
SELECT GET_LOCK('nightcap_pok_hub', 0) INTO held;
IF held <> 1 OR held IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='PoK content operation already running'; END IF;
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
START TRANSACTION;
""" + '\n'.join(statements) + """
COMMIT;
DO RELEASE_LOCK('nightcap_pok_hub');
END //
DELIMITER ;
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path, required=True)
    parser.add_argument('--capture', action='store_true', help='Read PEQ only; save complete targeted preimages')
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    audit = json.loads(args.audit.read_bytes())
    if args.capture:
        if args.snapshot.exists():
            raise ValueError('Refusing to overwrite a captured preimage')
        args.snapshot.write_bytes((json.dumps(capture(audit), separators=(',',':'))+'\n').encode())
    before = json.loads(args.snapshot.read_bytes())
    after = desired(before, audit)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir/'hub-after.json').write_bytes((json.dumps(after,separators=(',',':'))+'\n').encode())
    for name, first, second in [('hub-forward.sql',before,after),('hub-rollback.sql',after,before)]:
        (args.output_dir/name).write_bytes(patch_sql(first,second).encode())
    print(json.dumps({'status':'generated_not_applied', 'before':{t:len(r) for t,r in before['rows'].items()},
                      'after':{t:len(r) for t,r in after['rows'].items()}}))


if __name__ == '__main__':
    main()
