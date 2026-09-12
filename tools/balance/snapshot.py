"""Freeze non-player PEQ inputs for repeatable Classic balance work."""
import argparse
import gzip
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from baseline import query_json


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
                     'spells_new', 'base_data', 'skill_caps', 'rule_values'}:
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
        'npc_types': ('n', 'n.id IN (32040,73057,64001)'),
        'npc_spells': ('ns', 'ns.id IN (1,25,141)'),
        'npc_spells_entries': ('ne', 'ne.npc_spells_id IN (1,25,141)'),
        'spells_new': ('sp', 'sp.id BETWEEN 1 AND 1200'),
        'base_data': ('b', 'b.level<=55'),
        'skill_caps': ('sc', 'sc.level<=55'),
        'rule_values': ('r', "r.ruleset_id IN (1,2) AND r.rule_name REGEXP '^(Character|Spells|Combat|NPC|Zone|Expansion|AA|Merchant|Aggro):'"),
    }
    selects = []
    for table, (alias, condition) in definitions.items():
        row = row_json(table, alias)
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
    metadata = {
        'captured_at': datetime.now(timezone.utc).isoformat(), 'schema_version': 1,
        'query_sha256': hashlib.sha256(sql.encode()).hexdigest(),
        'scope': 'Unconditional, unflagged Classic version-0 drop pool and its tiers; excludes quests, merchants, global loot, epics, and augments. Spell IDs 1-1200 only; unresolved references must fail validation.',
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
