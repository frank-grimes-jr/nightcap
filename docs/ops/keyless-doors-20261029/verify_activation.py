"""Independent read-only full-content/runtime verification and wiki guard."""
import hashlib
import json
from pathlib import Path
from capture_baseline import remote

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]

def main():
    capture_source=(ROOT/'tools/keyless_doors_capture.py').read_text()
    runtime_source=(HERE/'runtime.py').read_text()
    report=remote('''from pathlib import Path
import json,hashlib,subprocess,datetime
base=Path('/opt/nightcap/deploy/production')
out=Path('/opt/nightcap/backups/keyless-doors-20261029')
receipt=out/'result.json';r=json.loads(receipt.read_text())
assert r['status']=='activated_verified' and r['admission_release']['held'] is False
before=json.loads((out/'before.json').read_text())
expected=json.loads(json.dumps(before['doors']))
for row in expected:row.update(keyitem=0,lockpick=0)
''' + 'ns={"__name__":"capture"};exec('+repr(capture_source)+',ns)\n' + '''
actual=ns['capture']()
assert actual['doors']==expected
assert not any(row['keyitem'] or row['lockpick'] for row in actual['doors'])
for name,s in r['services'].items():
 row=json.loads(subprocess.check_output(['docker','inspect',name],text=True))[0]
 assert row['Id']==s['id'] and row['Image']==s['image'] and row['State']['StartedAt']==s['start'] and row['RestartCount']==s['restarts']
 assert row['State']['Running'] and not row['State']['OOMKilled'] and row['State'].get('Health',{}).get('Status','healthy')=='healthy'
affected=sorted({row['zone'] for row in before['doors'] if row['keyitem'] or row['lockpick']})
''' + 'runtime_source='+repr(runtime_source)+'\n' + r'''
code='AFFECTED='+repr(affected)+'\nMODE="probe"\n'+runtime_source
now=json.loads(subprocess.check_output(['docker','compose','exec','-T','game','python3','-'],cwd=base,input=code,text=True))
old=json.loads((out/'runtime-before.json').read_text())
identity=lambda a:sorted((row['pid'],row['start']) for row in a['workers'])
assert identity(now)==identity(old) and now['locks']==r['admission_locks_before']
print(json.dumps(dict(verified=True,verified_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 main=r['main'],door_rows=len(expected),remaining_locks=0,worker_lifetimes_preserved=True,
 native_locks_restored=True,services=r['services'],runtime_receipt=str(receipt),
 runtime_receipt_sha256=hashlib.sha256(receipt.read_bytes()).hexdigest(),
 channel_sha256=hashlib.sha256((base/'data/public/channel.json').read_bytes()).hexdigest())))
''')
    (HERE/'activation-guard.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ['verified','door_rows','remaining_locks','native_locks_restored']}))

if __name__=='__main__':
    main()
