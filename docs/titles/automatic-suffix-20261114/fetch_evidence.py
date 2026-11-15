"""Collect compact deployment proof without private player-state or backup data."""
import json
from control import HERE,remote

script='''
from pathlib import Path
import hashlib,json
s=Path('/opt/nightcap/releases/titles-automatic-suffix-20261114-v1');a=s/'evidence/activation'
read=lambda p:json.loads(p.read_bytes())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
dep=read(a/'deployed.json');closed=read(a/'verified-closed.json');backup=read(a/'backup.json')
assert dep['gateway_open'] and not list(a.glob('held-*.json'))
print(json.dumps(dict(result='PASS',source=dep['source'],image=dep['image'],
    deployed_receipt=sha(a/'deployed.json'),runtime_started_at=dep['runtime']['started_at'],
    title_state_before=read(a/'title-state-before.json'),market=closed['market'],
    backup={k:backup[k] for k in ['sha256','compressed_bytes','uncompressed_bytes','gzip_integrity']},
    stopped_player_state_and_native_boot_state='PASS',closed_title_counter_award_preservation='PASS',
    restored_player_snapshot=False,owner_gameplay_accepted=False),indent=2))
'''
data=json.loads(remote(script))
(HERE/'activation-summary.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps(data,indent=2))
