import json,hashlib,sys
from pathlib import Path
root=Path.cwd();h=root/'docs/releases/thj-behaviors-20261019/deployment';records=[]
for rel,remote in [('thj-all-class-aa-20261019','all-class-aa-production-20261019.tar.gz'),('thj-parity-20261018','thj-parity-production-20261018.tar.gz')]:
 r=json.loads((root/f'docs/releases/{rel}/deployment/upload.json').read_text());p=Path(r['path']);assert hashlib.sha256(p.read_bytes()).hexdigest()==r['sha256'];records.append({'path':'/home/ubuntu/'+remote,'sha256':r['sha256'],'local_retained':str(p)})
sys.path.insert(0,str(root/'docs/releases/thj-all-class-aa-20261019/deployment'));from remote import run
source='''import json,hashlib,shutil,sys
from pathlib import Path
sys.path.insert(0,'/opt/nightcap/releases/zone-hunt-20261009');import runtime_ops as r
stage=Path('/opt/nightcap/releases/thj-behaviors-live-20261019');assert not (stage/'evidence/activation-started.json').exists()
services={s:r.compact(s) for s in ('game','gateway','db','web','tunnel')}
records=RECORDS
for row in records:
 p=Path(row['path']);assert p.parent==Path('/home/ubuntu') and not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==row['sha256']
for row in records:Path(row['path']).unlink()
assert services=={s:r.compact(s) for s in services}
print(json.dumps({'removed_redundant_transfers':records,'local_copies_verified':True,'services_preserved':True,'free_bytes':shutil.disk_usage(stage).free}))
'''.replace('RECORDS',repr(records))
receipt=run(source);(h/'redundant-transfers.json').write_bytes(receipt);print(receipt.decode())
