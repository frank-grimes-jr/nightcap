"""Extract reviewed fixed identities from a read-only production capture."""
import argparse
import hashlib
import json
from pathlib import Path
from classic_dungeon_catalog import ADDED_DUNGEONS, SKY_PRIVATE, sky_respawn

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/dungeons/classic-expansion-20261022'

def prepare(capture):
    data=json.loads(capture.read_text())
    npcs={r['id']:r for r in data['npc_types']}
    private={r[2]:r for r in SKY_PRIVATE}
    result={'source_sha256':hashlib.sha256(capture.read_bytes()).hexdigest(),
            'captured_at':data['captured_at'],'environment':'production',
            'scope':'fixed objective identities and Keeper templates; current native populations, not an era restoration',
            'npc_types':[],'spawn2':[],'spawnentry':[],
            'zone':[r for r in data['zone'] if r['short_name'] in {d[0] for d in ADDED_DUNGEONS}]}
    for short,zone,keeper,band,roster in ADDED_DUNGEONS:
        used=set()
        for npc_id in roster:
            npc=npcs[npc_id]
            assert npc['class']<=16 and not npc['merchant_id'],npc_id
            assert 'fabled' not in npc['name'].lower(),npc_id
            result['npc_types'].append(npc)
            if npc_id in private:
                spawn,group,_,x,y,z,h=private[npc_id]
                row=dict(id=spawn,zone=short,version=0,spawngroupID=group,x=x,y=y,z=z,heading=h,
                    respawntime=sky_respawn(npc_id),min_expansion=0,max_expansion=-1,content_flags='',content_flags_disabled='',managed_private=True)
                entry=dict(spawngroupID=group,npcID=npc_id,chance=100,min_expansion=0,max_expansion=-1,content_flags='',content_flags_disabled='')
            else:
                entries=[r for r in data['spawnentry'] if r['npcID']==npc_id and r['min_expansion']<=0
                         and not r['content_flags'] and not r['content_flags_disabled']]
                groups={r['spawngroupID'] for r in entries}
                candidates=sorted((r for r in data['spawn2'] if r['zone']==short and r['spawngroupID'] in groups
                    and r['min_expansion']<=0 and not r['content_flags'] and not r['content_flags_disabled'] and r['id'] not in used),key=lambda r:r['id'])
                assert candidates,('No independent eligible spawn',short,npc_id)
                row=candidates[0];entry=next(r for r in entries if r['spawngroupID']==row['spawngroupID'])
            used.add(row['id']);result['spawn2'].append(row);result['spawnentry'].append(entry)
    result['templates']={
        'sky_key_service':npcs[71058],
        'npc_types':npcs[999227],
        'spawngroup':next(r for r in data['spawngroup'] if r['id']==999227),
        'spawnentry':next(r for r in data['spawnentry'] if r['npcID']==999227),
        'spawn2':next(r for r in data['spawn2'] if r['spawngroupID']==999227)}
    result['door_keys']=[{k:r[k] for k in ('id','doorid','zone','keyitem','dest_zone','dest_x','dest_y','dest_z')}
        for r in data['doors'] if r['zone']=='airplane' and r['keyitem']]
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'content.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'objective_npcs':len(result['npc_types']),'zones':len(result['zone']),'private_spawns':len(private)}))

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--capture',required=True,type=Path)
    prepare(parser.parse_args().capture)
