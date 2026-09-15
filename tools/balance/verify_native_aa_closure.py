"""Ask native purchase gates whether all/free baselines omitted a legal rank."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from uuid import uuid4


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    root = Path.cwd().resolve()
    if root.parent != Path('/tmp') or not root.name.startswith('nightcap-balance-'):
        raise ValueError('Only the isolated runtime is supported')
    if any(p.resolve().parent != root for p in (args.inputs,args.output)):
        raise ValueError('All files must be directly inside the isolated runtime')
    builds = [b for b in json.loads(args.inputs.read_text())['builds'] if b['aa_stage'] in ('0','all')]
    profiles = {b['profile'] for b in builds}
    if not profiles or len(builds) != len(profiles)*2 or any(
            {b['aa_stage'] for b in builds if b['profile']==p} != {'0','all'} for p in profiles):
        raise ValueError('Expected both zero and all stages for every profile')
    token = uuid4().hex
    source, output = root/f'aa-closure-{token}-input.json', root/f'aa-closure-{token}-result.json'
    source.write_text(json.dumps({'export_aa_catalog':True,'builds':builds}))
    subprocess.run([str(root/'balance-zone'),'tests:balance',str(source),str(output)],check=True,timeout=60)
    rows = json.loads(output.read_text())['builds']
    if len(rows) != len(builds):
        raise ValueError('Native result did not cover all inputs')
    cases = []
    for b, r in zip(builds,rows):
        if (b['profile'],b['aa_stage']) != (r['profile'],r['aa_stage']):
            raise ValueError('Native result order/identity changed')
        remaining = [aa['rank_id'] for aa in r['aa_catalog'] if aa['purchasable_now_ignoring_price']
                     and (b['aa_stage']=='all' or aa['cost']==0)]
        exact = [p['rank_id'] for p in r['aa_purchases']]==b['aa_rank_ids']
        cases.append({'profile':b['profile'],'stage':b['aa_stage'],'native_spent':r['aa_spent'],
                      'remaining_purchasable_rank_ids':remaining,'exact_purchase_order':exact})
    result = {'binary_sha256':hashlib.sha256((root/'balance-zone').read_bytes()).hexdigest(),
              'inputs_sha256':hashlib.sha256(args.inputs.read_bytes()).hexdigest(),
              'raw_report_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),
              'raw_report_runtime_path':str(output),'cases':cases,
              'passed':all(not c['remaining_purchasable_rank_ids'] and c['exact_purchase_order'] for c in cases),
              'scope':'Native purchase gate closure; grant-only rewards and active buff compatibility are separate'}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    return int(not result['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
