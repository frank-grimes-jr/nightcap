"""Shared guarded snapshot and atomic SQL mechanics for scoped content releases."""
import json
from pok_hub_migration import sql_value, predicate, insert

def capture(query, scopes):
    schemas={};statements=['SET TRANSACTION ISOLATION LEVEL REPEATABLE READ; START TRANSACTION WITH CONSISTENT SNAPSHOT;']
    for table,scope in scopes.items():
        columns=[s.split('\t')[0] for s in query(f'SHOW COLUMNS FROM `{table}`;').splitlines()]
        schemas[table]={'create':query(f'SHOW CREATE TABLE `{table}`;').split('\t',1)[1].rstrip()}
        fields=','.join(sql_value(c)+f',CAST(`{c}` AS CHAR)' for c in columns)
        statements.append(f'SELECT {sql_value(table)},JSON_OBJECT({fields}) FROM `{table}` WHERE {scope};')
    statements.append('ROLLBACK;');rows={t:[] for t in scopes}
    for line in query('\n'.join(statements)).splitlines():
        table,data=line.split('\t',1);rows[table].append(json.loads(data))
    return dict(schemas=schemas,scopes=scopes,rows=rows)

def indexed(table,row,keys):
    return ' AND '.join(f'`{k}` <=> {sql_value(row[k])}' for k in keys[table])+' AND '+predicate(row)

def patch_sql(before,after,keys,scopes):
    statements=[]
    for table in keys:
        statements += [f"SELECT COUNT(*) INTO n FROM information_schema.TABLES WHERE TABLE_SCHEMA=DATABASE() AND TABLE_NAME='{table}' AND ENGINE='InnoDB';",
            f"IF n<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Court engine drift: {table}'; END IF;",
            f"SELECT COUNT(*) INTO n FROM information_schema.TRIGGERS WHERE TRIGGER_SCHEMA=DATABASE() AND EVENT_OBJECT_TABLE='{table}';",
            f"IF n<>0 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Court trigger drift: {table}'; END IF;",
            f'SELECT COUNT(*) INTO n FROM `{table}` WHERE {scopes[table]} FOR UPDATE;',
            f"IF n<>{len(before['rows'][table])} THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Court count drift: {table}'; END IF;"]
        for row in before['rows'][table]:
            statements += [f'SELECT COUNT(*) INTO n FROM `{table}` WHERE {indexed(table,row,keys)};',
                f"IF n<>1 THEN SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='Court row drift: {table}'; END IF;"]
    for table,columns in keys.items():
        old={tuple(r[k] for k in columns):r for r in before['rows'][table]}
        new={tuple(r[k] for k in columns):r for r in after['rows'][table]}
        for key,row in old.items():
            if key not in new:statements.append(f'DELETE FROM `{table}` WHERE {indexed(table,row,keys)};')
            elif row!=new[key]:
                changes=','.join(f'`{k}`={sql_value(v)}' for k,v in new[key].items() if row[k]!=v)
                statements.append(f'UPDATE `{table}` SET {changes} WHERE {indexed(table,row,keys)};')
        statements += [insert(table,row) for key,row in new.items() if key not in old]
    return ('-- Stop the target zone, back up and capture fresh preimages before applying.\n'
        'DELIMITER //\nBEGIN NOT ATOMIC\nDECLARE n BIGINT;\n'
        'DECLARE EXIT HANDLER FOR SQLEXCEPTION BEGIN ROLLBACK; RESIGNAL; END;\n'
        'SET TRANSACTION ISOLATION LEVEL SERIALIZABLE;\nSTART TRANSACTION;\n'+
        '\n'.join(statements)+'\nCOMMIT;\nEND //\nDELIMITER ;\n')

