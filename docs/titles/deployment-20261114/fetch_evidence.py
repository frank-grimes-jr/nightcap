"""Collect compact terminal release proof, never the private SQL backup."""
import json
from control import HERE,remote

code='''
from pathlib import Path
import hashlib,json
s=Path('/opt/nightcap/releases/titles-live-20261114-v1');a=s/'evidence/activation'
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
deployed=read(a/'deployed.json');closed=read(a/'verified-closed.json');backup=read(a/'backup.json')
assert deployed['gateway_open'] and closed['continuation']
assert not list(a.glob('held-*.json'))
assert read(a/'resume-stopped-rpc/resolved.json')['closed_verification_passed']
print(json.dumps(dict(result='PASS',source=deployed['source'],image=deployed['image'],
    deployed_receipt_sha256=sha(a/'deployed.json'),runtime_started_at=deployed['runtime']['started_at'],
    title_sql=read(a/'titles-sql-installed.json'),
    backup={k:backup[k] for k in ['sha256','compressed_bytes','uncompressed_bytes','gzip_integrity']},
    market=closed['market'],old_player_state_checks='exact stopped snapshot and native expected boot state passed',
    resolved_hold_sha256=read(a/'resume-stopped-rpc/resolved.json')['original_hold_sha256'],
    first_backup=read(a/'resume-stopped-rpc/started.json')['first_backup'],
    restored_player_snapshot=False,owner_gameplay_accepted=False),indent=2))
'''
data=json.loads(remote(code))
(HERE/'activation-summary.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(data,indent=2))
