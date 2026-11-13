"""Independently verify active binaries, worker health, catalog, cache and backup after reopening."""
import json
from probe import HERE, ROOT, remote
from stage import STAGE
from pathlib import Path

def main():
    catalog=json.loads((ROOT/'config/classic-raid-augments.json').read_bytes())
    names={i['id']:i['name'] for i in catalog}
    script="""
import hashlib,importlib.util,json,subprocess
from pathlib import Path
stage=Path('/opt/nightcap/releases')/NAME
spec=importlib.util.spec_from_file_location('raid',stage/'rollout.py');op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op);op.initialize()
before=op.read(stage/'evidence/preflight.json');folder=stage/'evidence/activation';done=op.read(folder/'deployed.json')
assert done['gateway_open'] and done['items']==16 and done['source']==op.m['source_revision']
current=op.r.running(before['image'],op.binaries())
assert current['started_at']==done['runtime']['started_at']
op.base.health();op.r.closed_ports()
for s in ('db','web','tunnel'):
 assert op.r.compact(s)==before['services'][s]
assert op.r.compact('gateway')['running'] and op.r.compact('game')['health']=='healthy'
catalog={int(line.split('\\t')[0]):line.split('\\t')[1] for line in op.sql('SELECT id,Name FROM items WHERE id BETWEEN 963200 AND 963215 ORDER BY id').splitlines()}
assert catalog==NAMES
assert op.trophy_digest()==before['rehearsal']['raid_rows']
assert op.h.caches()['items']==before['rehearsal']['sha256']
assert op.h.caches()['spells']==before['caches']['spells']
assert op.sha(op.ROOT/'data/public/channel.json')==op.m['client_channel_sha256']
backup=op.read(folder/'backup.json')
assert backup['gzip_integrity'] and backup['compressed_bytes']>0 and op.sha(Path(backup['path']))==backup['sha256']
logs=op.r.out('docker','compose','logs','--no-color','--since',current['started_at'],'game')
errors={msg:logs.count(msg) for msg in ('MySQL Error','Orphaned Rule','Unknown column','Dungeon schema drift','Dungeon content drift','Dungeon item cache drift','Failed to load Alternate Advancement')}
assert not any(errors.values())
result=dict(status='PASS',source=done['source'],game=op.r.compact('game'),runtime=current,gateway_open=True,
 item_count=len(catalog),item_cache=before['rehearsal']['sha256'],unchanged_stock_items=before['rehearsal']['original_items'],
 client_channel_sha256=op.m['client_channel_sha256'],binaries=op.m['binaries'],backup_verified=True,backup_sha256=backup['sha256'],receipt_sha256={n:op.sha(folder/n) for n in ('backup.json','sql-installed.json','verified-closed.json','deployed.json')},errors=errors,player_qa='open')
print(json.dumps(result))
"""
    data=json.loads(remote('NAME='+repr(STAGE)+'\nNAMES='+repr(names)+'\n'+script,timeout=300))
    (HERE/'deployed.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
    print(json.dumps(data))
if __name__=='__main__':main()
