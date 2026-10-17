import ast,json,subprocess
from pathlib import Path
root=Path(__file__).resolve().parent
payload='RELOAD_SOURCE='+repr((root/'reload_rules.py').read_text())+'\n'+(root/'apply.py').read_text()
ast.parse(payload)
p=subprocess.run(['C:/Windows/System32/OpenSSH/ssh.exe','-i','C:/Users/verre/.ssh/nightcap_ovh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202','sudo -n python3 -'],input=payload,text=True,capture_output=True,timeout=180)
(root.parent/'activation.log').write_text(p.stdout+'\n'+p.stderr)
if p.returncode: raise SystemExit('Operation failed: inspect remote receipt before any retry. '+p.stderr)
result=json.loads(p.stdout.splitlines()[-1])
(root.parent/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('reload_logs','binaries','backup_sha256')},indent=2))
