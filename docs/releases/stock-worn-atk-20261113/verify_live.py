"""Verify the active OVH runtime, data, backup and user-facing loot projection."""
import argparse
import json
from ops import HERE, STAGE, call, save

LOAD="""
from pathlib import Path
import json,importlib.util,subprocess,gzip
stage=Path('/opt/nightcap/releases')/NAME
s=importlib.util.spec_from_file_location('atk',stage/'release.py')
q=importlib.util.module_from_spec(s);s.loader.exec_module(q);q.initialize()
a=stage/'evidence/activation';verified=q.read(a/'deployed.json');before=q.read(stage/'evidence/preflight.json')
assert verified['gateway_open'] and verified['source']==q.SOURCE
"""
def main(loot):
    if loot:
        code="""
root=q.ROOT/'data/public/wiki-data'
def check():
 current=(root/'current').resolve();index=json.loads(gzip.decompress((current/'index.json.gz').read_bytes()))
 found=set(q.targets)&{int(x['id']) for x in index['items']}
 wrong=[]
 for i in sorted(found):
  record=json.loads(gzip.decompress((current/f'item-{i}.json.gz').read_bytes()))
  assert int(record['id'])==i
  if int(record['attack'])!=q.targets[i][1]:wrong.append(i)
 return current.name,len(found),wrong
revision,applicable,wrong=check()
if wrong:
 subprocess.run(['systemctl','start','nightcap-wiki-loot.service'],check=True,timeout=650)
 revision,applicable,wrong=check()
assert not wrong
print(json.dumps(dict(snapshot=revision,era_listed_targets=applicable,checked=applicable,wrong=wrong)))
"""
    else:
        code="""
cur=q.r.running(q.m['image'],q.op.binaries())
assert cur['started_at']==verified['runtime']['started_at'] and q.r.compact('game')['health']=='healthy'
assert q.r.compact('gateway')['running'] and q.r.compact('db')['health']=='healthy' and q.a.prior.players()>=0
q.base.health();q.r.closed_ports()
for n in ('db','web','tunnel'):assert q.r.compact(n)==before['services'][n],n
assert q.h.caches()['items']==before['rehearsal']['items_sha256'] and q.h.caches()['spells']==before['caches']['spells']
assert q.sha(q.ROOT/'data/public/channel.json')==q.m['channel'] and q.r.runtime()==before['runtime']
assert q.row_check(True)==926 and q.a.prior.p.rules()==before['rules']
backup=q.read(a/'backup.json');assert backup['gzip_integrity'] and q.sha(Path(backup['path']))==backup['sha256']==verified['backup_sha256']
logs=q.r.out('docker','compose','logs','--no-color','--since',cur['started_at'],'game')
errors={k:logs.count(k) for k in ('MySQL Error','Orphaned Rule','Unknown column','Dungeon schema drift','Dungeon content drift','Dungeon item cache drift','Failed to load Alternate Advancement')}
assert not any(errors.values()),errors
processes=[row[0] for row in cur['processes']];assert processes.count('zone')==12 and cur['restart_count']==0
print(json.dumps(dict(result='PASS',source=verified['source'],image=cur['image_id'],started_at=cur['started_at'],workers=processes.count('zone'),restart_count=cur['restart_count'],runtime_errors=cur['errors'],startup_errors=errors,admissions_open=True,cache=before['rehearsal'],full_rows_checked=926,normal_guards=135,backup_sha256=backup['sha256'],backup_integrity=True,client_channel_sha256=q.m['channel'],binaries=q.op.binaries(),client_update_required=False,receipt_sha256={f:q.sha(a/f) for f in ('deployed.json','verified-closed.json','backup.json','sql-installed.json')},player_qa='open')))
"""
    data=json.loads(call(LOAD+code,timeout=900,NAME=STAGE))
    save('loot-data.json' if loot else 'production-verified.json',data)
    print(json.dumps(data))
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--loot',action='store_true');main(p.parse_args().loot)
