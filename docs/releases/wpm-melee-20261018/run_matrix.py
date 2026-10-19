"""Run bounded native diagnostics only in the dedicated synthetic runtime."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT=Path('/tmp/nightcap-balance-wpm-20261018')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',action='append',help='Run only named cases')
    args=parser.parse_args()
    assert Path.cwd()==ROOT
    config=json.loads((ROOT/'eqemu_config.json').read_text())['server']
    assert config['database']['db']=='nightcap_wpm_balance_20261018'
    assert config['auto_database_updates']=='false'
    binary=ROOT/'balance-zone'
    manifest=json.loads((ROOT/'native-build-manifest.json').read_text())
    assert sha(binary)==manifest['binary_sha256']
    cases=json.loads((ROOT/'matrix.json').read_text())['cases']
    if args.case:
        cases=[case for case in cases if case['id'] in args.case]
        assert len(cases)==len(args.case),'Unknown/duplicate case'
    report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'binary_sha256':sha(binary),'matrix_sha256':sha(ROOT/'matrix.json'),
            'scope':'Synthetic DB, native objects, diagnostic packet/clock adapters; no actual client or production changes',
            'cases':[]}
    for case in cases:
        source=ROOT/(case['id']+'-input.json');output=ROOT/(case['id']+'-result.json')
        source.write_text(json.dumps(case['input']))
        env={**os.environ,'NIGHTCAP_BALANCE_RNG_SEED':str(case['seed'])}
        with (ROOT/(case['id']+'.log')).open('w') as log:
            try:
                result=subprocess.run([str(binary),'tests:balance',str(source),str(output)],
                                      env=env,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=180)
                status='passed' if result.returncode==0 else 'failed'
            except subprocess.TimeoutExpired:status='timeout'
        row={'id':case['id'],'seed':case['seed'],'status':status,'input_sha256':sha(source)}
        if status=='passed':
            data=json.loads(output.read_text());row['output_sha256']=sha(output)
            row['aa_spent']=data['builds'][0]['aa_spent']
            if 'encounter' in data:row['outcome']=data['encounter']['result']
        else:
            row['log_tail']=(ROOT/(case['id']+'.log')).read_text(errors='replace')[-2500:]
        report['cases'].append(row)
        (ROOT/'matrix-results.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(row),flush=True)
    report['status']='passed' if all(r['status']=='passed' for r in report['cases']) else 'failed'
    (ROOT/'matrix-results.json').write_text(json.dumps(report,indent=2)+'\n')
    raise SystemExit(0 if report['status']=='passed' else 1)


if __name__=='__main__':main()
