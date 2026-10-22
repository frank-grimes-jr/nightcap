"""Collect aggregate release evidence only; never export player records/backups."""
import argparse,json,subprocess
from upload import SSH,STAGE,HERE
def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['progress','preflight','live']);args=parser.parse_args()
    source='stage_name='+repr(STAGE)+'\naction='+repr(args.action)+'\n'+r'''
import json,sys,shutil
from pathlib import Path
stage=Path(stage_name);sys.path.insert(0,str(stage));import rollout as op
op.initialize()
result={'free_bytes':shutil.disk_usage(stage).free,'services':{s:op.r.compact(s) for s in ('game','gateway','db','web','tunnel')},
        'evidence_files':sorted(p.name for p in op.EVIDENCE.iterdir())}
if action=='progress':
    result['clone_tables']=op.sql("SELECT TABLE_SCHEMA,COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA LIKE 'nightcap_classic_stage_%' GROUP BY TABLE_SCHEMA;")
    result['rehearsal_logs']={p.name:p.stat().st_size for p in (stage/'rehearsal-runtime').glob('*.log')}
    result['container_memory']=op.r.out('docker','stats','--no-stream','--format','{{.Name}} {{.MemUsage}}')
else:
    p=op.load('preflight.json');result['preflight']={'manifest_sha256':p['manifest_sha256'],'new_image_id':p['new_image_id']}
    result['rehearsal']=op.load('rehearsal.json')
    if action=='live':
        m=op.manifest();op.health();op.contract();op.r.closed_ports()
        current=op.r.running(p['new_image_id'],m['binaries'])
        a=op.load('deployed.json');assert current['started_at']==a['runtime']['started_at']
        assert p['manifest_sha256']==op.sha(stage/'manifest.json')
        assert {n:op.sha(op.ROOT/'data/server/shared'/n) for n in a['caches']}==a['caches']
        assert op.sql('SELECT revision,enabled FROM nightcap_dungeon_state;').strip()=='2026101601\t1'
        assert op.r.state('gateway')['State']['Running'];op.unchanged(p,True)
        result.update(a);result['runtime']=current
        result['backup']=op.load('backup.json')
        expiry=op.load('native-expiry.json');result['native_expiry']={k:v for k,v in expiry.items() if k!='expired_hashes'}
print(json.dumps(result))
'''
    result=subprocess.run(SSH+['sudo -n python3 -'],input=source,text=True,capture_output=True,timeout=180)
    if result.returncode:raise RuntimeError(result.stderr[-2500:])
    report=json.loads(result.stdout)
    if args.action!='progress':(HERE/('live-verification.json' if args.action=='live' else 'preflight-verification.json')).write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
