"""Verify signed manifest and optionally every HTTPS asset using launcher policy."""
import json
import shutil
import subprocess
import sys
from pathlib import Path
from remote import run

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
STAGE=ROOT.parent/'thj-parity-production-stage'
hosted=sys.argv[1:]==['--hosted']
command=ROOT/'eq-launcher/cmd/thj-release-verify'
command.mkdir(exist_ok=False)
shutil.copyfile(HERE/'verify-client.go',command/'main.go')
try:
    args=['E:/EQ_Local_Dev/artifacts/toolchains/go1.27.1/go/bin/go.exe','run','./cmd/thj-release-verify',
          '-previous',str(STAGE/'client/previous-channel.json'),'-expected',str(STAGE/'client/channel.json')]
    if hosted:args+=['-hosted']
    output=subprocess.check_output(args,cwd=ROOT/'eq-launcher')
finally:
    (command/'main.go').unlink();command.rmdir()
record=json.loads(output)
target=HERE/('hosted-verification.json' if hosted else 'signed-verification.json')
with target.open('xb') as f:f.write(output)
if hosted:
    source="from pathlib import Path\np=Path('/opt/nightcap/releases/thj-parity-20261018/client/hosted-verification.json')\nwith p.open('xb') as f:f.write("+repr(output)+")\n"
    run(source)
print(output.decode())
