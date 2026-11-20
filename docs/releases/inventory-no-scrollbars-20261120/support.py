"""Transport and paths for the owner-approved XML-only publication."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ART=ROOT/'artifacts/inventory-no-scrollbars'
RELEASE=2026112001
STAGE='/opt/nightcap/releases/inventory-no-scrollbars-20261120-v1'
SSH=['C:/Windows/System32/OpenSSH/ssh.exe','-i','C:/Users/verre/.ssh/nightcap_ovh',
     '-o','BatchMode=yes','-o','ConnectTimeout=15','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202']
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,obj):path.write_text(json.dumps(obj,indent=2)+'\n',encoding='utf-8',newline='\n')
def remote(code,timeout=240):
    result=subprocess.run(SSH+['sudo -n python3 -'],input=code,text=True,encoding='utf-8',capture_output=True,timeout=timeout)
    if result.returncode:
        (ART/'remote-error.txt').write_text(result.stdout+'\n'+result.stderr,encoding='utf-8')
        raise RuntimeError('Remote action failed; inspect artifacts/inventory-no-scrollbars/remote-error.txt')
    return json.loads(result.stdout)
