"""Validate locally; deploy the owner-authorized, main-promoted quest."""
import ast
import base64
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
action=sys.argv[1] if len(sys.argv)==2 else 'check'
assert action in ('check','apply','rollback')
source=(HERE/'remote.py').read_text()
ast.parse(source)
quest=ROOT/'server-mods/quests/global/Instance_Keeper.pl'
recovery=HERE/'Instance_Keeper.recovery.pl'
for path in (quest,recovery):
    subprocess.run(['perl','-c',str(path)],check=True)
for path in (ROOT/'tools/tests/instance_keeper_visuals.t',ROOT/'tools/tests/waypoint_visuals.t',HERE/'test_recovery.t'):
    subprocess.run(['perl',str(path)],cwd=ROOT,check=True)
subprocess.run([sys.executable,'-B',str(HERE/'test_operator.py')],check=True)
if action=='check':sys.exit(0)
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
if action=='apply':
    subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/main'],cwd=ROOT,check=True)
assert not subprocess.check_output(['git','status','--porcelain','--',
    'server-mods/quests/global/Instance_Keeper.pl','docs/ops/dungeon-keeper-visibility-20261022',
    'tools/tests/instance_keeper_visuals.t'],cwd=ROOT,text=True).strip(),'Uncommitted operation files'
header=f'ACTION={action!r}\nCOMMIT={commit!r}\n'
# Preserve committed UTF-8 bytes, normalizing only checkout line endings.
for name,path in [('PAYLOAD',quest),('RECOVERY',recovery)]:
    payload=path.read_bytes().replace(b'\r\n',b'\n')
    header+=f'{name}={base64.b64encode(payload).decode()!r}\n'
subprocess.run(['ssh','-i',str(Path.home()/'.ssh/nightcap_ovh'),'-o','BatchMode=yes',
    '-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202',
    'sudo -n python3 -'],input=header+source,text=True,check=True)
