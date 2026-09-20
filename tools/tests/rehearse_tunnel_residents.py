"""Rehearse resident installation and ownership-safe rollback outside live PEQ."""
import argparse
import json
from pathlib import Path
import re
import secrets
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pok_hub_migration import predicate
from rehearse_living_economy import sql

ROOT=Path(__file__).resolve().parents[2]


def run(evidence):
    package=ROOT/'docs/economy/residents'
    source=json.loads((package/'source.json').read_text())
    forward=(package/'forward.sql').read_text()
    rollback=(package/'rollback.sql').read_text()
    schema='nightcap_residents_test_'+secrets.token_hex(5)
    if not re.fullmatch('nightcap_residents_test_[a-f0-9]{10}',schema):
        raise ValueError('Unsafe disposable schema name')
    tables=['items','npc_types','npc_types_tint','spawngroup','spawnentry','spawn2',
            'zone_state_spawns','inventory','character_currency','merchantlist']
    checks=[]
    def q(query,check=True):return sql('USE '+schema+';\n'+query,check)
    def verify(condition,label):
        if not condition:raise AssertionError(label)
        checks.append(label)
    def owned_count():
        return q('SELECT COUNT(*) FROM npc_types WHERE id BETWEEN 999520 AND 999525; '
                 'SELECT COUNT(*) FROM npc_types_tint WHERE id BETWEEN 999520 AND 999525; '
                 'SELECT COUNT(*) FROM spawn2 WHERE id BETWEEN 999520 AND 999525;').stdout.strip()
    def preserved():
        return q('SELECT * FROM npc_types WHERE id NOT BETWEEN 999520 AND 999525 ORDER BY id; '
                 'SELECT * FROM npc_types_tint WHERE id NOT BETWEEN 999520 AND 999525 ORDER BY id; '
                 'SELECT * FROM inventory ORDER BY character_id,slot_id; '
                 'SELECT * FROM character_currency ORDER BY id; '
                 'SELECT * FROM merchantlist ORDER BY merchantid,slot; '
                 'SELECT * FROM spawn2 WHERE id NOT BETWEEN 999520 AND 999525 ORDER BY id;').stdout
    try:
        sql('CREATE DATABASE '+schema+';')
        q('\n'.join('CREATE TABLE '+t+' LIKE peq.'+t+';' for t in tables)+
          '\nINSERT INTO items SELECT * FROM peq.items WHERE id IN('+','.join(source['items'])+');'+
          '\nINSERT INTO npc_types SELECT * FROM peq.npc_types WHERE id IN('+','.join(source['templates'])+');'+
          '\nINSERT INTO merchantlist SELECT * FROM peq.merchantlist LIMIT 10;'+
          '\nINSERT INTO character_currency(id,platinum) VALUES(77,123);'+
          '\nINSERT INTO inventory(character_id,slot_id,item_id,charges) VALUES(77,33,5500,1);'+
          "\nINSERT INTO spawngroup(id,name) VALUES(999500,'ExistingTrader');"+
          "\nINSERT INTO spawn2(id,spawngroupID,zone,x,y,z) VALUES(999500,999500,'ecommons',-350,-1685,3.75);")
        template=next(iter(source['templates'].values()))
        q(f"UPDATE npc_types SET armortint_id=999520 WHERE id={template['id']};")
        dangling=preserved()
        verify(q(forward,False).returncode!=0,'dangling unowned tint reference rejects installation')
        verify(owned_count()=='0\n0\n0' and preserved()==dangling,'rejected install leaves no resident rows or unrelated changes')
        q(f"UPDATE npc_types SET armortint_id={template['armortint_id']} WHERE id={template['id']};")
        before=preserved()
        q(forward)
        verify(owned_count()=='6\n6\n6','six residents, persistent tint sets and placements installed')
        for table,rows in source['after'].items():
            counts=q('\n'.join('SELECT COUNT(*) FROM '+table+' WHERE '+predicate(row)+';' for row in rows)).stdout.splitlines()
            verify(counts==['1']*len(rows),table+' exact appearance and ownership preimages match')
        verify(q('SELECT level,maxlevel FROM npc_types WHERE id=999524;').stdout.strip()=='12\t12','Trift is exactly level twelve')
        verify(q('SELECT COUNT(*) FROM npc_types WHERE id BETWEEN 999520 AND 999525 AND '
                 '(loottable_id<>0 OR merchant_id<>0 OR skip_global_loot<>1);').stdout.strip()=='0','costume gear is not loot or merchant stock')
        verify(preserved()==before,'installation preserves existing NPCs, merchant stock, player items, money and trader placement')
        verify(q(forward,False).returncode!=0 and owned_count()=='6\n6\n6','duplicate installation rejected atomically')
        npc=source['after']['npc_types'][0]
        q(f"UPDATE npc_types SET face=face+1 WHERE id={npc['id']};")
        verify(q(rollback,False).returncode!=0 and owned_count()=='6\n6\n6','rollback refuses edited ownership preimage without partial deletion')
        q(f"UPDATE npc_types SET face={npc['face']} WHERE id={npc['id']};")
        columns=[line.split('\t') for line in q('SHOW COLUMNS FROM zone_state_spawns;').stdout.splitlines()]
        required={c[0]:('0' if re.match(r'(tinyint|smallint|mediumint|int|bigint|float|double|decimal)',c[1]) else "''")
                  for c in columns if c[2]=='NO' and c[4]=='NULL' and 'auto_increment' not in c[5]}
        for instance,corpse,npc_id in [(0,0,999520),(0,1,999520),(1,0,999520),(0,0,999500)]:
            row={**required,'zone_id':'22','instance_id':str(instance),'is_corpse':str(corpse),'is_zone':'0','npc_id':str(npc_id)}
            q('INSERT INTO zone_state_spawns('+','.join('`'+c+'`' for c in row)+') VALUES('+','.join(row.values())+');')
        q(rollback)
        verify(owned_count()=='0\n0\n0','rollback removes only owned residents, tints and placements')
        verify(q('SELECT COUNT(*) FROM zone_state_spawns;').stdout.strip()=='3','rollback retains corpses, other instances and existing trader state')
        verify(preserved()==before,'rollback preserves original NPCs, stock, player money/items and trader placement')
    finally:
        sql('DROP DATABASE IF EXISTS '+schema+';')
    evidence.mkdir(parents=True,exist_ok=True)
    report=dict(status='passed',scope='disposable schema; no live PEQ writes',schema_removed=schema,checks=checks)
    (evidence/'residents-database.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence',type=Path)
    run(parser.parse_args().evidence)
