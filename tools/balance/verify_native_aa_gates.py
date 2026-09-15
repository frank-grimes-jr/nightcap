"""Run rejected-purchase controls inside the isolated native runtime."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from uuid import uuid4


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs',type=Path,required=True)
    parser.add_argument('--catalog',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    root = Path.cwd().resolve()
    if root.parent != Path('/tmp') or not root.name.startswith('nightcap-balance-'):
        raise ValueError('Only the isolated runtime is supported')
    if any(p.resolve().parent != root for p in (args.inputs,args.catalog,args.output)):
        raise ValueError('All files must be directly inside the isolated runtime')
    build = json.loads(args.inputs.read_text())['builds'][0]
    catalogs = json.loads(args.catalog.read_text())['builds']
    ranks = next(b['aa_catalog'] for b in catalogs if b['profile']==build['profile'])
    first = next(r for r in ranks if r['purchasable_now_ignoring_price'] and r['cost'] > 0)
    later = next(r for r in ranks if r['rank']==2 and not r['grant_only'] and not r['prereqs'])
    grant = next(r for r in ranks if r['rank']==1 and r['grant_only'])
    prereq = next(r for r in ranks if r['rank']==1 and not r['grant_only']
                 and any(p['ability_exists'] and p['ranks']>0 for p in r['prereqs']))
    own_ids = {r['rank_id'] for r in ranks}
    foreign = next(r for b in catalogs for r in b['aa_catalog']
                   if r['rank_id'] not in own_ids and r['purchasable_now_ignoring_price'])
    cases = [('insufficient_points',[first['rank_id']],first['cost']-1),
             ('duplicate_rank',[first['rank_id']]*2,100000),
             ('missing_previous_rank',[later['rank_id']],100000),
             ('grant_only',[grant['rank_id']],100000),
             ('missing_prerequisite',[prereq['rank_id']],100000),
             ('unheld_class',[foreign['rank_id']],100000)]
    result = []
    token = uuid4().hex
    for name, ids, budget in cases:
        source, output = root/f'aa-invalid-{token}-{name}.json', root/f'aa-invalid-{token}-{name}-result.json'
        source.write_text(json.dumps({'builds':[build | {'aa_budget':budget,'aa_rank_ids':ids}]}))
        run = subprocess.run([str(root/'balance-zone'),'tests:balance',str(source),str(output)],
                             capture_output=True,text=True,timeout=60)
        rejected = run.returncode==1 and 'Native AA purchase gate rejected rank' in run.stderr and not output.exists()
        result.append({'case':name,'rank_ids':ids,'budget':budget,'exit_code':run.returncode,
                       'rejected_by_purchase_gate':rejected})
    report = {'binary_sha256':hashlib.sha256((root/'balance-zone').read_bytes()).hexdigest(),
              'cases':result,'passed':all(r['rejected_by_purchase_gate'] for r in result)}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return int(not report['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
