"""Run the reviewed quest operator; no database or native process restart."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
from deploy import SSH, HERE, ROOT

SOURCE_COMMIT = 'f293626d4ddb69d464806084308f00b93ca8f35f'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['check', 'apply', 'rollback'])
    args = parser.parse_args()
    subprocess.run(['git','merge-base','--is-ancestor',SOURCE_COMMIT,'origin/main'],cwd=ROOT,check=True)
    payload = subprocess.check_output(['git','show',SOURCE_COMMIT+':server-mods/quests/global/999240.pl'],cwd=ROOT)
    local = (ROOT/'server-mods/quests/global/999240.pl').read_bytes()
    assert payload == local.replace(b'\r\n', b'\n'), 'Quest differs from promoted source'
    assert hashlib.sha256(payload).hexdigest() == '4b15350087dfd4153ea2ef98e418da9696b0c7efe99cdd8fe62cb96483f764a2'
    header = f'ACTION={args.action!r}\nCOMMIT={SOURCE_COMMIT!r}\nPAYLOAD={base64.b64encode(payload).decode()!r}\n'
    header += 'CONTROL='+repr((HERE/'world_control.py').read_text(encoding='utf-8'))+'\n'
    source = header + (HERE/'quest_remote.py').read_text(encoding='utf-8')
    result = subprocess.run(SSH+['sudo -n python3 -'],input=source,text=True,capture_output=True,timeout=180)
    if result.returncode:
        raise RuntimeError(result.stderr[-5000:])
    report = json.loads(result.stdout)
    (HERE/('quest-'+args.action+'.json')).write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report))

if __name__ == '__main__':
    main()
