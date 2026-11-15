"""Verify the explicitly reviewed augment-only successor without replaying titles."""
import hashlib
import json
import tarfile
from pathlib import Path
from control import HERE,ROOT,remote

sha=lambda b:hashlib.sha256(b).hexdigest()
package=Path('E:/EQ_Local_Dev/artifacts/classic-augment-stacking')
with tarfile.open(package/'classic-augment-stacking-20261114-v1.tar.gz') as archive:
    manifest_raw=archive.extractfile('manifest.json').read();manifest=json.loads(manifest_raw)
    for name,pin in manifest['files'].items():assert sha(archive.extractfile(name).read())==pin
    build=json.loads(archive.extractfile('build.json').read())
assert manifest['source']=='acb232e10453f683ba099d82ba794467381108ab'
assert manifest['image']==json.loads((HERE/'activation-summary.json').read_bytes())['image']
assert manifest['base_hashes']=={**json.loads((HERE/'staged.json').read_bytes())['base_hashes'],'bin/zone':json.loads((HERE/'shipping-candidate.json').read_bytes())['zone']}
assert build==json.loads((ROOT/'docs/items/classic-augment-stacking/build.json').read_bytes())
assert build['baseline']=={'zone':manifest['base_hashes']['bin/zone']}
assert build['patch']==sha((package/'feature.patch').read_bytes())
assert manifest['binaries']==build['binaries']
assert manifest['files']['release.py']==sha((ROOT/'docs/items/classic-augment-stacking/release.py').read_bytes().replace(b'\r\n',b'\n'))
proof=dict(stage='classic-augment-stacking-20261114-v1',manifest_sha256=sha(manifest_raw),
    operator=manifest['files']['release.py'],zone=manifest['binaries']['zone'],
    title_baseline=manifest['base_hashes']['bin/zone'],source=manifest['source'],
    reviewed_delta='Only augment socket compatibility and swap validation; title policy, queue hooks and notifications retained',
    rebuild_script_sha256=sha((package/'rebuild.py').read_bytes()),feature_patch_sha256=sha((package/'feature.patch').read_bytes()))
(HERE/'successor.json').write_text(json.dumps(proof,indent=2)+'\n')
script='pins='+repr(proof)+'\ntitle_operator='+repr(json.loads((HERE/'staged.json').read_bytes())['files']['release.py'])+'\n'+'''
from pathlib import Path
import fcntl,hashlib,importlib.util,json,subprocess,sys
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_bytes())
root=Path('/opt/nightcap/deploy/production');titles=Path('/opt/nightcap/releases/titles-automatic-suffix-20261114-v1')
stage=titles.parent/pins['stage'];active=stage/'evidence/activation'
with (root/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
 for handle in (lock,gm):fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert sha(stage/'manifest.json')==pins['manifest_sha256'] and sha(stage/'release.py')==pins['operator']
 m=read(stage/'manifest.json')
 for name,pin in m['files'].items():assert sha(stage/name)==pin
 assert sha(titles/'release.py')==title_operator
 spec=importlib.util.spec_from_file_location('title_successor_verification',titles/'release.py')
 op=importlib.util.module_from_spec(spec);sys.modules[spec.name]=op;spec.loader.exec_module(op);op=op.initialize()
 dep=read(active/'deployed.json');original=read(titles/'evidence/activation/deployed.json')
 assert dep['gateway_open'] and dep['source']==m['source']==pins['source'] and m['image']==original['image'] and m['base_hashes']['bin/zone']==pins['title_baseline']
 assert m['channel']==original['client_channel_sha256'] and sha(root/'data/public/channel.json')==m['channel']
 bins={k[4:]:v for k,v in m['base_hashes'].items() if k.startswith('bin/')};bins.update(m['binaries'])
 runtime=op.r.running(dep['image'],bins)
 assert runtime['restart_count']==0 and not any(runtime['errors'].values()) and sum(x[0]=='zone' for x in runtime['processes'])==12
 assert op.r.compact('gateway')['running'] and runtime['started_at']==read(active/'verified-closed.json')['started_at']
 op.p.unchanged(read(titles/'evidence/preflight.json'),after_open=True)
 op.title_state();op.p.contract();op.p.base.health();op.r.closed_ports()
 backup=read(active/'backup.json');assert backup['gzip_integrity'] and sha(Path(backup['path']))==backup['sha256']
 title_backup=read(titles/'evidence/activation/backup.json');assert title_backup['gzip_integrity'] and sha(Path(title_backup['path']))==title_backup['sha256']
 print(json.dumps(dict(result='PASS',source=original['source'],runtime_source=dep['source'],image=dep['image'],
  binaries=bins,workers=12,errors=runtime['errors'],restarts=runtime['restart_count'],started_at=runtime['started_at'],
  gateway_open=True,backup_integrity=True,backup_sha256=backup['sha256'],caches=op.p.h.caches(),
  client_release=original['client_release'],client_channel_sha256=m['channel'],
  deployed_receipt=sha(active/'deployed.json'),title_deployed_receipt=sha(titles/'evidence/activation/deployed.json'),
  runtime_stage=pins['stage'],title_catalog_enabled=True,owner_gameplay_accepted=False)))
'''
value=json.loads(remote(script,timeout=1200))
(HERE/'production-verified.json').write_text(json.dumps(value,indent=2)+'\n')
print(json.dumps(value,indent=2))
