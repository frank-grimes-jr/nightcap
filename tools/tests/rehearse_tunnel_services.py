"""Rehearse exact forward/rollback against an isolated disposable MariaDB schema."""
import argparse
import hashlib
import json
from pathlib import Path
import secrets
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tunnel_services import desired, plan, patch_sql, rollback_target, indexed_predicate, KEYS
from generate_living_economy import insert
from pok_hub_migration import sql_value


def run(source,container,evidence):
    before=json.loads(source.read_bytes());layout=plan(before['source']);after=desired(before,layout)
    schema='nightcap_tunnel_test_'+secrets.token_hex(5)
    checks=[];created=False
    def sql(text,check=True,use=True):
        r=subprocess.run(['docker','exec','-i',container,'sh','-c',
            'MYSQL_PWD="${MARIADB_ROOT_PASSWORD:-$MYSQL_ROOT_PASSWORD}" exec mariadb -uroot --batch --raw --skip-column-names'],input=(f'USE {schema};\n' if use else '')+text,
            text=True,encoding='utf-8',capture_output=True,timeout=120)
        if check and r.returncode:raise RuntimeError(r.stderr[-2500:])
        return r
    def verify(ok,label):
        if not ok:raise AssertionError(label)
        checks.append(label)
    def fingerprint():
        text='\n'.join(f'SELECT * FROM {t} ORDER BY '+','.join(k)+';' for t,k in KEYS.items())
        return hashlib.sha256(sql(text).stdout.encode()).hexdigest()
    try:
        sql(f'CREATE DATABASE {schema};',use=False)
        created=True
        sql('\n'.join(before['schemas'][t]['create']+';' for t in KEYS))
        sql('\n'.join(insert(t,r) for t in KEYS for r in before['rows'][t]))
        # An out-of-scope wallet/inventory proves no destructive reset enters the migration.
        sql('CREATE TABLE inventory(character_id INT,slot_id INT,item_id INT,charges INT) ENGINE=InnoDB; '
            'CREATE TABLE character_currency(id INT PRIMARY KEY,platinum INT) ENGINE=InnoDB;'
            'INSERT INTO character_currency(id,platinum) VALUES(77,321);'
            'INSERT INTO inventory(character_id,slot_id,item_id,charges) VALUES(77,22,5500,1);')
        original=fingerprint()
        # Indexed lookup must retain the binary comparison of every other field.
        npc=before['rows']['npc_types'][0]
        changed_name=npc['name'].swapcase()
        assert changed_name!=npc['name']
        sql(f"UPDATE npc_types SET name={sql_value(changed_name)} WHERE id={int(npc['id'])};")
        drifted=fingerprint()
        verify(sql(patch_sql(before,after),False).returncode!=0,'same-key case-only NPC drift rejected')
        verify(fingerprint()==drifted,'drift rejection preserves all scoped rows')
        sql(f"UPDATE npc_types SET name={sql_value(npc['name'])} WHERE id={int(npc['id'])};")
        # Explicit occupied-ID case fails before any writes.
        sql(insert('npc_types',dict(after['rows']['npc_types'][-1],id='999600')))
        collision=fingerprint()
        verify(sql(patch_sql(before,after),False).returncode!=0,'reserved NPC collision rejected')
        verify(fingerprint()==collision,'collision rejection leaves entire content unchanged')
        sql('DELETE FROM npc_types WHERE id=999600;')
        sql(patch_sql(before,after))
        for table in KEYS:
            counts=sql('\n'.join(f'SELECT COUNT(*) FROM `{table}` WHERE '+indexed_predicate(table,r)+';' for r in after['rows'][table])).stdout.splitlines() if after['rows'][table] else []
            if counts!=['1']*len(counts):
                bad=[(i,r) for i,r in enumerate(after['rows'][table]) if counts[i]!='1']
                evidence.mkdir(parents=True,exist_ok=True)
                (evidence/'mismatches.json').write_text(json.dumps({table:bad},indent=2))
            verify(counts==['1']*len(after['rows'][table]),table+' exact afterimage')
        for table in ('npc_types','merchantlist','items'):
            row=after['rows'][table][0]
            explain=sql(f'EXPLAIN SELECT COUNT(*) FROM `{table}` WHERE '+indexed_predicate(table,row)+';').stdout.strip().split('\t')
            verify(explain[5]!='NULL',table+' exact predicate uses an index')
        applied=fingerprint()
        verify(sql(patch_sql(before,after),False).returncode!=0,'second apply fails closed without duplicate stock')
        verify(fingerprint()==applied,'rejected replay preserves candidate')
        rollback=rollback_target(before,after)
        sql(patch_sql(after,rollback))
        verify(sql('SELECT platinum FROM character_currency WHERE id=77; SELECT item_id FROM inventory WHERE character_id=77;').stdout.strip()=='321\n5500','player wallet and inventory survive apply and rollback')
        verify(sql('SELECT COUNT(*) FROM items WHERE id BETWEEN 998600 AND 998639;').stdout.strip()=='32','rollback retains definitions for granted starter items')
        for table in KEYS:
            verify(sql(f'SELECT COUNT(*) FROM `{table}`;').stdout.strip()==str(len(rollback['rows'][table])),table+' rollback row count')
        # Restore only fixture starter definitions and original saved-state rows to compare.
        sql('DELETE FROM items WHERE id BETWEEN 998600 AND 998639;'+''.join(insert('zone_state_spawns',r) for r in before['rows']['zone_state_spawns']))
        verify(fingerprint()==original,'all original scoped content restored exactly')
        return checks
    finally:
        if created:sql(f'DROP DATABASE IF EXISTS {schema};',use=False)
        evidence.mkdir(parents=True,exist_ok=True)
        (evidence/'database-checks.json').write_text(json.dumps(dict(checks=checks,disposable_schema_removed=True),indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
    p.add_argument('--container',default='akk-stack-mariadb-1');p.add_argument('--evidence',type=Path,required=True)
    a=p.parse_args();print(json.dumps(run(a.source,a.container,a.evidence)))
