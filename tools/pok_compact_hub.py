"""Read-only capture and guarded SQL generation for the compact PoK hub.

This does not apply SQL or touch the original client. Stop PoK before capture
and apply; its saved-state shutdown can otherwise race the migration.
"""
import argparse
import copy
import json
import math
import struct
from pathlib import Path
from pok_hub_migration import read_sql, sql_value, predicate

ARRIVAL = (-285, -148)
MODELS = {
    407: {'name':'Lightning Warrior', 'model':'mur', 'archive':'mur.eqg'},
    411: {'name':'Pyrilen', 'model':'scu', 'archive':'scu.eqg'},
    417: {'name':'Gelidran', 'model':'frd', 'archive':'frd.eqg'},
    419: {'name':'Girplan', 'model':'ddv', 'archive':'ddv.eqg'},
    495: {'name':'Scrykin', 'model':'srn', 'archive':'srn.eqg'},
}
VISUAL_FIELDS = {'race','gender','size','texture','helmtexture','face'}
PLAN = {}
for index in range(16):
    class_id = index + 1
    race = 417 if class_id in (2,6,10) else 411 if class_id in (11,12,13,14) else 419 if class_id == 15 else 407
    PLAN[997900+index] = {'x':-321+(index%4)*24, 'y':-184+(index//4)*24, 'race':race, 'size':5.5}
PLAN[999220] = {'x':-285, 'y':-124, 'race':495, 'size':6}
for index, npc in enumerate((999225,999226,999237,999238,999239)):
    PLAN[npc] = {'x':-321+index*18, 'y':-205, 'race':(419,411,417,495,407)[index], 'size':5.5}

KEYS = {'npc_types':['id'], 'spawn2':['id'], 'spawngroup':['id'],
        'spawnentry':['spawngroupID','npcID'], 'merchantlist':['merchantid','slot'], 'zone_state_spawns':['id']}
MUTABLE = ('npc_types','spawn2','zone_state_spawns')


def scopes():
    ids = ','.join(map(str, sorted(PLAN)))
    return {'npc_types':f'id IN ({ids})', 'spawn2':f'spawngroupID IN ({ids})',
            'spawngroup':f'id IN ({ids})', 'spawnentry':f'spawngroupID IN ({ids}) OR npcID IN ({ids})',
            'merchantlist':'merchantid IN (SELECT merchant_id FROM npc_types WHERE id IN ('+ids+') AND merchant_id<>0)',
            'zone_state_spawns':f'zone_id=202 AND instance_id=0 AND is_corpse=0 AND (npc_id IN ({ids}) OR spawngroup_id IN ({ids}) OR spawn2_id IN (SELECT id FROM spawn2 WHERE spawngroupID IN ({ids})))'}


def capture():
    scope = scopes()
    schemas, queries = {}, ['SET TRANSACTION ISOLATION LEVEL REPEATABLE READ; START TRANSACTION WITH CONSISTENT SNAPSHOT;']
    for table, where in scope.items():
        columns = [row.split('\t')[0] for row in read_sql(f'SHOW COLUMNS FROM `{table}`;').splitlines()]
        create = read_sql(f'SHOW CREATE TABLE `{table}`;').split('\t',1)[1].rstrip()
        schemas[table] = {'columns':columns, 'create':create}
        fields = ','.join(sql_value(c)+f',CAST(`{c}` AS CHAR)' for c in columns)
        queries.append(f'SELECT {sql_value(table)},JSON_OBJECT({fields}) FROM `{table}` WHERE {where};')
    queries.append('ROLLBACK;')
    rows = {table:[] for table in scope}
    for line in read_sql('\n'.join(queries)).splitlines():
        table, payload = line.split('\t',1)
        rows[table].append(json.loads(payload))
    return {'status':'read_only_preimage','schemas':schemas,'scopes':scope,'rows':rows}


def desired(before):
    rows = before['rows']
    ids = set(PLAN)
    for table in KEYS:
        if 'ENGINE=InnoDB' not in before['schemas'][table]['create']:
            raise ValueError('Transactional InnoDB tables required')
    if {int(r['id']) for r in rows['npc_types']} != ids or len(rows['npc_types']) != len(ids):
        raise ValueError('Missing or extra hub NPC')
    if len(rows['spawngroup']) != len(ids) or {int(r['id']) for r in rows['spawngroup']} != ids:
        raise ValueError('Missing or extra hub spawn group')
    if len(rows['spawnentry']) != len(ids) or any(r['spawngroupID'] != r['npcID'] or r['chance'] != '100' or int(r['npcID']) not in ids for r in rows['spawnentry']):
        raise ValueError('Hub groups must exclusively spawn their expected NPC')
    if len(rows['spawn2']) != len(ids) or {int(r['spawngroupID']) for r in rows['spawn2']} != ids or any(
            r['zone'] != 'poknowledge' or r['version'] != '0' or r['pathgrid'] != '0' for r in rows['spawn2']):
        raise ValueError('Expected one stationary PoK version-0 spawn per service')
    for state in rows['zone_state_spawns']:
        if state['zone_id'] != '202' or state['instance_id'] != '0' or state['is_corpse'] != '0':
            raise ValueError('Saved-state scope includes an unrelated instance or corpse')
    after = copy.deepcopy(before)
    for npc in after['rows']['npc_types']:
        plan = PLAN[int(npc['id'])]
        npc.update(race=str(plan['race']), gender='2', size=str(plan['size']), texture='0', helmtexture='0', face='0')
    for spawn in after['rows']['spawn2']:
        plan = PLAN[int(spawn['spawngroupID'])]
        heading = math.atan2(ARRIVAL[0]-plan['x'], ARRIVAL[1]-plan['y']) * 512/(2*math.pi) % 512
        # spawn2.heading is FLOAT(14,6): match MariaDB's float32 storage before
        # serializing the rollback preimage. Double precision decimals drift.
        heading = struct.unpack('f', struct.pack('f', heading))[0]
        spawn.update(x=f"{plan['x']:.6f}", y=f"{plan['y']:.6f}", z='-158.875000', heading=f'{heading:.6f}')
    after['rows']['zone_state_spawns'] = []
    after['status'] = 'expected_after_not_applied'
    return after


def row_key(table, row):
    return tuple(row[k] for k in KEYS[table])


def where_row(table, row):
    index = ' AND '.join(f'`{k}` <=> {sql_value(row[k])}' for k in KEYS[table])
    return index+' AND '+predicate(row)


def patch_sql(before, after):
    statements = []
    for table in KEYS:
        statements += [f"SELECT COUNT(*) INTO n FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='{table}' AND ENGINE='InnoDB';",
                       f"IF n<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Hub table engine changed: {table}'; END IF;",
                       f"SELECT COUNT(*) INTO n FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() AND EVENT_OBJECT_TABLE='{table}';",
                       f"IF n<>0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Review hub table triggers: {table}'; END IF;"]
    for table, where in before['scopes'].items():
        rows = before['rows'][table]
        statements += [f'SELECT COUNT(*) INTO n FROM `{table}` WHERE {where} FOR UPDATE;',
                       f"IF n<>{len(rows)} THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Hub preimage count drift: {table}'; END IF;"]
        for row in rows:
            statements += [f'SELECT COUNT(*) INTO n FROM `{table}` WHERE {where_row(table,row)};',
                           f"IF n<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Hub preimage row drift: {table}'; END IF;"]
    for table in MUTABLE:
        old = {row_key(table,r):r for r in before['rows'][table]}
        new = {row_key(table,r):r for r in after['rows'][table]}
        if set(new)-set(old):
            raise ValueError('Never insert new NPCs or restore stale saved-state rows')
        for key, row in old.items():
            if key not in new:
                if table != 'zone_state_spawns': raise ValueError('Only affected saved states may be deleted')
                statements.append(f'DELETE FROM `{table}` WHERE {where_row(table,row)};')
            elif row != new[key]:
                changes = {k:v for k,v in new[key].items() if row[k] != v}
                allowed = VISUAL_FIELDS if table == 'npc_types' else {'x','y','z','heading'}
                if not changes.keys() <= allowed: raise ValueError('Unexpected hub mutation')
                assignments = ','.join(f'`{k}`={sql_value(v)}' for k,v in changes.items())
                statements.append(f'UPDATE `{table}` SET {assignments} WHERE {where_row(table,row)};')
    return """-- Generated from fresh preimages. Stop PoK, back up PEQ, then apply without --force.
-- Saved-state rows are invalidated only in zone 202 / instance 0 / non-corpses.
DELIMITER //
BEGIN NOT ATOMIC
DECLARE n BIGINT;
DECLARE held INT DEFAULT 0;
DECLARE EXIT HANDLER FOR SQLEXCEPTION
BEGIN
ROLLBACK;
IF held=1 THEN DO RELEASE_LOCK('nightcap_pok_hub'); END IF;
RESIGNAL;
END;
SELECT GET_LOCK('nightcap_pok_hub',0) INTO held;
IF held<>1 OR held IS NULL THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Hub operation already running'; END IF;
SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;
START TRANSACTION;
"""+'\n'.join(statements)+"\nCOMMIT;\nDO RELEASE_LOCK('nightcap_pok_hub');\nEND //\nDELIMITER ;\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--capture', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists(): raise ValueError('Refusing to overwrite an existing generation')
    if args.capture:
        if args.before.exists(): raise ValueError('Refusing to overwrite captured preimages')
        args.before.parent.mkdir(parents=True, exist_ok=True)
        args.before.write_text(json.dumps(capture(), separators=(',',':'))+'\n')
    before = json.loads(args.before.read_bytes())
    after = desired(before)
    rollback = copy.deepcopy(before)
    rollback['rows']['zone_state_spawns'] = []
    args.output.mkdir(parents=True)
    (args.output/'forward.sql').write_text(patch_sql(before,after))
    (args.output/'rollback.sql').write_text(patch_sql(after,rollback))
    (args.output/'after.json').write_text(json.dumps(after,separators=(',',':'))+'\n')
    (args.output/'layout.json').write_text(json.dumps({'arrival':ARRIVAL,'plan':PLAN,'models':MODELS},indent=2)+'\n')
    print(json.dumps({'status':'generated_not_applied','services':len(PLAN),'saved_states_invalidated':len(before['rows']['zone_state_spawns'])}))


if __name__ == '__main__': main()
