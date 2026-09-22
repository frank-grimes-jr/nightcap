"""Exercise travel apply/rollback in a random disposable schema, never live PEQ."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import secrets
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tunnel_travel import capture, desired, patch_sql, rollback_target, KEYS, indexed
from pok_hub_migration import insert, sql_value
from rehearse_living_economy import sql


def run(source,evidence):
    before=json.loads(source.read_bytes());after=desired(before)
    schema='nightcap_travel_test_'+secrets.token_hex(5)
    assert re.fullmatch(r'nightcap_travel_test_[a-f0-9]{10}',schema)
    checks=[];created=False
    def q(text,check=True):return sql('USE '+schema+';\n'+text,check)
    def query(text):return q(text).stdout
    def verify(ok,label):
        if not ok:raise AssertionError(label)
        checks.append(label)
    def fingerprint():
        output=query('\n'.join(f'SELECT * FROM `{t}` ORDER BY '+','.join(k)+';' for t,k in KEYS.items()))
        return hashlib.sha256(output.encode()).hexdigest()
    try:
        sql('CREATE DATABASE '+schema+';');created=True
        q('\n'.join(before['schemas'][t]['create']+';' for t in KEYS))
        q('\n'.join(insert(t,r) for t in KEYS for r in before['rows'][t]))
        q('CREATE TABLE character_currency(id INT PRIMARY KEY,platinum INT) ENGINE=InnoDB;'
          'CREATE TABLE inventory(character_id INT,slot_id INT,item_id INT) ENGINE=InnoDB;'
          'INSERT INTO character_currency VALUES(77,321); INSERT INTO inventory VALUES(77,22,5500);')
        original=fingerprint()
        q("UPDATE doors SET name=LOWER(name) WHERE id=40600;");drifted=fingerprint()
        verify(q(patch_sql(before,after),False).returncode!=0,'case-only door drift rejected')
        verify(fingerprint()==drifted,'rejected drift performs no writes')
        q('UPDATE doors SET name='+sql_value(before['rows']['doors'][0]['name'])+' WHERE id=40600;')
        collision=dict(before['rows']['spawnentry'][0],spawngroupID='7',npcID='999810')
        q(insert('spawnentry',collision));occupied=fingerprint()
        verify(q(patch_sql(before,after),False).returncode!=0,'dangling guide reference blocks installation')
        verify(fingerprint()==occupied,'reference collision preserves database')
        q('DELETE FROM spawnentry WHERE spawngroupID=7 AND npcID=999810;')
        q(patch_sql(before,after))
        for table in KEYS:
            actual=query('\n'.join(f'SELECT COUNT(*) FROM `{table}` WHERE {indexed(table,r)};' for r in after['rows'][table])).splitlines() if after['rows'][table] else []
            verify(actual==['1']*len(after['rows'][table]),table+' exact afterimage')
        applied=fingerprint()
        verify(q(patch_sql(before,after),False).returncode!=0,'replay rejected')
        verify(fingerprint()==applied,'replay preserves installed content')
        q(patch_sql(after,before))
        verify(fingerprint()==original,'immediate rollback restores original content exactly')
        q(patch_sql(before,after))
        columns=[line.split('\t') for line in query('SHOW COLUMNS FROM zone_state_spawns;').splitlines()]
        required={c[0]:('0' if re.match(r'(tinyint|smallint|mediumint|int|bigint|float|double|decimal)',c[1]) else '')
                  for c in columns if c[2]=='NO' and c[4]=='NULL' and 'auto_increment' not in c[5]}
        for ident,zone,instance,corpse,npc in [(7001,22,0,0,999810),(7002,22,0,1,999810),
                                            (7003,22,1,0,999810),(7004,202,0,0,999810),(7005,22,0,0,123)]:
            row={**required,**{k:str(v) for k,v in dict(id=ident,zone_id=zone,instance_id=instance,
                is_corpse=corpse,is_zone=0,npc_id=npc,spawngroup_id=npc,spawn2_id=npc).items()}}
            q(insert('zone_state_spawns',row))
        verify(q(patch_sql(after,before),False).returncode!=0,'stale immediate rollback fails closed after zone activity')
        referenced=fingerprint()
        try:rollback_target(before,capture(query),after)
        except ValueError:blocked=True
        else:blocked=False
        verify(blocked,'guide references in corpses or other instances/zones block rollback')
        verify(fingerprint()==referenced,'blocked rollback retains all referenced states and guide definitions')
        # These disposable fixtures now represent unrelated saved states.
        q('UPDATE zone_state_spawns SET npc_id=123,spawngroup_id=123,spawn2_id=123 WHERE id BETWEEN 7002 AND 7004;')
        retained=query('SELECT * FROM zone_state_spawns WHERE id<>7001 ORDER BY id;')
        current=capture(query);target=rollback_target(before,current,after)
        q(patch_sql(current,target))
        verify(query('SELECT COUNT(*) FROM zone_state_spawns WHERE id=7001;').strip()=='0','runtime rollback removes guide saved state')
        verify(query('SELECT * FROM zone_state_spawns ORDER BY id;')==retained,'runtime rollback preserves unrelated corpses, other instances/zones and NPC states')
        verify(query('SELECT platinum FROM character_currency; SELECT item_id FROM inventory;').strip()=='321\n5500','player wallet and inventory unchanged')
        q('DELETE FROM zone_state_spawns WHERE id BETWEEN 7002 AND 7005;')
        verify(fingerprint()==original,'post-activity rollback restores original scoped content exactly')
        return checks
    finally:
        if created:sql('DROP DATABASE '+schema+';')
        evidence.mkdir(parents=True,exist_ok=True)
        (evidence/'database-checks.json').write_text(json.dumps(dict(checks=checks,schema=schema,removed=created),indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True)
    p.add_argument('--evidence',type=Path,required=True);a=p.parse_args()
    print(json.dumps(run(a.source,a.evidence)))
