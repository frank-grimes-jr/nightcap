"""Verify sampled action integration against exact throughput expectations.

An inert target and artificial resource pools isolate event scheduling and sample
application. This is not a Nagafen encounter or a balance result.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import statistics

from encounter import Actor, simulate
from native_spell_actions import action, summarize


def control(probe, runs, duration_ms=60000):
    summary = summarize(probe)
    rows = probe['outcomes']
    costs = {r['mana'] for r in rows}
    times = {r['cast_ms'] for r in rows}
    if len(costs)!=1 or len(times)!=1:
        raise ValueError('This analytic control requires constant cost/cast time')
    cost, cast_ms = costs.pop(), times.pop()
    # Deliberate test cooldown, not a claim about focused spell reuse.
    recovery_ms = recast_ms = 1500
    casts = max(0,(duration_ms-cast_ms)//(cast_ms+recovery_ms)+1)
    spell = action(probe,recast_ms=recast_ms,recovery_ms=recovery_ms)
    p = Actor('native-action control caster',hp=10**9,mana=10**9,actions=(spell,))
    target = Actor('inert throughput control',hp=10**9)
    trials = [simulate(p,target,seed=seed,duration_ms=duration_ms,trace=seed==0) for seed in range(runs)]
    accounting = all(r['outcome']=='timeout' and r['player']['casts']==casts
                     and r['player']['mana_spent']==casts*cost for r in trials)
    per_cast = summary['amount']['mean']
    variance = sum(r['count']*(r['amount']-per_cast)**2 for r in rows)/probe['samples']
    expected = casts*per_cast
    observed = statistics.mean(r['player']['damage'] for r in trials)
    standard_error = math.sqrt(casts*variance/runs)
    z = (observed-expected)/standard_error if standard_error else 0 if observed==expected else math.inf
    return {'runs':runs,'first_seed':0,'last_seed':runs-1,'duration_ms':duration_ms,
            'casts_per_trial':casts,'mana_per_trial':casts*cost,'accounting_exact':accounting,
            'expected_mean_damage':expected,'observed_mean_damage':observed,
            'mean_standard_error':standard_error,'z_score':z,'passed':accounting and abs(z)<5,
            'first_trace':trials[0]['trace']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--runs',type=int,default=2000)
    args = parser.parse_args()
    if args.runs<2:
        raise ValueError('At least two control trials are required')
    report = json.loads(args.native.read_text())
    results = []
    for stage in ('0','all'):
        build = next(b for b in report['builds'] if b['profile']=='war-clr-wiz' and b['aa_stage']==stage)
        probe = next(p for p in build['spell_probes'] if p['spell_id']==732 and p['npc_id']==32040)
        results.append({'aa_stage':stage,**control(probe,args.runs)})
    result = {'native_report_sha256':hashlib.sha256(args.native.read_bytes()).hexdigest(),
              'engine_sha256':hashlib.sha256(Path(__file__).with_name('encounter.py').read_bytes()).hexdigest(),
              'scope':'Sampled Ice Comet actions against an inert unlimited-resource control; no boss AI or encounter certification',
              'controls':results,'passed':all(r['passed'] for r in results)}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({**result,'controls':[{k:v for k,v in r.items() if k!='first_trace'} for r in results]},indent=2))
    return int(not result['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
