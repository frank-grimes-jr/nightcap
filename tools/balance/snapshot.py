"""Freeze non-player PEQ inputs for repeatable Classic balance work."""
import argparse
import gzip
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from baseline import query_json

ITEM_SPELL_FIELDS = ('clickeffect', 'worneffect', 'proceffect', 'focuseffect', 'scrolleffect', 'bardeffect')
NPC_IDS = '32040,73057,64001'
NPC_LISTS = f'SELECT npc_spells_id FROM npc_types WHERE id IN ({NPC_IDS})'
NPC_LISTS_WITH_PARENTS = f'{NPC_LISTS} UNION SELECT parent_list FROM npc_spells WHERE id IN ({NPC_LISTS})'


def validate_spell_references(tables):
    if 'npc_types' in tables:
        lists={s['id']:s for s in tables['npc_spells']}
        for npc in tables['npc_types']:
            list_id=npc['npc_spells_id']
            if list_id and (list_id not in lists or (lists[list_id]['parent_list'] and lists[list_id]['parent_list'] not in lists)):
                raise ValueError(f'Missing spell-list dependency for NPC {npc["id"]}')
    available = {s['id'] for s in tables['spells_new']}
    referenced = {r['spellid'] for r in tables['npc_spells_entries']}
    referenced.update(s.get('RecourseLink', 0) for s in tables['spells_new'])
    for item in tables['items']:
        item = {k.lower():v for k,v in item.items()}
        referenced.update(item.get(field, 0) for field in ITEM_SPELL_FIELDS)
    missing = {s for s in referenced if s and 0 < s < 65535} - available
    if missing:
        raise ValueError(f'Missing referenced spell rows: {sorted(missing)}')


def era_predicate(alias):
    if not re.fullmatch(r'[a-z]+', alias):
        raise ValueError('Invalid SQL alias')
    return (f'({alias}.min_expansion=-1 OR {alias}.min_expansion=0) '
            f'AND ({alias}.max_expansion=-1 OR {alias}.max_expansion>=0) '
            f"AND COALESCE({alias}.content_flags,'')='' "
            f"AND COALESCE({alias}.content_flags_disabled,'')=''")


DROP_SOURCES = f"""SELECT DISTINCT ld.item_id, z.short_name AS zone, n.id AS npc_id,
n.name AS npc_name, n.level AS npc_level
FROM zone z JOIN spawn2 s ON s.zone=z.short_name AND s.version=z.version
JOIN spawnentry se ON se.spawngroupID=s.spawngroupID
JOIN npc_types n ON n.id=se.npcID
JOIN loottable l ON l.id=n.loottable_id
JOIN loottable_entries lt ON lt.loottable_id=l.id
JOIN lootdrop d ON d.id=lt.lootdrop_id
JOIN lootdrop_entries ld ON ld.lootdrop_id=lt.lootdrop_id
WHERE z.expansion=0 AND z.version=0 AND s._condition=0
AND NOT EXISTS (SELECT 1 FROM spawn2_disabled sd WHERE sd.spawn2_id=s.id AND sd.instance_id=0 AND sd.disabled<>0)
AND se.chance>0 AND lt.probability>0 AND lt.multiplier>0
AND ld.chance>0 AND ld.multiplier>0 AND ld.item_id BETWEEN 1 AND 199999
AND (ld.npc_min_level=0 OR n.level>=ld.npc_min_level)
AND (ld.npc_max_level=0 OR n.level<=ld.npc_max_level)
AND {era_predicate('s')} AND {era_predicate('se')} AND {era_predicate('ld')}
AND {era_predicate('l')} AND {era_predicate('d')}"""


def row_json(table, alias):
    # Only hardcoded content tables reach this function, never arbitrary user SQL.
    if table not in {'items', 'npc_types', 'npc_spells', 'npc_spells_entries',
                     'spells_new', 'base_data', 'skill_caps', 'rule_values',
                     'char_create_combinations', 'char_create_point_allocations'}:
        raise ValueError('Unsupported snapshot table')
    if table == 'rule_values':
        return f"JSON_OBJECT('ruleset_id',{alias}.ruleset_id,'rule_name',{alias}.rule_name,'rule_value',{alias}.rule_value)"
    columns = query_json("SELECT JSON_OBJECT('name',COLUMN_NAME) FROM information_schema.COLUMNS "
                         f"WHERE TABLE_SCHEMA='peq' AND TABLE_NAME='{table}' ORDER BY ORDINAL_POSITION")
    if not columns or any(not re.fullmatch(r'\w+', row['name']) for row in columns):
        raise ValueError('Unexpected table schema')
    return 'JSON_OBJECT(' + ','.join(f"'{row['name']}',{alias}.`{row['name']}`" for row in columns) + ')'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    eligible = f'SELECT item_id FROM ({DROP_SOURCES}) drop_sources'
    definitions = {
        'items': ('i', f'i.id<800000 AND i.slots>0 AND MOD(i.id,200000) IN ({eligible})'),
        'npc_types': ('n', f'n.id IN ({NPC_IDS})'),
        'npc_spells': ('ns', f'ns.id IN ({NPC_LISTS_WITH_PARENTS})'),
        'npc_spells_entries': ('ne', f'ne.npc_spells_id IN ({NPC_LISTS_WITH_PARENTS})'),
        'spells_new': ('sp', 'sp.id BETWEEN 1 AND 1200'),
        'base_data': ('b', 'b.level<=55'),
        'skill_caps': ('sc', 'sc.level<=55'),
        'char_create_combinations': ('cc', 'cc.race=1'),
        'char_create_point_allocations': ('ca', 'ca.id IN (SELECT allocation_id FROM char_create_combinations WHERE race=1)'),
        'rule_values': ('r', "r.ruleset_id IN (1,2) AND r.rule_name REGEXP '^(Character|Spells|Combat|NPC|Zone|Expansion|AA|Merchant|Aggro):'"),
    }
    selects = []
    for table, (alias, condition) in definitions.items():
        row = row_json(table, alias)
        if table == 'spells_new':
            item_refs = ' UNION '.join(f'SELECT {field} FROM eligible_items' for field in ITEM_SPELL_FIELDS)
            selects.append(f"""WITH RECURSIVE eligible_items AS (
SELECT i.* FROM items i WHERE {definitions['items'][1]}),
initial_refs(id) AS (SELECT id FROM spells_new WHERE id BETWEEN 1 AND 1200
UNION SELECT spellid FROM npc_spells_entries WHERE npc_spells_id IN ({NPC_LISTS_WITH_PARENTS})
UNION {item_refs}), spell_refs(id) AS (
SELECT id FROM initial_refs WHERE id>0 AND id<65535
UNION SELECT s.RecourseLink FROM spells_new s JOIN spell_refs r ON s.id=r.id
WHERE s.RecourseLink>0 AND s.RecourseLink<65535)
SELECT JSON_OBJECT('table','spells_new','row',{row}) FROM spells_new sp
WHERE sp.id IN (SELECT id FROM spell_refs)""")
        else:
            selects.append(f"SELECT JSON_OBJECT('table','{table}','row',{row}) FROM {table} {alias} WHERE {condition}")
    selects.append("SELECT JSON_OBJECT('table','drop_sources','row',"
                   "JSON_OBJECT('item_id',item_id,'zone',zone,'npc_id',npc_id,'npc_name',npc_name,'npc_level',npc_level)) "
                   f"FROM ({DROP_SOURCES}) sources ORDER BY item_id,zone,npc_id")
    sql = ';\n'.join(selects)
    rows = query_json(sql)  # One read-only transaction for all content rows.
    tables = {key: [] for key in (*definitions, 'drop_sources')}
    for row in rows:
        tables[row['table']].append(row['row'])
    for table in tables.values():
        table.sort(key=lambda row: json.dumps(row, sort_keys=True))
    if len(tables['npc_types']) != 3 or not tables['items']:
        raise ValueError('Incomplete content export')
    validate_spell_references(tables)
    metadata = {
        'captured_at': datetime.now(timezone.utc).isoformat(), 'schema_version': 1,
        'query_sha256': hashlib.sha256(sql.encode()).hexdigest(),
        'scope': 'Unconditional, unflagged Classic version-0 drop pool and its tiers; excludes quests, merchants, global loot, epics, and augments. Spells include IDs 1-1200, all captured NPC/item references, and recursive recourse links; Human creation allocations included.',
        'rows': {name: len(value) for name, value in tables.items()},
    }
    payload = json.dumps({'metadata': metadata, 'tables': tables}, separators=(',', ':')).encode()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(gzip.compress(payload, mtime=0))
    metadata['snapshot_sha256'] = hashlib.sha256(args.output.read_bytes()).hexdigest()
    args.output.with_suffix('.manifest.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    args.output.with_suffix('.queries.sql').write_text(sql + ';\n', encoding='utf-8')
    print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
