"""Validate or transmit the checked-in Crushbone migration to the owner OVH host."""
import ast
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
action=sys.argv[1] if len(sys.argv)>1 else 'check'
assert action in ('check','apply')
for name in ('deploy.py','world_status.py','run.py'):
    ast.parse((HERE/name).read_text(encoding='utf-8'))
subprocess.run([sys.executable,'-I',str(ROOT/'tools/tests/test_crushbone_waypoint.py'),'--sql-dir',str(HERE)],check=True)
if action=='check':
    print('Syntax and SQL scope checks passed.')
    sys.exit(0)
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
subprocess.run(['git','merge-base','--is-ancestor',commit,'origin/main'],cwd=ROOT,check=True)
paths=['docs/ops/crushbone-waypoint-20261009','tools/tests/test_crushbone_waypoint.py']
assert not subprocess.check_output(['git','status','--porcelain','--',*paths],cwd=ROOT,text=True).strip(),'Commit operation files before deployment'
source='COMMIT='+repr(commit)+'\n'
for name,file in [('FORWARD','forward.sql'),('ROLLBACK','rollback.sql'),('STATUS_SOURCE','world_status.py')]:
    source+=name+'='+repr((HERE/file).read_text(encoding='utf-8'))+'\n'
source+=(HERE/'deploy.py').read_text(encoding='utf-8')
ssh=['ssh','-i',str(Path.home()/'.ssh/nightcap_ovh'),'-o','BatchMode=yes',
     '-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202','sudo -n python3 -']
result=subprocess.run(ssh,input=source,text=True)
sys.exit(result.returncode)
