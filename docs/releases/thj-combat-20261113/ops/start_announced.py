"""Install the one-shot owner-approved maintenance continuation and start it durably."""
import hashlib
from pathlib import Path
from probe import remote,STAGE


if __name__=="__main__":
    script=Path(__file__).with_name("announced.py").read_bytes().replace(b"\r\n",b"\n")
    print(remote(f"stage={STAGE!r}\nscript={script!r}\npin={hashlib.sha256(script).hexdigest()!r}\n"+"""
import fcntl,hashlib,os,subprocess
from pathlib import Path
root=Path('/opt/nightcap/releases')/stage
file=root/'announced.py'
with Path('/opt/nightcap/deploy/production/.deployment.lock').open('a') as lock:
    fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    assert not (root/'evidence').exists() and not file.exists()
    assert (root/'preflight.log').read_text().rstrip().endswith('AssertionError: Players online')
    with file.open('xb') as f:
        f.write(script)
        f.flush()
        os.fsync(f.fileno())
    file.chmod(0o600)
    assert hashlib.sha256(file.read_bytes()).hexdigest()==pin
log=root/'announced.log'
with log.open('x') as f:
    f.write('Authenticated maintenance continuation '+pin+'\\n')
subprocess.run(['systemd-run','--unit=nightcap-'+stage+'-announced','--property=WorkingDirectory='+str(root),
    '--property=StandardOutput=append:'+str(log),'--property=StandardError=append:'+str(log),
    '/usr/bin/python3','-B',str(file)],check=True,stdout=subprocess.DEVNULL)
print('Started announced maintenance '+pin)
""").strip())
