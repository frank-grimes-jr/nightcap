"""Apply and recover court content in a random disposable MariaDB schema."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import secrets
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tunnel_courts import desired, patch_sql, capture, rollback_target, KEYS, indexed
from pok_hub_migration import insert
from rehearse_living_economy import sql

def run(source,evidence):
    before=json.loads(source.read_bytes());after=desired(before)
    schema='nightcap_courts_test_'+secrets.token_hex(5)
    assert re.fullmatch(r'nightcap_courts_test_[a-f0-9]{10}',schema)
    checks=[];created=False
    def q(statement,check=True):return sql('USE '+schema+';\n'+statement,check)
    def query(statement):return q(statement).stdout
    def verify(ok,label):
        if not ok:raise AssertionError(label)
        checks.append(label)
    def fingerprint():
        result=query('\n'.join(f'SELECT * FROM `{t}` ORDER BY '+','.join(k)+';' for t,k in KEYS.items()))
        return hashlib.sha256(result.encode()).hexdigest()
    try:
        sql('CREATE DATABASE '+schema+';');created=True
        q('\n'.join(before['schemas'][t]['create']+';' for t in KEYS))
        q('\n'.join(insert(t,r) for t in KEYS for r in before['rows'][t]))
        q('CREATE TABLE character_currency(id INT PRIMARY KEY,platinum INT) ENGINE=InnoDB;'
          'CREATE TABLE inventory(character_id INT,slot_id INT,item_id INT) ENGINE=InnoDB;'
          'CREATE TABLE merchantlist(merchantid INT,slot INT,item INT) ENGINE=InnoDB;'
          'CREATE TABLE rule_values(rule_name VARCHAR(80),rule_value VARCHAR(80)) ENGINE=InnoDB;'
          'INSERT INTO character_currency VALUES(77,321); INSERT INTO inventory VALUES(77,22,5500);'
          'INSERT INTO merchantlist VALUES(99300,1,100); INSERT INTO rule_values VALUES("Expansion:CurrentExpansion","0");')
        original=fingerprint()
        q("UPDATE npc_types SET name=LOWER(name) WHERE id=999525;");drifted=fingerprint()
        verify(q(patch_sql(before,after),False).returncode!=0,'case-only NPC drift rejected')
        verify(fingerprint()==drifted,'rejected row drift performs no writes')
        # Restore just this test's modified name using its captured literal.
        from pok_hub_migration import sql_value
        name=next(n['name'] for n in before['rows']['npc_types'] if n['id']=='999525')
        q('UPDATE npc_types SET name='+sql_value(name)+' WHERE id=999525;')
        collision=dict(before['rows']['spawnentry'][0],spawngroupID='7',npcID='999527')
        q(insert('spawnentry',collision));occupied=fingerprint()
        verify(q(patch_sql(before,after),False).returncode!=0,'dangling Khaleid reference blocks installation')
        verify(fingerprint()==occupied,'reference collision preserves database')
        q('DELETE FROM spawnentry WHERE spawngroupID=7 AND npcID=999527;')
        q(patch_sql(before,after))
        for table in KEYS:
            found=query('\n'.join(f'SELECT COUNT(*) FROM `{table}` WHERE {indexed(table,r)};' for r in after['rows'][table])).splitlines() if after['rows'][table] else []
            verify(found==['1']*len(after['rows'][table]),table+' exact afterimage')
        applied=fingerprint()
        verify(q(patch_sql(before,after),False).returncode!=0,'replay rejected')
        verify(fingerprint()==applied,'replay preserves installed content')
        q(patch_sql(after,before))
        verify(fingerprint()==original,'immediate rollback restores exact preimage')
        q(patch_sql(before,after))
        template=copy.deepcopy(before['rows']['zone_state_spawns'][0])
        for ident,zone,instance,corpse,npc in [(700001,22,0,0,999527),(700002,22,0,1,999527),
                (700003,22,1,0,999527),(700004,202,0,0,999527),(700005,22,0,0,123)]:
            template.update({k:str(v) for k,v in dict(id=ident,zone_id=zone,instance_id=instance,
                is_corpse=corpse,is_zone=0,npc_id=npc,spawngroup_id=npc,spawn2_id=npc).items()})
            q(insert('zone_state_spawns',template))
        verify(q(patch_sql(after,before),False).returncode!=0,'stale rollback stops after new zone activity')
        current=capture(query);referenced=fingerprint()
        try:rollback_target(before,current,after)
        except ValueError:blocked=True
        else:blocked=False
        verify(blocked,'corpse/other-zone/other-instance dependencies block rollback')
        verify(fingerprint()==referenced,'blocked rollback preserves all referenced states')
        q('UPDATE zone_state_spawns SET npc_id=123,spawngroup_id=123,spawn2_id=123 WHERE id BETWEEN 700002 AND 700004;')
        retained=query('SELECT * FROM zone_state_spawns WHERE id<>700001 ORDER BY id;')
        current=capture(query);target=rollback_target(before,current,after)
        q(patch_sql(current,target))
        verify(query('SELECT COUNT(*) FROM zone_state_spawns WHERE id=700001;').strip()=='0','fresh scoped rollback removes Khaleid cached state')
        verify(query('SELECT * FROM zone_state_spawns ORDER BY id;')==retained,'unrelated/corpse/other-instance saved states preserved')
        verify(query('SELECT platinum FROM character_currency;SELECT item_id FROM inventory;SELECT item FROM merchantlist;SELECT rule_value FROM rule_values;').strip()=='321\n5500\n100\n0','player inventory/currency, merchant stock and era rule preserved')
        return checks
    finally:
        if created:sql('DROP DATABASE '+schema+';')
        evidence.mkdir(parents=True,exist_ok=True)
        (evidence/'database-checks.json').write_text(json.dumps(dict(checks=checks,schema=schema,removed=created),indent=2)+'\n')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True);parser.add_argument('--evidence',type=Path,required=True)
    args=parser.parse_args();print(json.dumps(run(args.source,args.evidence)))
