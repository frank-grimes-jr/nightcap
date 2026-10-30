"""Execute one reviewed action; retain detailed logs/receipts exclusively on-host."""
from pathlib import Path
import hashlib,json,subprocess,sys
from stage_release import SSH,STAGE
HERE=Path(__file__).resolve().parent
action=sys.argv[1];assert action in ('preflight','activate','open','rollback','open-rollback')
resume='--normalization' in sys.argv[2:];assert not (resume and action=='preflight')
operator='resume_normalization.py' if resume else 'rollout.py'
label=action+('-normalization' if resume else '')
pin=hashlib.sha256((HERE/operator).read_bytes()).hexdigest()
code=f'''from pathlib import Path
import hashlib,json,subprocess
stage=Path({STAGE!r});action={action!r};operator={operator!r};label={label!r}
assert hashlib.sha256((stage/operator).read_bytes()).hexdigest()=={pin!r}
log=stage/('action-'+label+'.log');assert not log.exists(),'Inspect existing action before any continuation'
with log.open('x') as f:
 p=subprocess.run(['python3','-B',str(stage/operator),action],stdout=f,stderr=subprocess.STDOUT,cwd=stage)
if p.returncode:
 print(json.dumps({{'action':action,'status':'held_or_failed','log_tail':log.read_text()[-2500:],'returncode':p.returncode}}))
 raise SystemExit(p.returncode)
report={{'action':action,'status':'passed','private_receipts_retained_on_host':True}}
if action=='preflight':
 r=json.loads((stage/'evidence/preflight.json').read_text());report.update(checks=r['checks'],candidate_image=r['image'])
else:
 name='deployed.json' if action in ('open','open-rollback') else 'verified-closed.json'
 folder='recovery' if action in ('rollback','open-rollback') else 'activation'
 r=json.loads((stage/'evidence'/folder/name).read_text())
 report.update(checks=r['checks'],state_tables=r['state_tables'],image_id=r['runtime']['image_id'],started_at=r['runtime']['started_at'],restart_count=r['runtime']['restart_count'],zone_workers=sum(n=='zone' for n,h in r['runtime']['processes']),errors=r['runtime']['errors'],gateway_open=action in ('open','open-rollback'),database_restored=False,owner_gameplay_accepted=False)
print(json.dumps(report))
'''
p=subprocess.run(SSH+['sudo -n python3 -'],input=code,text=True,encoding='utf-8',capture_output=True,timeout=1500)
(HERE/'private'/('action-'+label+'.log')).write_text(p.stdout+p.stderr,encoding='utf-8')
if p.stdout:
 report=json.loads(p.stdout);(HERE/(label+'-receipt.json')).write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
if p.returncode:
 print(p.stderr[-2000:]);raise SystemExit(p.returncode)
