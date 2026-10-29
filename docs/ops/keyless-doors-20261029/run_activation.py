"""Send the reviewed single-use operator and pinned private inputs over SSH."""
import hashlib
import json
from pathlib import Path
import subprocess
from capture_baseline import SSH

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

def main():
    pins = json.loads((HERE/'production-plan.json').read_text())['files']
    for name, digest in pins.items():
        assert hashlib.sha256((HERE/'private'/name).read_bytes()).hexdigest() == digest
    revision = subprocess.check_output(['git','rev-parse','origin/main'],cwd=ROOT,text=True).strip()
    assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip() == revision
    values = dict(CAPTURE_SOURCE=(ROOT/'tools/keyless_doors_capture.py').read_text(),
                  RUNTIME_SOURCE=(HERE/'runtime.py').read_text(),
                  EXPECTED=json.loads((HERE/'private/production-before.json').read_text()),
                  FORWARD=(HERE/'private/forward.sql').read_text(),
                  ROLLBACK=(HERE/'private/rollback.sql').read_text(),
                  MAIN_REVISION=revision,
                  EXPECTED_IMAGE='sha256:0dec2bfc8b2e83a30301c2fc203c5688d44a2b39cf354b5e0e0b2ba8ed38f9dd')
    source = ''.join(k+'='+repr(v)+'\n' for k,v in values.items()) + (HERE/'activate.py').read_text()
    result = subprocess.run(SSH+['sudo -n python3 -'],input=source,text=True,capture_output=True,timeout=900)
    if result.returncode:
        raise RuntimeError(result.stderr[-4000:]+'\nInspect remote result.json before any continuation.')
    report=json.loads(result.stdout)
    assert report['status']=='activated_verified'
    (HERE/'deployed.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['status','changed_doors','remaining_locks','no_restart']}))

if __name__ == '__main__':
    main()
