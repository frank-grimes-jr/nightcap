"""Read-only current client/wiki/services baseline; fetch verified public assets."""
import base64,datetime,hashlib,json,subprocess
from pathlib import Path
from urllib.request import Request,urlopen

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
PRIVATE=ROOT/'.local/cast-bar/release'
SSH=['C:/Windows/System32/OpenSSH/ssh.exe','-i','C:/Users/verre/.ssh/nightcap_ovh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202']

def remote(code,timeout=240):
    p=subprocess.run(SSH+['sudo -n python3 -'],input=code,text=True,capture_output=True,timeout=timeout)
    if p.returncode:raise RuntimeError((p.stdout+p.stderr)[-4000:])
    return json.loads(p.stdout)
