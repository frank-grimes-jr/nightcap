"""Start or inspect the guarded whole-game maintenance unit without replaying it."""
import argparse
import hashlib
import json
import time

from probe import HERE, STAGE, remote, write


def main(start):
    source = (HERE/"maintenance.py").read_bytes().replace(b"\r\n",b"\n")
    digest = hashlib.sha256(source).hexdigest()
    code = """
import fcntl, hashlib, json, os, subprocess
from pathlib import Path
root = Path('/opt/nightcap/releases')/stage
assert hashlib.sha256((root/'manifest.json').read_bytes()).hexdigest()==manifest
unit = 'nightcap-'+stage+'-maintenance'
log = root/'maintenance.log'
if start:
    with Path('/opt/nightcap/deploy/production/.deployment.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not (root/'evidence').exists() and not (root/'drain-started.json').exists()
        file = root/'maintenance.py'
        with file.open('xb') as f:
            f.write(source)
            f.flush()
            os.fsync(f.fileno())
        file.chmod(0o600)
        assert hashlib.sha256(file.read_bytes()).hexdigest()==digest
        with log.open('x') as f:
            f.write('Maintenance driver '+digest+'\\n')
        subprocess.run(['systemd-run','--unit='+unit,'--property=WorkingDirectory='+str(root),
            '--property=StandardOutput=append:'+str(log),'--property=StandardError=append:'+str(log),
            '/usr/bin/python3','-B',str(file)],check=True,stdout=subprocess.DEVNULL)
state = subprocess.check_output(['systemctl','show',unit,'--property=LoadState,ActiveState,Result,ExecMainStatus'],text=True)
receipts = sorted(str(f.relative_to(root)) for f in (root/'evidence').rglob('*.json'))
drain = root/'drain-started.json'
print(json.dumps(dict(state=state.splitlines(),receipts=receipts,drain=json.loads(drain.read_bytes()) if drain.exists() else None,
                      log=log.read_text()[-1200:] if log.is_file() else '')))
"""
    manifest = json.loads((HERE/"staged.json").read_bytes())
    expected = hashlib.sha256((json.dumps(manifest,indent=2)+"\n").encode()).hexdigest()
    result = json.loads(remote("stage="+repr(STAGE)+"\nstart="+repr(start)+"\nsource="+repr(source if start else b"")+
                               "\ndigest="+repr(digest)+"\nmanifest="+repr(expected)+"\n"+code))
    if start:
        write("maintenance-start.json",dict(driver_sha256=digest,manifest_sha256=expected))
    return result


def observe():
    previous = None
    while True:
        result = main(False)
        current = (tuple(result["state"]),bool(result["drain"]),tuple(result["receipts"]))
        if current != previous:
            print(json.dumps(result,indent=2),flush=True)
            previous = current
        if "evidence/activation/deployed.json" in result["receipts"]:
            from control import combat
            combat.verify()
            return
        if "ActiveState=active" not in result["state"] and "ActiveState=activating" not in result["state"]:
            raise RuntimeError("Maintenance stopped without a deployed receipt: "+result["log"])
        time.sleep(45)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--start",action="store_true")
    mode.add_argument("--observe",action="store_true")
    args = parser.parse_args()
    if args.observe:
        observe()
    else:
        print(json.dumps(main(args.start),indent=2))
