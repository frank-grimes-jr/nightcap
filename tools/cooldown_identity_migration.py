"""Generate stopped-game cooldown v1 SQL. Never connects to a database.

Input is a fresh SELECT-only catalog (capture schema documented in the release).
Old ambiguous clocks are carried to every possible successor, without shortening
any deadline. Execute using mariadb without --force, with gameplay stopped.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

AA = 0x100000
ITEM = 0x200000
DISC = 0x300000
UNLINKED_DISC = 0x400000


def mappings(catalog):
    ranks = {int(r['id']): r for r in catalog['ranks']}
    pairs = {(14 + i, DISC + i) for i in range(20)}
    for spell in catalog['spells']:
        if int(spell['IsDiscipline']) and int(spell['timer_id']) == -1:
            sid = int(spell['id'])
            if not 0 < sid <= 0xffff:
                raise ValueError('discipline exceeds native spell ID limit')
            pairs.add((13, UNLINKED_DISC + sid))
    for ability in catalog['abilities']:
        aid, rid = int(ability['id']), int(ability['first_rank_id'])
        if not 0 <= aid < 0x100000:
            raise ValueError('AA family exceeds reserved namespace')
        seen = set()
        while rid in ranks:
            if rid in seen:
                raise ValueError('cyclic AA rank chain')
            seen.add(rid)
            rank = ranks[rid]
            group = int(rank['spell_type'])
            if int(rank['spell']) > 0:
                if not 0 <= group < 100:
                    raise ValueError('legacy AA group outside native slots')
                pairs.add((1000 + group, AA + aid))
            rid = int(rank['next_id'])
    items = set()
    for item in catalog['items']:
        if int(item['recasttype']) != -1:
            continue
        iid = int(item['id'])
        if not 0 < iid <= 0xfffff:
            raise ValueError('item exceeds RoF2 item ID limit')
        pairs.add(((-iid) & 0xffff, ITEM + iid))
        items.add(iid)
    return sorted(pairs), sorted(items)


MERGE = '''ON DUPLICATE KEY UPDATE
 duration=GREATEST(timers.start+timers.duration,VALUES(start)+VALUES(duration))-LEAST(timers.start,VALUES(start)),
 start=LEAST(timers.start,VALUES(start)), enable=GREATEST(timers.enable,VALUES(enable));'''


def catalog_guards(catalog):
    statements = []
    specs = [('abilities', 'aa_ability', ['id', 'first_rank_id'], '1'),
             ('ranks', 'aa_ranks', ['id', 'spell', 'spell_type', 'next_id'], '1'),
             ('items', 'items', ['id', 'recasttype', 'clickeffect', 'recastdelay'], 'clickeffect>0 AND recastdelay>0')]
    for key, table, columns, where in specs:
        temp = 'cooldown_expected_' + key
        definitions = ','.join(f'{c} BIGINT NOT NULL' for c in columns)
        values = ','.join('(' + ','.join(str(int(row[c])) for c in columns) + ')'
                          for row in catalog[key])
        mismatch = ' OR '.join(f'e.{c}<>a.{c}' for c in columns)
        statements.extend([
            f'CREATE TEMPORARY TABLE {temp}({definitions},PRIMARY KEY(id));',
            f'INSERT INTO {temp} VALUES {values};' if values else '',
            f'INSERT INTO cooldown_assert SELECT COUNT(*)={len(catalog[key])} FROM {table} WHERE {where};',
            f'INSERT INTO cooldown_assert SELECT COUNT(*)=0 FROM {temp} e LEFT JOIN {table} a ON a.id=e.id WHERE a.id IS NULL OR {mismatch};'])
    unlinked = sorted(int(s['id']) for s in catalog['spells']
                      if int(s['IsDiscipline']) and int(s['timer_id']) == -1)
    allowed = ','.join(map(str, unlinked)) or '0'
    statements.extend([
        f'INSERT INTO cooldown_assert SELECT COUNT(*)={len(unlinked)} FROM spells_new WHERE IsDiscipline<>0 AND EndurTimerIndex=-1;',
        f'INSERT INTO cooldown_assert SELECT COUNT(*)=0 FROM spells_new WHERE IsDiscipline<>0 AND EndurTimerIndex=-1 AND id NOT IN ({allowed});'])
    return '\n'.join(statements)


def sql(catalog, digest, rollback=False):
    pairs, items = mappings(catalog)
    mapping = ',\n'.join(f'({old},{new})' for old, new in pairs)
    prefix = f'''-- Cooldown identity v1; source catalog SHA256 {digest}
-- REQUIRES: stopped gateway/game, fresh stopped backup, exact catalog comparison.
-- Run as one session, without --force. A failed assertion must abort/rollback.
SET SESSION innodb_lock_wait_timeout=10;
CREATE TABLE IF NOT EXISTS nightcap_cooldown_schema (
 id TINYINT UNSIGNED PRIMARY KEY, version INT UNSIGNED NOT NULL,
 catalog_sha256 CHAR(64) NOT NULL) ENGINE=InnoDB;
CREATE TEMPORARY TABLE cooldown_map(old_type INT UNSIGNED,new_type INT UNSIGNED,
 PRIMARY KEY(old_type,new_type));
INSERT INTO cooldown_map VALUES {mapping};
CREATE TEMPORARY TABLE cooldown_assert(ok INT NOT NULL CHECK(ok=1));
INSERT INTO cooldown_assert SELECT COUNT(*)=3 FROM information_schema.TABLES
 WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME IN ('timers','character_item_recast','nightcap_cooldown_schema') AND ENGINE='InnoDB';
INSERT INTO cooldown_assert SELECT COUNT(*)=1 FROM information_schema.STATISTICS
 WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='nightcap_cooldown_schema' AND INDEX_NAME='PRIMARY' AND COLUMN_NAME='id';
INSERT INTO cooldown_assert SELECT COUNT(*)=1 FROM information_schema.COLUMNS
 WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='timers' AND COLUMN_NAME='type'
 AND DATA_TYPE='mediumint' AND COLUMN_TYPE LIKE '%unsigned%';
INSERT INTO cooldown_assert SELECT COUNT(*)=0 FROM information_schema.TRIGGERS
 WHERE TRIGGER_SCHEMA=DATABASE() AND EVENT_OBJECT_TABLE IN
 ('timers','nightcap_cooldown_schema','nightcap_cooldown_backup_v1','nightcap_cooldown_rollback_v1');
{catalog_guards(catalog)}
'''
    if rollback:
        return prefix + f'''
CREATE TABLE IF NOT EXISTS nightcap_cooldown_rollback_v1 LIKE timers;
{backup_guard('nightcap_cooldown_rollback_v1')}
START TRANSACTION;
INSERT INTO cooldown_assert SELECT COUNT(*)=1 FROM nightcap_cooldown_schema
 WHERE id=1 AND version=1 AND catalog_sha256='{digest}';
INSERT INTO cooldown_assert SELECT COUNT(*)=0 FROM nightcap_cooldown_rollback_v1;
INSERT INTO nightcap_cooldown_rollback_v1 SELECT * FROM timers;
-- Every new key must be representable before exposing the old uint16 loader.
INSERT INTO cooldown_assert SELECT COUNT(*)=0 FROM timers t
 WHERE t.type>=1048576 AND NOT EXISTS(SELECT 1 FROM cooldown_map m WHERE m.new_type=t.type);
INSERT INTO timers(char_id,type,start,duration,enable)
 SELECT t.char_id,m.old_type,t.start,t.duration,t.enable
 FROM nightcap_cooldown_rollback_v1 t JOIN cooldown_map m ON m.new_type=t.type
 WHERE t.enable=1 AND t.start+t.duration>UNIX_TIMESTAMP()
{MERGE}
DELETE FROM timers WHERE type>=1048576;
DELETE FROM nightcap_cooldown_schema WHERE id=1;
COMMIT;
'''
    item_values = ','.join(f'({iid},{ITEM+iid})' for iid in items)
    return prefix + f'''
CREATE TABLE IF NOT EXISTS nightcap_cooldown_backup_v1 LIKE timers;
{backup_guard('nightcap_cooldown_backup_v1')}
CREATE TEMPORARY TABLE cooldown_items(item_id INT UNSIGNED PRIMARY KEY,new_type INT UNSIGNED);
INSERT INTO cooldown_items VALUES {item_values};
START TRANSACTION;
INSERT INTO cooldown_assert SELECT COUNT(*)=0 FROM nightcap_cooldown_schema;
INSERT INTO cooldown_assert SELECT COUNT(*)=0 FROM nightcap_cooldown_backup_v1;
INSERT INTO nightcap_cooldown_backup_v1 SELECT * FROM timers;
INSERT INTO timers(char_id,type,start,duration,enable)
 SELECT t.char_id,m.new_type,t.start,t.duration,t.enable
 FROM nightcap_cooldown_backup_v1 t JOIN cooldown_map m ON m.old_type=t.type
 WHERE t.enable=1 AND t.start+t.duration>UNIX_TIMESTAMP()
{MERGE}
-- Item timestamp persistence can lead the periodic PTimerList save.
INSERT INTO timers(char_id,type,start,duration,enable)
 SELECT r.id,m.new_type,UNIX_TIMESTAMP(),r.timestamp-UNIX_TIMESTAMP(),1
 FROM character_item_recast r JOIN cooldown_items m ON m.item_id=r.recast_type
 WHERE r.timestamp>UNIX_TIMESTAMP()
{MERGE}
INSERT INTO nightcap_cooldown_schema VALUES(1,1,'{digest}');
COMMIT;
'''


def backup_guard(table):
    return f'''INSERT INTO cooldown_assert SELECT COUNT(*)=1 FROM information_schema.TABLES
 WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='{table}' AND ENGINE='InnoDB';
INSERT INTO cooldown_assert SELECT COUNT(*)=5 FROM information_schema.COLUMNS
 WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='{table}';
INSERT INTO cooldown_assert SELECT COUNT(*)=0 FROM information_schema.COLUMNS t
 LEFT JOIN information_schema.COLUMNS b ON b.TABLE_SCHEMA=t.TABLE_SCHEMA
 AND b.TABLE_NAME='{table}' AND b.COLUMN_NAME=t.COLUMN_NAME
 WHERE t.TABLE_SCHEMA=DATABASE() AND t.TABLE_NAME='timers' AND
 (b.COLUMN_NAME IS NULL OR b.COLUMN_TYPE<>t.COLUMN_TYPE OR b.COLUMN_KEY<>t.COLUMN_KEY
 OR b.IS_NULLABLE<>t.IS_NULLABLE OR b.ORDINAL_POSITION<>t.ORDINAL_POSITION);'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('catalog', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    data = gzip.decompress(args.catalog.read_bytes()) if args.catalog.suffix == '.gz' else args.catalog.read_bytes()
    catalog = json.loads(data)
    digest = hashlib.sha256(data).hexdigest()
    args.output.mkdir(parents=True, exist_ok=True)
    for name, rollback in [('forward.sql', False), ('rollback.sql', True)]:
        (args.output/name).write_text(sql(catalog, digest, rollback), encoding='utf-8')
    pairs, items = mappings(catalog)
    print(json.dumps({'mapping_pairs': len(pairs), 'unlinked_items': len(items),
                      'catalog_sha256': digest, 'status': 'generated_not_applied'}))


if __name__ == '__main__':
    main()
