"""Verify the published payload with curl (Python urllib is rejected at the edge)."""
from pathlib import Path
import concurrent.futures
import datetime
import hashlib
import json
import subprocess

ROOT=Path(__file__).resolve().parents[3]
manifest=json.loads((ROOT/'artifacts/loot-wiki/wiki.tar.json').read_text())
def verify(pair):
    name,expected=pair
    data=subprocess.check_output(['curl.exe','--fail','--silent','--show-error',
        '--max-time','30','https://wiki.nightcapgame.org/'+name])
    return name,hashlib.sha256(data).hexdigest()==expected
with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
    results=list(pool.map(verify,manifest.items()))
assert all(ok for _,ok in results),[name for name,ok in results if not ok]
report={'result':'PASS','release':'20261018-loot-quality-v1',
        'verified_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'public_files_verified':len(results),'all_sha256_match':True,'owner_balance_accepted':False}
(Path(__file__).parent/'wiki-public-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
