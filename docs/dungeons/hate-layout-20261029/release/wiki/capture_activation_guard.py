"""Read the completed paired-release receipts and pin current service identities.

Call only after the release owner has verified open admissions and the signed
client. No publication or service mutation occurs here.
"""
import json
from pathlib import Path

from capture_baseline import remote

HERE = Path(__file__).resolve().parent
RUNTIME = '/opt/nightcap/releases/hate-layout-20261029-v1/evidence/activation/deployed.json'
CLIENT = '/opt/nightcap/releases/hate-client-2026102901/published.json'


def main():
    assert not (HERE / 'wiki-publication.json').exists(), 'Inspect already-published release'
    client = json.loads((HERE.parent / 'client/published.json').read_text())
    assert client['release'] == 2026102901
    result = remote(f'''from pathlib import Path
import fcntl,hashlib,json,subprocess
base=Path('/opt/nightcap/deploy/production')
runtime_path=Path({RUNTIME!r});client_path=Path({CLIENT!r})
with (base/'.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 runtime=json.loads(runtime_path.read_text());client=json.loads(client_path.read_text())
 assert runtime['gateway_open'] is True and runtime['database_restored'] is False
 assert runtime['owner_gameplay_accepted'] is False
 assert client['release']==2026102901 and client['channel_sha256']=={client['channel_sha256']!r}
 assert hashlib.sha256((base/'data/public/channel.json').read_bytes()).hexdigest()==client['channel_sha256']
 services={{}}
 for name in ['game','gateway','db','web','tunnel']:
  cid=subprocess.check_output(['docker','compose','ps','-aq',name],cwd=base,text=True).strip()
  row=json.loads(subprocess.check_output(['docker','inspect',cid],text=True))[0]
  assert row['State']['Running'] and not row['State']['OOMKilled'],name
  if name in ['game','db']:assert row['State']['Health']['Status']=='healthy',name
  if name=='game':
   assert row['Image']==runtime['runtime']['image_id']
   assert row['State']['StartedAt']==runtime['runtime']['started_at']
   assert row['RestartCount']==runtime['runtime']['restart_count']
  services[name]={{k:row[k] for k in ['Id','Image','RestartCount']}}
  services[name]['state']={{k:row['State'][k] for k in ['Running','StartedAt','OOMKilled']}}
 print(json.dumps(dict(verified=True,runtime_receipt=str(runtime_path),client_receipt=str(client_path),
  runtime_receipt_sha256=hashlib.sha256(runtime_path.read_bytes()).hexdigest(),
  client_receipt_sha256=hashlib.sha256(client_path.read_bytes()).hexdigest(),
  channel_sha256=client['channel_sha256'],services_after=services,
  owner_gameplay_accepted=False)))
''')
    (HERE / 'activation-guard.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'verified': True, 'game_image': result['services_after']['game']['Image'],
                      'channel_sha256': result['channel_sha256']}))


if __name__ == '__main__':
    main()
