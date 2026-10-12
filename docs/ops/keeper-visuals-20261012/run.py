"""Check locally; apply/rollback the reviewed quest only after owner approval."""
import ast
import base64
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
action = sys.argv[1] if len(sys.argv) == 2 else 'check'
assert action in ('check', 'apply', 'rollback')
source = (HERE / 'remote.py').read_text()
ast.parse(source)
quest = ROOT / 'server-mods/quests/global/Instance_Keeper.pl'
subprocess.run(['perl', '-c', str(quest)], check=True)
subprocess.run(['perl', str(ROOT / 'tools/tests/instance_keeper_visuals.t')], check=True)
if action == 'check':
    sys.exit(0)
commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
if action == 'apply':
    subprocess.run(['git', 'merge-base', '--is-ancestor', commit, 'origin/main'], cwd=ROOT, check=True)
    assert not subprocess.check_output(['git','status','--porcelain','--',
        'server-mods/quests/global/Instance_Keeper.pl','docs/ops/keeper-visuals-20261012',
        'tools/tests/instance_keeper_visuals.t'],cwd=ROOT,text=True).strip(), 'Uncommitted operation files'
payload = quest.read_text().replace('\r\n', '\n').encode()
header = f'ACTION={action!r}\nCOMMIT={commit!r}\nPAYLOAD={base64.b64encode(payload).decode()!r}\n'
subprocess.run(['ssh','-i',str(Path.home()/'.ssh/nightcap_ovh'),'-o','BatchMode=yes',
    '-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202',
    'sudo -n python3 -'],input=header+source,text=True,check=True)
