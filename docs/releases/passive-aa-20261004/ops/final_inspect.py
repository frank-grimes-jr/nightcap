"""Independently verify hosted release identities and persistent rules after rollout."""
import json,subprocess
from pathlib import Path
r=Path(__file__).parent
ssh=['ssh','-i',str(Path.home()/'.ssh/nightcap_ovh'),'-o','BatchMode=yes','-o','ConnectTimeout=15','ubuntu@135.148.47.202']
result=subprocess.run(ssh+['sudo -n python3 -'],input=(r/'inspect_host.py').read_text(),text=True,capture_output=True,check=True,timeout=120)
d=json.loads(result.stdout)
before=json.loads((r/'hosted-before.json').read_text())
m=json.loads((r/'server-stage/manifest.json').read_text())
assert d['image']==m['new_image']
assert d['hashes']=={**before['hashes'],**{'bin/'+n:h for n,h in m['binaries'].items()}}
assert d['public']==before['public']
for s in ('db','web','tunnel'):assert d['services'][s]==before['services'][s]
assert d['services']['game']['health']=='healthy' and d['services']['game']['restarts']==0
assert d['services']['game']['running'] and d['services']['gateway']['running']
assert '1\tAA:PassiveExpPercent\t1' in d['rules']
assert '1\tCharacter:AAExpMinLevel\t1' in d['rules']
with (r/'hosted-after.json').open('x') as f:f.write(result.stdout)
print(json.dumps({'verified':True,'services':d['services'],'rules':d['rules'],'client_release':d['public']['channel.json']['signed']['release']}))
