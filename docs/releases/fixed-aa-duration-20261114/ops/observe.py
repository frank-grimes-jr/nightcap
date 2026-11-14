"""Follow the durable deployment through its independent open-access verification."""
import json
import time
from control import combat
from probe import STAGE,remote


def state():
    code = """
import json, subprocess
from pathlib import Path
root = Path('/opt/nightcap/releases')/stage
unit = 'nightcap-'+stage+'-deploy'
stat = subprocess.check_output(['systemctl','show',unit,'--property=ActiveState,Result,ExecMainStatus'],text=True).splitlines()
files = sorted(str(p.relative_to(root)) for p in (root/'evidence').rglob('*.json'))
log = root/'deploy.log'
tail = log.read_text().splitlines()[-2:] if log.is_file() else []
print(json.dumps(dict(unit=stat,receipts=files,log=tail,drain=(root/'drain-started.json').is_file())))
"""
    return json.loads(remote("stage="+repr(STAGE)+"\n"+code))


def monitor():
    previous = None
    while True:
        now = state()
        if now != previous:
            print(json.dumps(now),flush=True)
            previous = now
        if "evidence/activation/deployed.json" in now["receipts"]:
            combat.verify()
            return
        if "ActiveState=active" not in now["unit"] and "ActiveState=activating" not in now["unit"]:
            raise RuntimeError(now)
        time.sleep(45)


if __name__ == "__main__":
    monitor()
