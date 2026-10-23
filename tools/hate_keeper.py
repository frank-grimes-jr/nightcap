"""Guarded relocation of the existing Hate service; no player/run mutations."""
import copy
import json
from pathlib import Path
import content_patch

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'docs/ops/hate-keeper-commonlands-20261022'
KEYS={'npc_types':['id'],'spawnentry':['spawngroupID','npcID'],'spawngroup':['id'],
      'spawn2':['id'],'zone':['id'],'nightcap_dungeon_spawns':['zone_id','spawn_id'],
      'zone_state_spawns':['id']}
SCOPES={'npc_types':'id=998812','spawnentry':'npcID=998812 OR spawngroupID=998812',
        'spawngroup':'id=998812','spawn2':'id=9100012 OR spawngroupID=998812',
        'zone':"short_name='hateplane' AND version=0",
        'nightcap_dungeon_spawns':'zone_id=76 OR spawn_id=9100012',
        'zone_state_spawns':'zone_id=76 AND instance_id=0 AND is_corpse=0 AND is_zone=0 AND spawn2_id=9100012 AND spawngroup_id=998812 AND npc_id IN (0,998812)'}
POSE={'zone':'ecommons','x':'-346.000000','y':'-1570.000000','z':'3.000000','heading':'256.000000'}
PRIVATE=dict(zone_id=76,spawn_id=9100012,npc_id=998812,group_id=998812,boss_id=0,
             is_final=0,x=-337.08,y=-374.8,z=2,heading=0,respawn=86400,grid_id=0)

def capture(query):return content_patch.capture(query,SCOPES)

def desired(before):
    rows=before['rows']
    if before['scopes']!=SCOPES:raise ValueError('Capture scope drift')
    if any(len(rows[t])!=1 for t in ('npc_types','spawnentry','spawngroup','spawn2','zone')):
        raise ValueError('Service identity cardinality drift')
    npc,spawn,zone=(rows[t][0] for t in ('npc_types','spawn2','zone'))
    if any(npc[k]!=v for k,v in dict(id='998812',name='Instance_Keeper',lastname='hateplane').items()):
        raise ValueError('Keeper identity drift')
    if any(spawn[k]!=v for k,v in dict(id='9100012',spawngroupID='998812',zone='hateplane',version='0').items()):
        raise ValueError('Keeper spawn drift')
    if zone['zoneidnumber']!='76' or zone['min_status']!='80' or zone['min_level']!='46':
        raise ValueError('Hate access policy drift')
    if rows['nightcap_dungeon_spawns']:raise ValueError('Private service slot occupied')
    for row in rows['zone_state_spawns']:
        expected=dict(zone_id='76',instance_id='0',is_corpse='0',is_zone='0',spawn2_id='9100012',spawngroup_id='998812')
        if any(row[k]!=v for k,v in expected.items()) or row['npc_id'] not in ('0','998812'):
            raise ValueError('Unowned saved state')
    after=copy.deepcopy(before)
    after['rows']['spawn2'][0].update(POSE)
    after['rows']['zone'][0]['min_status']='0'
    after['rows']['nightcap_dungeon_spawns']=[{k:str(v) for k,v in PRIVATE.items()}]
    after['rows']['zone_state_spawns']=[]
    return after

def patch_sql(before,after):
    return content_patch.patch_sql(before,after,KEYS,SCOPES)

def refresh_contract(contract):
    from dungeon_contract import predicate
    # Successor overlays the reviewed historical install batch, leaving that
    # installation and its rollback immutable. A new native zone is mandatory.
    rows=json.loads((ROOT/'docs/dungeons/classic-expansion-20261022/install-rows.json').read_text())['spawn2']
    batch=copy.deepcopy(rows[8:16])
    target=next(r for r in batch if r['id']==9100012)
    target.update(zone='ecommons',x=-346,y=-1570,z=3,heading=256)
    check=next(c for c in contract['content'] if c['label']=='classic/spawn2/8')
    check['sql']='SELECT COUNT(*) FROM `spawn2` WHERE '+' OR '.join(predicate(r) for r in batch)
    additions=[dict(label='hate-keeper/access',sql='SELECT COUNT(*) FROM zone WHERE '+predicate(dict(id=162,zoneidnumber=76,version=0,short_name='hateplane',min_status=0,min_level=46)),expected='1'),
               dict(label='hate-keeper/private',sql='SELECT COUNT(*) FROM nightcap_dungeon_spawns WHERE '+predicate(PRIVATE),expected='1')]
    contract['content']=[c for c in contract['content'] if not c['label'].startswith('hate-keeper/')]+additions
    return contract

def main():
    before=json.loads((HERE/'preimages.json').read_text());after=desired(before)
    (HERE/'afterimages.json').write_text(json.dumps(after,indent=2)+'\n')
    (HERE/'forward.sql').write_text(patch_sql(before,after),encoding='utf-8',newline='\n')
    # Rehearsal-only inverse. Live rollback must capture fresh state and retain
    # private service content once runs/checkpoints exist; never replay snapshots.
    (HERE/'inverse-rehearsal.sql').write_text(patch_sql(after,before),encoding='utf-8',newline='\n')
    print('Generated exact guarded content patch and isolated inverse rehearsal.')

if __name__=='__main__':main()
