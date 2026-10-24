"""Read verified host receipts and current health; never perform a rollout action."""
import json
from pathlib import Path
from dispatch import remote, STAGE

HERE = Path(__file__).resolve().parent


def main():
    assert not (HERE/'open-receipt.json').exists(), 'Preserve the original verification'
    source = r'''
import contextlib,datetime,hashlib,importlib.util,json,shutil,sys
from pathlib import Path
stage=Path(STAGE)
spec=importlib.util.spec_from_file_location('release',stage/'rollout.py')
op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op)
with contextlib.redirect_stdout(sys.stderr):
 op.initialize();m=op.manifest();b=op.base;r=op.r
 p=b.load('preflight.json');a=b.load('deployed.json')
 assert a['gateway_open'] and not a['database_restored']
 assert not list((stage/'evidence').glob('held-*.json'))
 current=r.running(p['new_image_id'],m['binaries'])
 assert current['started_at']==a['runtime']['started_at']
 assert r.state('gateway')['State']['Running']
 b.health();r.closed_ports();b.unchanged(p,True);op.check_new_storage()
 checks=op.contract();assert checks==a['checks']
 for table in ('nightcap_ashen_state','nightcap_highkeep_state'):
  assert b.sql('SELECT revision,enabled FROM '+table+';').strip()=='2026102401\t1'
 assert {n:op.sha(op.ROOT/'data/server/shared'/n) for n in a['caches']}==a['caches']
 assert op.sha(op.ROOT/'data/public/channel.json')==m['client_channel_sha256']
 evidence={f.name:json.loads(f.read_text()) for f in (stage/'evidence').glob('*.json')}
 summary={'result':'PASS','verified_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
  'source_revision':m['source_revision'],'runtime':current,'gateway_open':True,
  'checks':checks,'state_tables':a['state_tables'],'cache':a['cache'],
  'cache_comparison':evidence['generated-cache.json']['comparison'],
  'stopped_backup_verified':bool(evidence['backup.json']),
  'native_shutdown':evidence['native-shutdown.json'],
  'native_expired_noncorpse_rows':evidence['native-expiry.json']['expired_noncorpse_rows'],
  'campaign_flags_enabled':True,'client_channel_sha256':m['client_channel_sha256'],
  'client_release':2026102402,'database_restored':False,'owner_gameplay_accepted':False,
  'free_bytes':shutil.disk_usage(stage).free}
print(json.dumps({'summary':summary,'evidence':evidence}))
'''.replace('Path(STAGE)', 'Path('+repr(STAGE)+')')
    result = json.loads(remote(source))
    (HERE/'private/deployment-evidence.json').write_text(json.dumps(result['evidence'],indent=2)+'\n')
    (HERE/'open-receipt.json').write_text(json.dumps(result['summary'],indent=2)+'\n')
    print(json.dumps(result['summary']))


if __name__ == '__main__':
    main()
