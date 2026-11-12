"""Run actual publication and rollout fault tests with Linux fsync and mode semantics."""
import json
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'docs/releases/imitate-death-20261112/deployment'
if __name__=='__main__':
    paths=['docs/releases/imitate-death-20261112/deployment/rollout.py','tools/tests/test_imitate_death_rollout.py']
    sources={p:(ROOT/p).read_text(encoding='utf-8') for p in paths}
    code=r'''
from pathlib import Path
import tempfile,subprocess,json,sys
root=Path(tempfile.mkdtemp(prefix='nightcap-imitate-death-linux-'))
for name,text in SOURCES.items():
 p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
results=[]
for folder,pattern,count in [('tools/tests','test_imitate_death_rollout.py',9)]:
 p=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s',folder,'-p',pattern,'-v'],cwd=root,text=True,capture_output=True)
 print(p.stdout+p.stderr,flush=True);assert p.returncode==0
 assert 'skipped=' not in p.stderr
 results.append(dict(folder=folder,tests=count,status='PASS'))
print('REPORT='+json.dumps(dict(status='PASS',checks=results)))
'''
    result=subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-'],input=f'SOURCES={sources!r}\n'+code,text=True,encoding='utf-8',capture_output=True,timeout=240)
    (OUT/'linux-tests.log').write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
    print((result.stdout+result.stderr)[-1700:])
    if result.returncode:raise SystemExit(result.returncode)
    line=next(x[7:] for x in result.stdout.splitlines() if x.startswith('REPORT='))
    (OUT/'linux-tests.json').write_text(json.dumps(json.loads(line),indent=2)+'\n')
