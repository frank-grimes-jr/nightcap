"""Exercise campfire forward/rollback SQL against real captured MariaDB schemas."""
import argparse
import hashlib
import json
from pathlib import Path
import secrets
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tunnel_campfire as content
from pok_hub_migration import insert, sql_value
from rehearse_living_economy import sql

def run(source,evidence):
    before=json.loads(source.read_bytes())
    schema='nightcap_campfire_test_'+secrets.token_hex(5)
    checks=[];created=False
    def q(statement,check=True):return sql('USE '+schema+';\n'+statement,check)
    def query(statement):return q(statement).stdout
    def verify(ok,label):
        if not ok:raise AssertionError(label)
        checks.append(label)
    def fingerprint():
        return hashlib.sha256(query('\n'.join('SELECT * FROM `'+t+'` ORDER BY '+','.join(keys)+';' for t,keys in content.KEYS.items())).encode()).hexdigest()
    def exact(expected):
        actual=content.capture(query)
        for table in content.KEYS:
            if content.normalized(actual['rows'][table])!=content.normalized(expected['rows'][table]):raise AssertionError('Afterimage mismatch: '+table)
    def blocked(statement,label):
        baseline=fingerprint()
        verify(q(statement,False).returncode!=0,label)
        if fingerprint()!=baseline:raise AssertionError('Rejected SQL wrote data: '+label)
    try:
        sql('CREATE DATABASE '+schema+';');created=True
        q('\n'.join(before['schemas'][t]['create']+';' for t in content.KEYS))
        q('\n'.join(insert(t,r) for t in content.KEYS for r in before['rows'][t]))
        # Explicit fresh cache plus an unrelated state must survive opposite ways.
        spawn=next(s for s in before['rows']['spawn2'] if s['spawngroupID']=='999523')
        cache=dict(id='8000000',zone_id='22',instance_id='0',is_corpse='0',is_zone='0',npc_id='999523',
                   spawn2_id=spawn['id'],spawngroup_id='999523',x='-249',y='-1718',z='3.75',heading='0',respawn_time='60',variance='0')
        q(insert('zone_state_spawns',cache));other=dict(cache,id='8000001',npc_id='22001',spawn2_id='123',spawngroup_id='123')
        q(insert('zone_state_spawns',other))
        before=content.capture(query);after=content.desired(before);forward=content.patch_sql(before,after)
        q("UPDATE npc_types SET name=LOWER(name) WHERE id=999523;")
        blocked(forward,'case-only NPC drift rejected without writes')
        q('UPDATE npc_types SET name='+sql_value(content.NAMES[999523])+' WHERE id=999523;')
        donor=before['rows']['doors'][0]
        for label,row in [('global fire ID',dict(donor,id=str(content.FIRE_ID),zone='unrelated')),
                          ('door ID in another version',dict(donor,id='8000000',zone='ecommons',version='1',doorid=str(content.FIRE_DOOR)))]:
            q(insert('doors',row));blocked(forward,label+' collision rejected without writes')
            q('DELETE FROM doors WHERE id='+row['id']+';')
        q(insert('spawnentry',dict(before['rows']['spawnentry'][0],spawngroupID='8000000')))
        blocked(forward,'external resident spawn reference rejected')
        q('DELETE FROM spawnentry WHERE spawngroupID=8000000;')
        q(forward);exact(after);verify(True,'exact MariaDB forward afterimages')
        verify(query('SELECT COUNT(*) FROM zone_state_spawns WHERE id=8000000;').strip()=='0','owned saved spawn invalidated')
        verify(query('SELECT COUNT(*) FROM zone_state_spawns WHERE id=8000001;').strip()=='1','unrelated saved spawn preserved')
        blocked(forward,'replay rejected without writes')
        target=content.rollback_target(before,after,after);q(content.patch_sql(after,target));exact(target)
        verify(True,'immediate rollback restores six residents and removes only owned fire')
        installed=content.desired(target);q(content.patch_sql(target,installed));q(insert('zone_state_spawns',cache))
        for field,value in [('is_corpse','1'),('is_zone','1'),('instance_id','1'),('zone_id','202'),('spawn2_id','123')]:
            q(f'UPDATE zone_state_spawns SET `{field}`={value} WHERE id=8000000;')
            rejected=False
            try:content.rollback_target(before,content.capture(query),installed)
            except ValueError:rejected=True
            verify(rejected,'rollback rejects ambiguous state: '+field)
            q(f'UPDATE zone_state_spawns SET `{field}`={cache[field]} WHERE id=8000000;')
        q('UPDATE doors SET size=66 WHERE id=999606;')
        rejected=False
        try:content.rollback_target(before,content.capture(query),installed)
        except ValueError:rejected=True
        verify(rejected,'rollback rejects edited fire')
        q('UPDATE doors SET size=65 WHERE id=999606;')
        current=content.capture(query);target=content.rollback_target(before,current,installed)
        q(content.patch_sql(current,target));exact(target)
        verify(query('SELECT id FROM zone_state_spawns WHERE id IN (8000000,8000001);').strip()=='8000001','fresh rollback removes new owned cache and preserves unrelated cache')
        return checks
    finally:
        if created:sql('DROP DATABASE '+schema+';')
        evidence.mkdir(parents=True,exist_ok=True)
        (evidence/'database-checks.json').write_text(json.dumps(dict(checks=checks,schema=schema,removed=created),indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True)
    a=p.parse_args();print(json.dumps(run(a.source,a.evidence)))
