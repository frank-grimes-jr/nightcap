"""Private isolated native trial runner. Never connects to production."""
from pathlib import Path
import json,subprocess,time,argparse,hashlib
from setup_database import DB,SERVER,RUNTIME,sql,insert,run
HERE=Path(__file__).resolve().parent
matrix=json.loads((HERE/'matrix-private.json').read_text())
private=json.loads((HERE/'palwar-private-reference.json').read_text())['tables']
items={r['id']:r for r in private['items']}
RESULTS=HERE/'results';RESULTS.mkdir(exist_ok=True)

def reset():
    queries=['START TRANSACTION;']
    for table,key in [('character_skills','id'),('character_alternate_abilities','id'),('character_spells','id'),('character_memmed_spells','id'),('character_buffs','character_id')]:
        queries.append(f'DELETE FROM `{DB}`.`{table}` WHERE `{key}`=1;')
        queries.extend(insert(table,{**r,key:1}) for r in private[table])
    queries.extend([f'DELETE FROM `{DB}`.timers WHERE char_id=1;','COMMIT;'])
    sql('\n'.join(queries))

def validate(c,data):
    assert len(data['builds'])==1 and isinstance(data['status'],str)
    b=data['builds'][0];s=b['fixture_state'];build=c['build']
    assert (s['race'],s['deity'],s['gender'],s['classes'],s['size'])==(7,208,0,[3,1,7],5.5)
    skills=[0]*len(s['skills'])
    for row in build['saved_skills']:skills[row['skill_id']]=row['value']
    if build['equalize_2hs']:skills[3]=skills[1]
    assert skills==s['skills'],('skills',c['id'])
    expected={(r['aa_id'],r['aa_value'],r['charges']) for r in build['saved_aa']}
    actual={(r['first_rank'],r['earned'],r['saved_charges']) for r in b['aa_purchases']}
    assert expected==actual and b['aa_spent']==1979 and b['aa_remaining']==2
    assert all(0<=r['active']<=r['earned'] and r['active_charges']==r['saved_charges'] for r in b['aa_purchases'])
    expected_buffs={(r['slot_id'],r['spell_id'],r['ticsremaining'],r['caster_level']) for r in private['character_buffs']}
    assert expected_buffs=={(r['slot'],r['spell'],r['ticks'],r['casterlevel']) for r in s['buffs']}
    assert s['aa_block']==5 and s['shield_damage_aa']==100
    assert s['item_block']==build['candidate_block']
    actual_items={r['slot']:r for r in s['equipment']}
    assert {r['slot']:r['id'] for r in build['equipment']}=={slot:r['id'] for slot,r in actual_items.items()}
    assert s['shield']==(14 in actual_items)
    for requested in build['equipment']:
        resolved=actual_items[requested['slot']];raw=items[requested['id']]
        expected_fields={'damage':raw['damage'],'delay':raw['delay'],'accuracy':raw['accuracy'],'mana':raw['mana'],
            'astr':raw['astr'],'awis':raw['awis'],'heroic_str':raw['heroic_str'],'heroic_wis':raw['heroic_wis'],
            'healamt':raw['healamt'],'spelldmg':raw['spelldmg'],'proceffect':raw['proceffect'],'proctype':raw['proctype'],'proclevel2':raw['proclevel2']}
        expected_fields.update(requested.get('test_override',{}))
        for k,v in expected_fields.items():assert resolved[k]==v,(c['id'],requested['id'],k,resolved[k],v)
    assert actual_items[13]['type']==(0 if c['grip']=='1h' else 1)
    # Current equipped 5504 is compiled same-power 1HS: SQL 23/45, no candidate override.
    if c['kind']=='current-equipped-no-shield':assert (actual_items[13]['damage'],actual_items[13]['delay'])==(23,45)
    return b

def execute(c,mode,seed=101,pulse=32,suffix=''):
    name=f"{c['id']}-{mode}-{seed}-{pulse}{suffix}"
    dest=RESULTS/(name+'.json')
    payload=json.loads((HERE/'fixtures'/(c['id']+'-'+mode+'.json')).read_text())
    if mode=='combat':payload['encounter']['pulse_ms']=pulse
    source=HERE/'current-input.json';source.write_text(json.dumps(payload))
    reset()
    run(['docker','cp',str(source),SERVER+':'+RUNTIME+'/trial-input.json'])
    t=time.monotonic()
    p=subprocess.run(['docker','exec','-e',f'NIGHTCAP_BALANCE_RNG_SEED={seed}','-w',RUNTIME,SERVER,RUNTIME+'/balance-zone','tests:balance',RUNTIME+'/trial-input.json',RUNTIME+'/trial-output.json'],capture_output=True)
    (RESULTS/(name+'.log')).write_bytes(p.stdout+p.stderr)
    if p.returncode:raise RuntimeError(f'Native trial failed {name}: '+(p.stdout+p.stderr).decode(errors='replace')[-3000:])
    run(['docker','cp',SERVER+':'+RUNTIME+'/trial-output.json',str(dest)])
    data=json.loads(dest.read_text());validate(c,data)
    e=data.get('encounter',{})
    if mode=='combat':
        assert e and e['result'] in ['npc_death','player_death','timeout']
        assert e['npc_id']==73057 and e['pulse_ms']==pulse and data['native_rng_seed']==seed and data['native_seed_hook_calls']>0
        initial=e['initial_state']
        assert all(initial[k] for k in ['zone_loaded','npc_ai','npc_engaged','can_combat','npc_can_attack','player_can_attack','npc_has_spells'])
        assert not any(initial[k] for k in ['player_zoning','player_destroying','player_dead'])
        assert initial['npc_hate_target']==e['player_entity_id']
        assert e['trace'][0]['npc_hp']==32000 and e['trace'][0]['player_hp']==data['builds'][0]['hp']
        assert 0<e['trace'][-1]['ms']-e['trace'][0]['ms']<=900000
        assert e['damage_ledger'] and e['player_ledger']['incoming']
    print(json.dumps({'case':name,'wall_s':round(time.monotonic()-t,2),'result':e.get('result','stats_pass'),'elapsed_ms':e.get('elapsed_ms'),'bytes':dest.stat().st_size}),flush=True)
    return data

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['stats','pilot','matrix','controls']);a=p.parse_args()
    if a.mode=='stats':
        for c in matrix['conditions']:execute(c,'stats')
        (HERE/'stat-gates-passed.json').write_text(json.dumps({'conditions':48,'matrix_sha256':hashlib.sha256((HERE/'matrix-private.json').read_bytes()).hexdigest()})+'\n')
    elif a.mode=='pilot':execute(next(c for c in matrix['conditions'] if c['id']=='palwar-605504-1h-captured'),'combat')
    elif a.mode=='matrix':
        gate=json.loads((HERE/'stat-gates-passed.json').read_text())
        assert gate['matrix_sha256']==hashlib.sha256((HERE/'matrix-private.json').read_bytes()).hexdigest()
        for c in matrix['conditions']:
            for seed in matrix['seeds']:execute(c,'combat',seed)
    else:
        for item in [605504,611050,10099,810099]:
            for grip,skill in [('1h','captured'),('2h','equalized')]:
                c=next(c for c in matrix['conditions'] if c['id']==f'palwar-{item}-{grip}-{skill}')
                for seed in matrix['seeds']:execute(c,'combat',seed,50)
        execute(matrix['conditions'][0],'combat',101,32,'-replay')
