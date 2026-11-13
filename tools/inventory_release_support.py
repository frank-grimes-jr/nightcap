"""Bounded pinned-host transport for this owner-authorized Inventory release."""
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]
HERE=ROOT/'docs/releases/heroic-stats-inventory-20261112'
ART=ROOT/'artifacts/heroic-stats'
SSH=['C:/Windows/System32/OpenSSH/ssh.exe','-i','C:/Users/verre/.ssh/nightcap_ovh',
     '-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202']
STAGE='/opt/nightcap/releases/inventory-combat-stats-20261112-v1'
AUTHORIZATION='Yes, implement it to match the screenshot, including the caps and combat stats above. Use the correct server values for MIT and AVD, and publish it for live testing.'


def remote(code,timeout=240):
    p=subprocess.run(SSH+['sudo -n python3 -'],input=code,text=True,encoding='utf-8',capture_output=True,timeout=timeout)
    if p.returncode:raise RuntimeError(p.stderr[-3500:]+p.stdout[-2000:])
    return json.loads(p.stdout)


def save(path,value):
    path.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
