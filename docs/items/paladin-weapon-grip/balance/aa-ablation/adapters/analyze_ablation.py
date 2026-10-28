"""Whole-encounter and predeclared first20s comparisons for the AA experiment."""
from pathlib import Path
from collections import defaultdict,Counter
import json,statistics as st,hashlib,csv
import aa_ablation as a
from analyze_results import analyze
WINDOW_MS=20000
ARMS=['baseline','wu_off','steel_off','both_off']

def result_path(c,arm,seed,pulse=32):
    if arm=='baseline':return a.base.RESULTS/f"{c['id']}-combat-{seed}-{pulse}.json"
    return a.RESULTS/f"{arm}-{c['id']}-combat-{seed}-{pulse}.json"

def measure(c,arm,seed,pulse=32):
    path=result_path(c,arm,seed,pulse);r=analyze(path,c);data=json.loads(path.read_text());e=data['encounter'];t0=e['trace'][0]['ms']
    assert e['trace'][-1]['ms']-t0>=WINDOW_MS,('Common20s window not available',path)
    def damage(d):return max(0,max(0,d['hp_before'])-max(0,d['hp_after']))
    early=[d for d in e['damage_ledger'] if d['depth']==0 and t0<=d['ms']<=t0+WINDOW_MS]
    packets=[p for p in e['events'] if p['type']=='damage' and p['target']==e['npc_entity_id'] and p['damage']>0 and t0<=p['ms']<=t0+WINDOW_MS]
    total=sum(p['damage'] for p in packets);monk=sum(p['damage'] for p in packets if p['damage_type'] in [21,23,30] and p['spell']==65535)
    slash=sum(p['damage'] for p in packets if p['damage_type']==1 and p['spell']==65535)
    r.update(arm=arm,early_dps=sum(damage(d) for d in early)/(WINDOW_MS/1000),early_monk_dps=monk/(WINDOW_MS/1000),early_slash_dps=slash/(WINDOW_MS/1000),early_monk_share=monk/total if total else 0)
    # Packet evidence of the associated skill proc; not successful damaging landings.
    r['fists_of_fury_events']=sum(p.get('spell')==23598 for p in e['events'])
    if arm in ['steel_off','both_off']:assert r['fists_of_fury_events']==0
    r['monk_requests']=len(e['monk_actions']['requests'])
    r['nested_damage_calls']=sum(d['depth']>0 for d in e['damage_ledger'])
    return r

def summarize(rs):
    wins=[r for r in rs if r['result']=='npc_death']
    return {'runs':len(rs),'wins':len(wins),'deaths':sum(r['result']=='player_death' for r in rs),'timeouts':sum(r['result']=='timeout' for r in rs),
      'mean_winning_seconds':st.mean(r['seconds'] for r in wins) if wins else None,
      **{'mean_'+k:st.mean(r[k] for r in rs) for k in ['seconds','dps','early_dps','early_monk_dps','early_slash_dps','early_monk_share','monk_packet_share','minimum_sampled_hp_pct','accepted_heals','mend_requests','native_healing_hp','monk_requests']},
      'minimum_sampled_hp_pct':min(r['minimum_sampled_hp_pct'] for r in rs)}

if __name__=='__main__':
    rows=[measure(c,arm,seed) for arm in ARMS for c in a.base.matrix['conditions'] for seed in a.base.matrix['seeds']]
    aggregates=[]
    for c in a.base.matrix['conditions']:
        for arm in ARMS:
            rs=[r for r in rows if r['condition']==c['id'] and r['arm']==arm]
            assert len(rs)==5
            aggregates.append({'condition':c['id'],'name':c['weapon_name'],'grip':c['grip'],'equalized':c['build']['equalize_2hs'],'arm':arm,**summarize(rs)})
    cohorts=[]
    for equal in [False,True]:
        for arm in ARMS:
            rs=[r for r in rows if r['equalized']==equal and r['arm']==arm]
            cohorts.append({'equalized':equal,'arm':arm,**summarize(rs)})
    duplicate_pairs={};replays={}
    for arm in ARMS:
        count=0
        for c in a.base.matrix['conditions']:
            if c['grip']!='1h' or c['build']['equalize_2hs']:continue
            equal=next(k for k in a.base.matrix['conditions'] if k['id']==c['id'].replace('-captured','-equalized'))
            for seed in a.base.matrix['seeds']:
                one=json.loads(result_path(c,arm,seed).read_text());two=json.loads(result_path(equal,arm,seed).read_text());assert one['encounter']==two['encounter'];count+=1
        duplicate_pairs[arm]=count
        if arm!='baseline':
            c=next(c for c in a.base.matrix['conditions'] if c['id']=='palwar-605504-1h-captured')
            replay=a.RESULTS/f"{arm}-{c['id']}-combat-101-32-replay.json"
            assert json.loads(replay.read_text())==json.loads(result_path(c,arm,101).read_text());replays[arm]=True
    controls=[]
    for arm in ARMS:
        for item in [605504,611050,10099,810099]:
            for grip,skill in [('1h','captured'),('2h','equalized')]:
                c=next(c for c in a.base.matrix['conditions'] if c['id']==f'palwar-{item}-{grip}-{skill}')
                for seed in a.base.matrix['seeds']:controls.append(measure(c,arm,seed,50))
    interactions=[]
    for c in a.base.matrix['conditions']:
        d={g['arm']:g for g in aggregates if g['condition']==c['id']}
        b,w,s,n=[d[k]['mean_early_dps'] for k in ARMS]
        interactions.append({'condition':c['id'],'wu_removal_drop_pct':100*(b-w)/b,'steel_removal_drop_pct':100*(b-s)/b,'both_removal_drop_pct':100*(b-n)/b,
            'interaction_dps':b-w-s+n,'wu_gain_with_steel':b-w,'wu_gain_without_steel':s-n,'steel_gain_with_wu':b-s,'steel_gain_without_wu':w-n})
    out={'window_ms':WINDOW_MS,'primary_runs_including_reused_baseline':len(rows),'new_primary_runs':720,'new_timestep_controls':120,
      'whole_aa_scope':'Remove selected synthetic owned AA families; no refunds/reallocation. Way of Steel removal includes its Fists of Fury skill proc, not just +200 damage.',
      'limits':'Five-seed whole-build pilot; seeds diverge after AA differences change RNG consumption. First20s is observed native HP-loss DPS over a common duration, not a pure formula multiplier. Conditional differences include cadence, misses, procs and controller effects. Whole-fight mean DPS and outcome mix are separate; mean winning time excludes deaths/timeouts. Duplicate1H pairs and controls are not independent samples.',
      'cohorts':cohorts,'aggregates':aggregates,'interactions':interactions,'controls':controls,'duplicate_1h_pairs':duplicate_pairs,'exact_replays':replays,'runs':rows}
    (a.OUT/'summary.json').write_text(json.dumps(out,indent=2)+'\n')
    with (a.OUT/'summary.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(aggregates[0]));writer.writeheader();writer.writerows(aggregates)
    print(json.dumps({'cohorts':cohorts,'duplicates':duplicate_pairs,'replays':replays},indent=2))
