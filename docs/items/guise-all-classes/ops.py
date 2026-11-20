"""Stage the Guise correction and run the inherited maintenance workflow."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "docs/releases/classic-raid-augments-20261112"))
from probe import remote
STAGE = "guise-all-classes-20261120-v1"

def stage():
    source = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    before = json.loads((HERE / "before.json").read_bytes())
    fields = ["ID", "Classes", "Races"]
    code = '#include "common/item_data.h"\n#include <cstdio>\n#include <cstddef>\nint main(){printf("%zu",sizeof(EQ::ItemData));' + "".join('printf(" %zu",offsetof(EQ::ItemData,' + field + '));' for field in fields) + "}"
    command = "cd /tmp/nightcap-raid-augments-shipping-20261112-v3 && clang++ -std=c++20 -Isource -xc++ - -o /tmp/nightcap-guise-layout && /tmp/nightcap-guise-layout"
    layout = list(map(int, subprocess.check_output(["docker", "exec", "-i", "akk-stack-eqemu-server-1", "sh", "-c", command], input=code.encode()).split()))
    assert layout[:2] == [1332, 440]
    data = {}
    for name in ("release.py", "catalog.py", "before.json"):
        path = HERE / name
        content = subprocess.check_output(["git", "show", source + ":" + path.relative_to(ROOT).as_posix()], cwd=ROOT)
        assert content == path.read_bytes().replace(b"\r\n", b"\n")
        data[name] = content
    manifest = {key: before[key] for key in ("image", "binaries", "caches", "channel", "stock_operator", "focus_operator")}
    manifest.update(source=source, client=before["client"], layout=dict(zip(["size"]+fields, layout)),
                    files={name:hashlib.sha256(content).hexdigest() for name,content in data.items()})
    data["manifest.json"] = (json.dumps(manifest, indent=2)+"\n").encode()
    code = """
import base64,hashlib,json,os
from pathlib import Path
os.umask(0o077)
folder=Path('/opt/nightcap/releases')/stage
folder.mkdir(exist_ok=True,mode=0o700)
for name,encoded in data.items():
 assert Path(name).name==name
 raw=base64.b64decode(encoded,validate=True)
 path=folder/name
 if path.exists():assert not path.is_symlink() and path.read_bytes()==raw
 else:
  with path.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
print(stage)
"""
    print(remote("stage="+repr(STAGE)+"\ndata="+repr({name:base64.b64encode(content).decode() for name,content in data.items()})+"\n"+code))
    (HERE / "staged.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf8")

def action(name, start):
    code = """
from pathlib import Path
import subprocess,json
folder=Path('/opt/nightcap/releases')/stage
cmd=['/usr/bin/python3','-B',str(folder/'release.py'),action]
if action=='verify':
 print(subprocess.check_output(cmd,text=True))
else:
 unit='nightcap-'+stage+'-'+action
 log=folder/(action+'.log')
 if start:
  subprocess.run(['systemd-run','--unit='+unit,'--property=WorkingDirectory='+str(folder),'--property=StandardOutput=append:'+str(log),'--property=StandardError=append:'+str(log),*cmd],check=True)
 state=subprocess.check_output(['systemctl','show',unit,'--property=ActiveState,Result,ExecMainStatus'],text=True)
 print(json.dumps(dict(state=state.splitlines(),log=log.read_text()[-1700:] if log.exists() else '',receipts=[str(p.relative_to(folder)) for p in (folder/'evidence').rglob('*.json')])))
"""
    result = remote("stage="+repr(STAGE)+"\naction="+repr(name)+"\nstart="+repr(start)+"\n"+code)
    if name == "verify":
        (HERE / "production-verified.json").write_text(json.dumps(json.loads(result),indent=2)+"\n",encoding="utf8")
    print(result)

if __name__ == "__main__":
    cli=argparse.ArgumentParser()
    cli.add_argument("action",choices=("stage","preflight","activate","verify"))
    cli.add_argument("--start",action="store_true")
    args=cli.parse_args()
    stage() if args.action=="stage" else action(args.action,args.start)

