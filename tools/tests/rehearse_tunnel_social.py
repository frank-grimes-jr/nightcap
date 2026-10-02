"""Exercise the actual social revision SQL in a disposable MariaDB schema."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import secrets
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tunnel_social as content
from pok_hub_migration import insert, sql_value
from rehearse_living_economy import sql

def run(source,evidence):
    before=json.loads(source.read_bytes());after=content.desired(before)
    schema='nightcap_social_test_'+secrets.token_hex(5)
    if not re.fullmatch(r'nightcap_social_test_[a-f0-9]{10}',schema):raise ValueError('Invalid test schema')
    checks=[];created=False
    def q(statement,check=True):return sql('USE '+schema+';\n'+statement,check)
    def query(statement):return q(statement).stdout
    def verify(ok,label):
        if not ok:raise AssertionError(label)
        checks.append(label)
    def fingerprint():
        rows=query('\n'.join('SELECT * FROM `'+t+'` ORDER BY '+','.join(keys)+';' for t,keys in content.KEYS.items()))
        return hashlib.sha256(rows.encode()).hexdigest()
    def exact(expected):
        actual=content.capture(query)
        for table in content.KEYS:
            norm=lambda rows:sorted(json.dumps(r,sort_keys=True) for r in rows)
            if norm(actual['rows'][table])!=norm(expected['rows'][table]):
                raise AssertionError('Exact database afterimage mismatch: '+table)
    try:
        sql('CREATE DATABASE '+schema+';');created=True
        q('\n'.join(before['schemas'][t]['create']+';' for t in content.KEYS))
        q('\n'.join(insert(t,r) for t in content.KEYS for r in before['rows'][t]))
        q('CREATE TABLE inventory(character_id INT,slot_id INT,item_id INT) ENGINE=InnoDB;'
          'CREATE TABLE character_currency(id INT PRIMARY KEY,platinum INT) ENGINE=InnoDB;'
          'CREATE TABLE merchantlist(merchantid INT,slot INT,item INT) ENGINE=InnoDB;'
          'CREATE TABLE rule_values(rule_name VARCHAR(80),rule_value VARCHAR(80)) ENGINE=InnoDB;'
          'INSERT INTO inventory VALUES(77,22,5500); INSERT INTO character_currency VALUES(77,321);'
          'INSERT INTO merchantlist VALUES(99300,1,100); INSERT INTO rule_values VALUES("Expansion:CurrentExpansion","0");')
        exact(before)
        name=next(n['name'] for n in before['rows']['npc_types'] if n['id']=='997900')
        q("UPDATE npc_types SET name=LOWER(name) WHERE id=997900;");drifted=fingerprint()
        verify(q(content.patch_sql(before,after),False).returncode!=0,'case-only source drift rejected')
        verify(fingerprint()==drifted,'drift rejection writes nothing')
        q('UPDATE npc_types SET name='+sql_value(name)+' WHERE id=997900;')
        collision=dict(before['rows']['npc_types'][0],id='8000000',name=content.MERCHANT_NAMES[997900])
        q(insert('npc_types',collision));occupied=fingerprint()
        verify(q(content.patch_sql(before,after),False).returncode!=0,'new merchant name collision rejected')
        verify(fingerprint()==occupied,'name collision preserves all data')
        q('DELETE FROM npc_types WHERE id=8000000;')
        collision=dict(before['rows']['spawnentry'][0],spawngroupID='8000000',npcID='999520')
        q(insert('spawnentry',collision))
        verify(q(content.patch_sql(before,after),False).returncode!=0,'new external NPC reference rejected')
        q('DELETE FROM spawnentry WHERE spawngroupID=8000000;')
        q(content.patch_sql(before,after));exact(after)
        verify(True,'exact native numeric afterimages for all eight content tables')
        applied=fingerprint()
        verify(q(content.patch_sql(before,after),False).returncode!=0,'replay rejected')
        verify(fingerprint()==applied,'replay preserves installed scene')
        restored=content.rollback_target(before,after,after)
        q(content.patch_sql(after,restored));exact(restored)
        verify(True,'immediate rollback restores content without old moved NPC caches')
        q(content.patch_sql(restored,content.desired(restored)))
        current=content.capture(query)
        template=copy.deepcopy(before['rows']['zone_state_spawns'][0])
        spawn=next(s for s in before['rows']['spawn2'] if s['spawngroupID']=='999520')
        for key,value in dict(id=8000000,npc_id=999520,spawn2_id=spawn['id'],spawngroup_id=999520,
                              zone_id=22,instance_id=0,is_corpse=0,is_zone=0).items():template[key]=str(value)
        q(insert('zone_state_spawns',template))
        for field,value in [('is_corpse','1'),('is_zone','1'),('instance_id','1'),('zone_id','202')]:
            q(f'UPDATE zone_state_spawns SET `{field}`={value} WHERE id=8000000;')
            blocked=False
            try:content.rollback_target(before,content.capture(query),after)
            except ValueError:blocked=True
            verify(blocked,'rollback blocks ambiguous saved state: '+field)
            q(f'UPDATE zone_state_spawns SET `{field}`={template[field]} WHERE id=8000000;')
        native=copy.deepcopy(next(s for s in before['rows']['zone_state_spawns'] if int(s['npc_id']) in content.NATIVES))
        native['id']='8000001';q(insert('zone_state_spawns',native))
        current=content.capture(query);target=content.rollback_target(before,current,after)
        retained=[r for r in current['rows']['zone_state_spawns'] if int(r['npc_id']) in content.NATIVES]
        q(content.patch_sql(current,target));exact(target)
        verify(query('SELECT COUNT(*) FROM zone_state_spawns WHERE id=8000000;').strip()=='0','fresh rollback invalidates newly saved moved NPC')
        verify(query('SELECT COUNT(*) FROM zone_state_spawns WHERE id=8000001;').strip()=='1','fresh unrelated native cache survives rollback')
        verify(len(target['rows']['zone_state_spawns'])==len(retained),'all unchanged native saved states retained')
        verify(query('SELECT item_id FROM inventory;SELECT platinum FROM character_currency;SELECT item FROM merchantlist;SELECT rule_value FROM rule_values;').strip()=='5500\n321\n100\n0',
               'player items/money, merchant stock and era preserved')
        return checks
    finally:
        if created:sql('DROP DATABASE '+schema+';')
        evidence.mkdir(parents=True,exist_ok=True)
        (evidence/'database-checks.json').write_text(json.dumps(dict(checks=checks,schema=schema,removed=created),indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True)
    a=p.parse_args();print(json.dumps(run(a.source,a.evidence)))
