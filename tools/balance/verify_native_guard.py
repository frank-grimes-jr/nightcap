"""Verify native preflight rejects unsafe configs before database initialization.

Run inside the server container; every test uses invented credentials and must
fail at preflight, never at a later connection attempt.
"""
import argparse
import copy
import json
import subprocess
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--binary',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    config = {'server':{'database':{'db':'nightcap_balance_20260912','username':'nightcap_balance'},
                        'auto_database_updates':'false'}}
    changes = (
        ('live_database', lambda c:c['server']['database'].update(db='peq')),
        ('root_account', lambda c:c['server']['database'].update(username='root')),
        ('content_database', lambda c:c['server'].update(content_database={})),
        ('automatic_updates', lambda c:c['server'].update(auto_database_updates='true')),
    )
    results = []
    with tempfile.TemporaryDirectory(prefix='nightcap-balance-guard-',dir='/tmp') as temp:
        root = Path(temp)
        def attempt(name, candidate, *, cwd=root, input_path=None, operation='tests:balance'):
            (root/'eqemu_config.json').write_text(json.dumps(candidate))
            run = subprocess.run([str(args.binary),operation,str(input_path or root/'input.json'),str(root/'output.json')],
                                 cwd=cwd,capture_output=True,text=True,timeout=15)
            passed = run.returncode != 0 and 'Balance preflight refused:' in run.stderr and not run.stdout
            results.append({'case':name,'passed':passed,'exit_code':run.returncode})
        for name, change in changes:
            candidate = copy.deepcopy(config)
            change(candidate)
            attempt(name,candidate)
        attempt('outside_input',config,input_path=Path('/tmp/outside-input.json'))
        attempt('outside_runtime',config,cwd=Path('/tmp'))
        attempt('wrong_operation',config,operation='tests:npc-handins')
    report = {'checks':results,'passed':all(r['passed'] for r in results),
              'scope':'Early preflight rejection only; no valid configuration is started'}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
