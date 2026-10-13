"""Rehearse captured production content in a disposable LOCAL MariaDB schema."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import secrets
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tunnel_cozy as content
from pok_hub_migration import insert, sql_value
from rehearse_living_economy import sql

def run(source,evidence):
    captured=json.loads(source.read_bytes())
    schema='nightcap_cozy_test_'+secrets.token_hex(5)
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
            if content.normalize(actual['rows'][table])!=content.normalize(expected['rows'][table]):
                raise AssertionError('Afterimage mismatch: '+table)
    def blocked(statement,label):
        baseline=fingerprint()
        verify(q(statement,False).returncode!=0,label)
        if fingerprint()!=baseline:raise AssertionError('Rejected SQL wrote data: '+label)
    try:
        sql('CREATE DATABASE '+schema+';');created=True
        q('\n'.join(captured['schemas'][t]['create']+';' for t in content.KEYS))
        q('\n'.join(insert(t,r) for t in content.KEYS for r in captured['rows'][t]))
        spawn=content.topology(captured['rows'])[999220]
        cache=dict(id='8000000',zone_id='22',instance_id='0',is_corpse='0',is_zone='0',npc_id='999220',
            spawn2_id=spawn['id'],spawngroup_id=spawn['spawngroupID'],x='-141',y='-1702',z='3.75',heading='0',respawn_time='60',variance='0')
        q('\n'.join(insert('zone_state_spawns',row) for row in [cache,
            dict(cache,id='8000001',is_corpse='1'),dict(cache,id='8000002',instance_id='9'),
            dict(cache,id='8000003',is_zone='1'),dict(cache,id='8000004',npc_id='0')]))
        before=content.capture(query);after=content.desired(before);forward=content.patch_sql(before,after)
        name=next(n['name'] for n in before['rows']['npc_types'] if n['id']=='999220')
        q("UPDATE npc_types SET name=LOWER(name) WHERE id=999220;")
        blocked(forward,'case-only content drift rejected atomically')
        q('UPDATE npc_types SET name='+sql_value(name)+' WHERE id=999220;')
        donor=before['rows']['doors'][0]
        for label,row in [('global ornament ID',dict(donor,id='999611',zone='unrelated')),
                          ('cross-version zone door ID',dict(donor,id='8000000',zone='ecommons',version='1',doorid='216'))]:
            q(insert('doors',row));blocked(forward,label+' collision rejected')
            q('DELETE FROM doors WHERE id='+row['id']+';')
        entry=next(e for e in before['rows']['spawnentry'] if e['npcID']=='999220')
        q(insert('spawnentry',dict(entry,spawngroupID='8000000')))
        blocked(forward,'external owned-NPC reference rejected')
        q('DELETE FROM spawnentry WHERE spawngroupID=8000000;')
        q(forward);exact(after);verify(True,'exact forward afterimages')
        verify(query('SELECT id FROM zone_state_spawns WHERE id BETWEEN 8000000 AND 8000004 ORDER BY id;').splitlines()==['8000001','8000002','8000003'],
               'corpses, other instances and metadata retained; owned active and dormant cache removed')
        blocked(forward,'replay rejected atomically')
        target=content.rollback_target(before,after,after)
        q(content.patch_sql(after,target));exact(target);verify(True,'exact immediate rollback; no stale cache reinsertion')
        installed=content.desired(target);q(content.patch_sql(target,installed))
        q(insert('zone_state_spawns',cache))
        q('UPDATE zone_state_spawns SET x=123 WHERE id=8000001;')
        current=content.capture(query);target=content.rollback_target(before,current,installed)
        q(content.patch_sql(current,target));exact(target)
        verify(query('SELECT x FROM zone_state_spawns WHERE id=8000001;').strip()=='123','rollback preserves fresh corpse changes')
        verify(query('SELECT COUNT(*) FROM zone_state_spawns WHERE id=8000000;').strip()=='0','rollback invalidates fresh owned cache')
        static=copy.deepcopy(installed);static['rows']['doors'][0]['size']='77'
        rejected=False
        try:content.rollback_target(before,static,installed)
        except ValueError:rejected=True
        verify(rejected,'rollback rejects intervening static content changes')
        return checks
    finally:
        evidence.mkdir(parents=True,exist_ok=True)
        record=dict(checks=checks,schema=schema,removed=False)
        path=evidence/'database-checks.json';path.write_text(json.dumps(record,indent=2)+'\n')
        if created:
            sql('DROP DATABASE '+schema+';')
            record['removed']=True;path.write_text(json.dumps(record,indent=2)+'\n')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True)
    args=p.parse_args();print(json.dumps(run(args.source,args.evidence),indent=2))
