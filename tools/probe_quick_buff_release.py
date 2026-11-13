"""Fresh read-only live release identity probe; no player records exported."""
import json
from pathlib import Path
from quick_buff_remote import run,ART
REMOTE=r'''
from pathlib import Path
import importlib.util,json,hashlib,datetime
path=Path('/opt/nightcap/releases/augment-icons-20261112-v1/rollout.py')
spec=importlib.util.spec_from_file_location('icon_release',path);a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a);a.initialize()
r=a.r;services={n:r.compact(n) for n in ('game','gateway','db','web','tunnel')}
image=services['game']['image_id']
report=dict(captured_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 scope='Read-only production identities; player count only',services=services,
 players=a.prior.players(),image_files=r.image_hashes(image),
 publication=a.h.publication(),caches=a.h.caches(),runtime=a.r.runtime(),
 operator_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
print(json.dumps(report))
'''
if __name__=='__main__':
    ART.mkdir(parents=True,exist_ok=True)
    data=json.loads(run(REMOTE,240));(ART/'production-probe.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({k:v for k,v in data.items() if k in ('captured_at','players','services','image_files','publication')}))
