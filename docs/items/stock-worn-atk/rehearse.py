"""Rehearse forward/replay/rollback and reject drift on a throwaway MariaDB clone."""
import gzip
import json
import subprocess
import uuid
from pathlib import Path
from plan import HERE, plan
from rabid_bear import sql_value

def main():
    db='nightcap_stock_atk_'+uuid.uuid4().hex
    def sql(query, database=db, check=True):
        cmd=['docker','exec','-i','akk-stack-mariadb-1','sh','-c',
             'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" exec mariadb -uroot --default-character-set=utf8mb4 -NB '+database]
        proc=subprocess.run(cmd,input=query.encode(),capture_output=True)
        if check and proc.returncode:raise RuntimeError(proc.stderr.decode(errors='replace')[-1500:])
        return proc

    data=json.loads(gzip.decompress((HERE/'production-items.json.gz').read_bytes()))
    columns=data['columns'];changes, guards, _=plan(data)
    pk=lambda row:int(row['id'])
    before={pk(row):row for row in data['rows']}
    after={**before,**{pk(row):row for _,row in changes}}
    def all_rows():
        fields=','.join('CAST(`'+c+'` AS CHAR)' for c in columns)
        lines=sql('SELECT JSON_ARRAY('+fields+') FROM items ORDER BY id;').stdout.decode().splitlines()
        rows=[dict(zip(columns,json.loads(line),strict=True)) for line in lines]
        return {pk(row):row for row in rows}
    sql('CREATE DATABASE '+db,'information_schema')
    try:
        sql('CREATE TABLE items LIKE peq.items')
        fields=','.join('`'+c+'`' for c in columns)
        for i in range(0,len(data['rows']),40):
            values=','.join('('+','.join(sql_value(row[c]) for c in columns)+')' for row in data['rows'][i:i+40])
            sql('INSERT INTO items ('+fields+') VALUES '+values)
        assert all_rows()==before
        forward=gzip.decompress((HERE/'forward.sql.gz').read_bytes()).decode()
        rollback=gzip.decompress((HERE/'rollback.sql.gz').read_bytes()).decode()
        for query,expect in ((forward,after),(forward,after),(rollback,before),(rollback,before)):
            sql(query)
            assert all_rows()==expect
        for row,field in ((guards[-1],'astr'),(changes[-1][0],'augslot1type')):
            ident=pk(row)
            sql(f'UPDATE items SET {field}={field}+1 WHERE id={ident}')
            drifted=all_rows()
            result=sql(forward,check=False)
            assert result.returncode and b'preimage drift' in result.stderr and all_rows()==drifted
            sql(f'UPDATE items SET {field}={field}-1 WHERE id={ident}')
        assert all_rows()==before
        print(f'PASS: {len(changes)} ATK-only updates, {len(guards)} locked Normals, {len(before)} complete rows; forward, replay, rollback, inverse replay, Normal/socket drift refusal.')
    finally:
        sql('DROP DATABASE '+db,'information_schema')

if __name__=='__main__':main()
