"""Exclusively stage/start or inspect the reviewed checkpoint continuation."""
import hashlib
import json
from pathlib import Path
import sys
from control import remote,HERE

source=(HERE/'resume.py').read_text(encoding='utf8').replace('\r\n','\n')
pin=hashlib.sha256(source.encode()).hexdigest()
start=sys.argv[1:]==['--start']
assert sys.argv[1:] in [[],['--start']]
code='source='+repr(source)+'\npin='+repr(pin)+'\nstart='+repr(start)+'\n'+'''
import fcntl,hashlib,json,subprocess
from pathlib import Path
stage=Path('/opt/nightcap/releases/titles-live-20261114-v1')
unit='nightcap-titles-live-20261114-v1-resume'
log=stage/'resume.log'
if start:
    assert hashlib.sha256(source.encode()).hexdigest()==pin
    with Path('/opt/nightcap/deploy/production/.deployment.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (stage/'resume.py').exists() and not log.exists()
        assert not (stage/'evidence/activation/titles-sql-started.json').exists()
        assert subprocess.check_output(['systemctl','show','nightcap-titles-live-20261114-v1-deploy.service','--property=ActiveState','--value'],text=True).strip()=='failed'
        with (stage/'resume.py').open('x') as stream:stream.write(source)
        (stage/'resume.py').chmod(0o600)
        log.touch(exist_ok=False)
    subprocess.run(['systemd-run','--unit='+unit,'--property=WorkingDirectory='+str(stage),
        '--property=StandardOutput=append:'+str(log),'--property=StandardError=append:'+str(log),
        '/usr/bin/python3','-B',str(stage/'resume.py')],check=True,stdout=subprocess.DEVNULL)
state=subprocess.check_output(['systemctl','show',unit,'--property=ActiveState,Result,ExecMainStatus'],text=True)
print(json.dumps(dict(state=state.splitlines(),receipts=sorted(str(p.relative_to(stage)) for p in (stage/'evidence').rglob('*.json')),log=log.read_text()[-1600:] if log.exists() else '')))
'''
print(remote(code,timeout=600))
if start:(HERE/'resume-staged.json').write_text(json.dumps(dict(source_sha256=pin,one_shot=True),indent=2)+'\n')
