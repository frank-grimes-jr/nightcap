"""Validate native direct-action samples and adapt their joint distributions."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from encounter import Action


def validate_probe(probe):
    n = probe['samples']
    rows = probe['outcomes']
    if not isinstance(n,int) or n < 1 or not rows or sum(r['count'] for r in rows) != n:
        raise ValueError('Native sample count mismatch')
    keys = []
    for r in rows:
        if not isinstance(r['count'],int) or r['count'] <= 0 or min(r['amount'],r['mana'],r['cast_ms']) < 0:
            raise ValueError('Invalid native outcome')
        if not 0 <= r['landed_percent'] <= 100 or (r['landed_percent']==0 and r['amount']!=0):
            raise ValueError('Invalid native resist/amount pair')
        if any(not isinstance(r[k],int) for k in ('amount','mana','cast_ms')):
            raise ValueError('Native amounts, mana, and cast times must be integers')
        keys.append(tuple(r[k] for k in ('amount','mana','cast_ms','landed_percent')))
    if len(set(keys)) != len(keys):
        raise ValueError('Duplicate native histogram outcome')
    if probe['effect'] not in ('damage','heal'):
        raise ValueError('Only direct sampled effects are integrated')


def action(probe, *, recast_ms, recovery_ms, hp_below=1000):
    """Caller supplies resolved cooldown policy; no raw-to-effective assumption."""
    validate_probe(probe)
    return Action(name=probe['name'],effect=probe['effect'],amount=0,
                  mana=probe['raw_mana'],cast_ms=probe['raw_cast_ms'],
                  recast_ms=recast_ms,recovery_ms=recovery_ms,hp_below=hp_below,
                  resolved_outcomes=tuple((r['count'],r['amount'],r['mana'],r['cast_ms'],r['landed_percent'])
                                          for r in probe['outcomes']))


def summarize(probe):
    validate_probe(probe)
    n, rows = probe['samples'],probe['outcomes']
    result = {k:probe[k] for k in ('spell_id','name','npc_id','effect','samples')}
    for field in ('amount','mana','cast_ms'):
        mean = sum(r['count']*r[field] for r in rows)/n
        variance = sum(r['count']*(r[field]-mean)**2 for r in rows)/(n-1) if n>1 else None
        result[field] = {'mean':mean,'min':min(r[field] for r in rows),'max':max(r[field] for r in rows),
                         'mean_standard_error':math.sqrt(variance/n) if variance is not None else None}
    result['full_resist_fraction'] = sum(r['count'] for r in rows if r['landed_percent']==0)/n
    return result


def scenario_key(row):
    return row['profile'],row['tier'],row['aa_stage'],row['aa_policy']


def verify(inputs, report):
    expected = {scenario_key(b):b for b in inputs['builds']}
    actual = {scenario_key(b):b for b in report['builds']}
    if expected.keys()!=actual.keys() or len(expected)!=len(inputs['builds']) or len(actual)!=len(report['builds']):
        raise ValueError('Missing, duplicate, or unexpected native build')
    if not isinstance(report.get('native_rng_seed'),int) or report.get('native_seed_hook_calls',0) < 1:
        raise ValueError('Native seed hook was not exercised')
    summaries = []
    for key, b in expected.items():
        r = actual[key]
        probes = {(p['spell_id'],p['npc_id']):p for p in r['spell_probes']}
        requested = {(p['spell_id'],p.get('npc_id',0)) for p in b['spell_probes']}
        if probes.keys()!=requested or len(probes)!=len(r['spell_probes']) or len(requested)!=len(b['spell_probes']):
            raise ValueError('Native probe coverage mismatch')
        for p in probes.values():
            if p['samples']!=inputs['spell_samples'] or (p['caster_hp'],p['caster_mana'])!=(r['hp'],r['mana']):
                raise ValueError('Wrong native sample count or caster resource state')
            summaries.append({'profile':b['profile'],'aa_stage':b['aa_stage'],'aa_policy':b['aa_policy'],**summarize(p)})
    return summaries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs',type=Path,required=True)
    parser.add_argument('--native',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    inputs, report = json.loads(args.inputs.read_text()),json.loads(args.native.read_text())
    rows = verify(inputs,report)
    result = {'input_sha256':hashlib.sha256(args.inputs.read_bytes()).hexdigest(),
              'native_sha256':hashlib.sha256(args.native.read_bytes()).hexdigest(),
              'native_seed':report['native_rng_seed'],'actions':len(rows),
              'samples':sum(r['samples'] for r in rows),'summaries':rows,
              'scope':'Sampled native direct actions at full resources without active buffs; mean errors describe Monte Carlo sampling only, not model omissions'}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='summaries'},indent=2))


if __name__ == '__main__':
    main()
