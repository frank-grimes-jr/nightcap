"""Verify the current title layer; retain exact original preservation evidence.

Later independently authorized content releases may restart the same image or
change caches. Do not mistake their changes for failed original title activation,
or overwrite them to reproduce an old preflight snapshot.
"""
import json
from control import HERE,remote


def main():
    summary=json.loads((HERE/'activation-summary.json').read_bytes())
    assert summary['result']=='PASS' and not summary['restored_player_snapshot']
    script='expected_receipt='+repr(summary['deployed_receipt_sha256'])+'\n'+'''
from pathlib import Path
import fcntl,importlib.util,json,sys,time
s=Path('/opt/nightcap/releases/titles-live-20261114-v1')
spec=importlib.util.spec_from_file_location('titles_fresh_probe',s/'release.py')
module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
with (module.ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
    deadline=time.monotonic()+1200
    for handle in (lock,gm):
        while True:
            try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);break
            except BlockingIOError:
                assert time.monotonic()<deadline,'Maintenance still owned; no verification performed'
                time.sleep(5)
    op=module.initialize()
    assert not (op.ROOT/'private/gm-maintenance.json').exists()
    assert op.prior.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes')").strip()=='1'
    dep=op.read(op.ACTIVE/'deployed.json');before=op.read(op.EVIDENCE/'preflight.json')
    assert op.sha(op.ACTIVE/'deployed.json')==expected_receipt and dep['gateway_open']
    assert op.r.compact('gateway')['running'] and op.r.compact('game')['health']=='healthy'
    assert op.sha(op.ROOT/'data/public/channel.json')==dep['client_channel_sha256']
    op.title_state()
    runtime,backup=op.verification(before)
    op.p.base.health();op.r.closed_ports()
    assert runtime['image_id']==dep['image']
    print(json.dumps(dict(result='PASS',source=dep['source'],image=dep['image'],binaries=op.p.binaries(),
        workers=12,errors=runtime['errors'],restarts=runtime['restart_count'],started_at=runtime['started_at'],
        gateway_open=True,backup_integrity=True,backup_sha256=backup['sha256'],caches=op.p.h.caches(),
        title_catalog_enabled=True,title_settings=op.title_schema.settings(op.prior.sql),
        title_command=[r for r in op.title_schema.commands(op.prior.sql) if r['command']=='titles'],
        client_release=dep['client_release'],client_channel_sha256=dep['client_channel_sha256'],
        deployed_receipt=expected_receipt,owner_gameplay_accepted=False,
        preservation_scope='Original exact state/content/cache preservation passed in immutable closed and post-open deployment receipts; this probe freshly verifies the current title layer, native pair and client',
        same_runtime_start_as_title_activation=runtime['started_at']==dep['runtime']['started_at'])))
'''
    data=json.loads(remote(script,timeout=1200))
    assert data['result']=='PASS' and data['workers']==12 and data['title_catalog_enabled']
    (HERE/'production-verified.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(data,indent=2))


if __name__=='__main__':main()
