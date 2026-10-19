"""Guarded content-only row-group migrations. Never writes character state."""
from rabid_bear import sql_value


def predicate(row):
    # Item/spell names and descriptions are exact preimages, including case.
    return ' AND '.join(('BINARY ' if isinstance(v,str) else '')+'`'+k+'` <=> '+
                        ('BINARY ' if isinstance(v,str) else '')+sql_value(v) for k,v in row.items())


def insert(table, row):
    return 'INSERT INTO '+table+' ('+','.join('`'+k+'`' for k in row)+') VALUES ('+','.join(sql_value(v) for v in row.values())+');'


def equal_group(table, key, rows):
    matches = ' OR '.join('('+predicate(r)+')' for r in rows) or 'FALSE'
    return (f'(SELECT COUNT(*) FROM {table} WHERE {predicate(key)})={len(rows)} AND '
            f'NOT EXISTS (SELECT 1 FROM {table} WHERE {predicate(key)} AND NOT ({matches}))')


def migration(groups, name):
    """Each group owns one indexed key and all of its child rows, if any."""
    lines=['DELIMITER //', f'CREATE PROCEDURE {name}()', 'BEGIN',
           ' DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;',
           ' SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;', ' START TRANSACTION;']
    for table in sorted({g['table'] for g in groups}):
        lines.append(f" IF (SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='{table}' AND ENGINE='InnoDB')<>1 OR EXISTS (SELECT 1 FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() AND EVENT_OBJECT_TABLE='{table}') THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Unexpected WPM content storage'; END IF;")
    for g in groups:
        table,key,before,after=(g[k] for k in ('table','key','before','after'))
        lines += [f' IF NOT ({equal_group(table,key,after)}) THEN',
                  f"  IF NOT ({equal_group(table,key,before)}) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='WPM {table} preimage drift'; END IF;"]
        if len(before)==len(after)==1 and all(before[0].get(k)==v for k,v in key.items()):
            changes={k:v for k,v in after[0].items() if before[0].get(k)!=v}
            if changes:
                lines.append(f'  UPDATE {table} SET '+','.join('`'+k+'`='+sql_value(v) for k,v in changes.items())+' WHERE '+predicate(key)+';')
        else:
            if before: lines.append('  DELETE FROM '+table+' WHERE '+predicate(key)+';')
            lines += ['  '+insert(table,row) for row in after]
        lines += [f"  IF NOT ({equal_group(table,key,after)}) THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='WPM {table} afterimage mismatch'; END IF;", ' END IF;']
    lines += [' COMMIT;','END//','DELIMITER ;',f'CALL {name}();',f'DROP PROCEDURE {name};','']
    return '\n'.join(lines)
