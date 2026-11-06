"""Launch/poll a specific detached release job; never restart an existing action."""
import argparse
import json
import subprocess
from probe import SSH

STAGE='/opt/nightcap/releases/augment-audit-20261106-v1'


def main(mode,action):
    prefix=f'STAGE={STAGE!r}\nACTION={action!r}\n'
    code='''from pathlib import Path
import json,os,subprocess
stage=Path(STAGE);job=stage/'jobs'/ACTION
'''
    if mode=='start':
        runner="""import json,subprocess,time,os
from pathlib import Path
job=Path(JOB);stage=Path(STAGE)
start=time.time()
p=subprocess.run(['/usr/bin/python3',str(stage/'rollout.py'),ACTION],cwd=stage)
result={'action':ACTION,'returncode':p.returncode,'started':start,'ended':time.time()}
with (job/'result.json').open('x') as f:json.dump(result,f);f.flush();os.fsync(f.fileno())
"""
        code+=f'''job.mkdir(mode=0o700,parents=True,exist_ok=False)
runner=job/'runner.py';runner.write_text('JOB='+repr(str(job))+'\\nSTAGE='+repr(STAGE)+'\\nACTION='+repr(ACTION)+'\\n'+{runner!r});runner.chmod(0o600)
with (job/'private.log').open('xb') as log:
 p=subprocess.Popen(['/usr/bin/python3',str(runner)],cwd=stage,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
start_ticks=Path('/proc/'+str(p.pid)+'/stat').read_text().split()[21]
identity={{'pid':p.pid,'start_ticks':start_ticks,'action':ACTION}}
with (job/'identity.json').open('x') as f:json.dump(identity,f);f.flush();os.fsync(f.fileno())
print(json.dumps({{'status':'started','job':str(job),**identity}}))
'''
    else:
        code+='''identity=json.loads((job/'identity.json').read_text());proc=Path('/proc/'+str(identity['pid'])+'/stat')
running=proc.exists() and proc.read_text().split()[21]==identity['start_ticks']
result=json.loads((job/'result.json').read_text()) if (job/'result.json').exists() else None
tail=(job/'private.log').read_text(errors='replace').splitlines()[-12:]
print(json.dumps({'job':str(job),'running':running,'result':result,'tail':tail}))
'''
    result=subprocess.run(SSH+['sudo -n python3 -'],input=prefix+code,text=True,encoding='utf-8',capture_output=True,timeout=40)
    if result.returncode:raise RuntimeError(result.stderr[-2000:])
    print(result.stdout)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('mode',choices=('start','poll'));parser.add_argument('action',choices=('preflight','activate','rollback','open'))
    args=parser.parse_args();main(args.mode,args.action)
