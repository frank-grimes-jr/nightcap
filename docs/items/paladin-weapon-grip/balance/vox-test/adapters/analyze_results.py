"""Aggregate actual native encounter ledgers; never substitute formula DPS."""
from pathlib import Path
from collections import Counter,defaultdict
import json,statistics as st,hashlib,csv
HERE=Path(__file__).resolve().parent
matrix=json.loads((HERE/'matrix-private.json').read_text())
RESULTS=HERE/'results'

def analyze(path,c):
    data=json.loads(path.read_text());b=data['builds'][0];e=data['encounter'];trace=e['trace'];t0=trace[0]['ms'];t1=trace[-1]['ms'];seconds=(t1-t0)/1000
    assert seconds>0 and t1==e['elapsed_ms']
    top=[r for r in e['damage_ledger'] if r['depth']==0]
    dealt=lambda r:max(0,max(0,r['hp_before'])-max(0,r['hp_after']))
    damage=sum(map(dealt,top));melee=sum(dealt(r) for r in top if r['spell']==65535)
    byspell=defaultdict(int)
    for r in top:byspell[str(r['spell'])]+=dealt(r)
    incoming=sum(max(0,r['lost_hp']) for r in e['player_ledger']['incoming'])
    if e['result']=='player_death':incoming=max(0,incoming+min(0,trace[-1]['player_hp']))
    packets=[r for r in e['events'] if r['type']=='damage' and r['target']==e['npc_entity_id'] and r['damage']>0]
    packet_total=sum(r['damage'] for r in packets)
    slash=sum(r['damage'] for r in packets if r['damage_type']==1 and r['spell']==65535)
    monk=sum(r['damage'] for r in packets if r['damage_type'] in [21,23,30] and r['spell']==65535)
    casts=Counter(r['spell'] for r in e['events'] if r['type']=='begin_cast' and r['source']==e['npc_entity_id'])
    p=b['fixture_state'];f=b['final_fixture_state'];weapon=next(r for r in p['equipment'] if r['slot']==13)
    return {'condition':c['id'],'name':c['weapon_name'],'kind':c['kind'],'grip':c['grip'],'equalized':c['build']['equalize_2hs'],
        'seed':data['native_rng_seed'],'pulse_ms':e['pulse_ms'],'result':e['result'],'seconds':seconds,'hp_max':b['hp'],'mana_max':b['mana'],
        'player_hp_end':max(0,trace[-1]['player_hp']),'player_mana_end':trace[-1]['player_mana'],'vox_hp_end':max(0,trace[-1]['npc_hp']),
        'minimum_sampled_hp_pct':100*min(max(0,r['player_hp']) for r in trace)/b['hp'],
        'native_healing_hp':sum(max(0,r['healed']) for r in e['player_ledger']['healing']),
        'damage':damage,'dps':damage/seconds,'melee_dps':melee/seconds,'spell_dps':(damage-melee)/seconds,
        'incoming_hp_loss':incoming,'incoming_dps':incoming/seconds,'feared_samples':sum(bool(r['feared']) for r in trace),'samples':len(trace),
        'packet_total':packet_total,'slash_packet_dps':slash/seconds,'monk_packet_dps':monk/seconds,'monk_packet_share':monk/packet_total if packet_total else 0,
        'two_hs_start':p['skills'][3],'two_hs_end':f['skills'][3],'weapon_damage':weapon['damage'],'weapon_delay':weapon['delay'],
        'weapon_accuracy':weapon['accuracy'],'item_block':p['item_block'],'aa_block':p['aa_block'],
        'npc_casts':dict(casts),'damage_by_spell':dict(byspell),'heal_attempts':len(e['attempts']),
        'accepted_heals':sum(bool(r['accepted']) for r in e['attempts']), 'mend_requests':len(e['mend_requests']),
        'failed_paths':e['movement']['failed_paths'],'seed_hook_calls':data['native_seed_hook_calls'],
        'source':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

def aggregate(rows):
    out=[]
    for c in matrix['conditions']:
        rs=[r for r in rows if r['condition']==c['id']]
        if not rs:continue
        assert len(rs)==5
        o={k:rs[0][k] for k in ['condition','name','kind','grip','equalized','hp_max','mana_max','weapon_damage','weapon_delay','weapon_accuracy','item_block','aa_block']}
        o['wins']=sum(r['result']=='npc_death' for r in rs);o['deaths']=sum(r['result']=='player_death' for r in rs);o['timeouts']=sum(r['result']=='timeout' for r in rs)
        for k in ['seconds','dps','melee_dps','spell_dps','slash_packet_dps','monk_packet_dps','monk_packet_share','incoming_dps','player_hp_end','player_mana_end','vox_hp_end','two_hs_end','accepted_heals','mend_requests','minimum_sampled_hp_pct','native_healing_hp']:
            o[k]=st.mean(r[k] for r in rs)
        for k in ['seconds','dps']:o[k+'_min']=min(r[k] for r in rs);o[k+'_max']=max(r[k] for r in rs)
        out.append(o)
    return out

if __name__=='__main__':
    rows=[]
    for c in matrix['conditions']:
        for seed in matrix['seeds']:
            p=RESULTS/f"{c['id']}-combat-{seed}-32.json"
            assert p.exists(),p
            rows.append(analyze(p,c))
    agg=aggregate(rows)
    replay=RESULTS/f"{matrix['conditions'][0]['id']}-combat-101-32-replay.json"
    original=RESULTS/f"{matrix['conditions'][0]['id']}-combat-101-32.json"
    replay_equal=json.loads(replay.read_text())==json.loads(original.read_text())
    assert replay_equal,'Native replay differs; do not claim deterministic evidence'
    unchanged_pairs=0
    for c in matrix['conditions']:
        if c['grip']=='1h' and not c['build']['equalize_2hs']:
            for seed in matrix['seeds']:
                a=json.loads((RESULTS/f"{c['id']}-combat-{seed}-32.json").read_text())
                b=json.loads((RESULTS/f"{c['id'].replace('-captured','-equalized')}-combat-{seed}-32.json").read_text())
                assert a['encounter']==b['encounter']
                unchanged_pairs+=1
    controls=[]
    for c in matrix['conditions']:
        for seed in matrix['seeds']:
            p=RESULTS/f"{c['id']}-combat-{seed}-50.json"
            if p.exists():controls.append(analyze(p,c))
    assert len(controls)==40
    output={'scope':matrix['scope'],'actual_fights':len(rows),'timestep_controls':controls,'exact_replay_equal':replay_equal,'unchanged_1h_skill_pairs':unchanged_pairs,'aggregates':agg,'runs':rows,
        'metrics':'DPS = sum of positive non-overkill native NPC HP loss from depth-zero Damage calls / elapsed fight seconds. Includes melee, Monk attacks, procs and damage shields; spell attribution follows outer Damage calls. Not primary-weapon-only DPS. Packet slashing/Monk DPS and shares exclude an un-emitted lethal packet and are descriptive only. Incoming HP loss excludes final negative-HP death sentinel; not mitigation-only. NPC casts are cast starts, not landings; fear/HP minima are sampled about512ms, not continuous. Five seeded trials per condition are pilot observations, not population win probabilities.'}
    (HERE/'results-summary.json').write_text(json.dumps(output,indent=2)+'\n')
    with (HERE/'results-summary.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(agg[0]));w.writeheader();w.writerows(agg)
    print(json.dumps({'fights':len(rows),'wins':sum(r['result']=='npc_death' for r in rows),'deaths':sum(r['result']=='player_death' for r in rows),'timeouts':sum(r['result']=='timeout' for r in rows),'replay_equal':replay_equal,'controls':len(controls)}))
