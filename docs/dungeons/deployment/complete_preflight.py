"""One-shot recovery for the recorded October 16 old-world health failure.

Does not relabel the failed ordinary preflight or restore data. Revalidates its
successful content/cache rehearsal against a fresh, explicitly unhealthy old
runtime baseline. Access closes before checks and stays closed until activation.
"""
import fcntl
import json
import os
from pathlib import Path
import re
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
import rollout as d

OLD_GAME='0aff90dc67d11aff1297e17473decd129b0b4b8e82b7ef42e0b4ce538c681c42'
OLD_START='2026-10-16T17:04:51.766916239Z'

def fingerprint_table(table,database):
    assert re.fullmatch('[a-z_][a-z0-9_]*',table)
    columns=d.sql("SELECT column_name FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name='"+table+"' ORDER BY ordinal_position;",database).splitlines()
    assert columns and all(re.fullmatch('[a-zA-Z_][a-zA-Z0-9_]*',c) for c in columns)
    return sorted(d.sql('SELECT SHA2(JSON_ARRAY('+','.join('`'+c+'`' for c in columns)+'),256) FROM `'+table+'`;',database).splitlines())

def schema(table,database):
    result={}
    for source,fields in (
      ('columns','ordinal_position,column_name,column_type,is_nullable,column_default,extra,collation_name'),
      ('statistics','index_name,non_unique,seq_in_index,column_name,sub_part,index_type'),
      ('triggers','trigger_name,event_manipulation,action_order,action_condition,action_statement,action_orientation,action_timing')):
        condition=("trigger_schema=DATABASE() AND event_object_table=" if source=='triggers' else 'table_schema=DATABASE() AND table_name=')+"'"+table+"'"
        result[source]=sorted(d.sql('SELECT SHA2(JSON_ARRAY('+fields+'),256) FROM information_schema.'+source+' WHERE '+condition+';',database).splitlines())
    result['engine']=d.sql("SELECT engine FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name='"+table+"';",database)
    return result

def main():
    m=d.manifest();prior=json.loads((d.STAGE/'rehearsed-inputs.json').read_text())
    for key in ('source_commit','base_binaries','binaries','client_release','client_channel_sha256'):
        assert m[key]==prior[key],key
    for name,digest in prior['files'].items():
        if name not in ('rollout.py','test_rollout.py'):assert m['files'][name]==digest,name
    assert {p.name for p in d.r.EVIDENCE.iterdir()}=={'references.json','rehearsal.json'},'Recovery already attempted or activation evidence exists'
    rehearsal=d.load('rehearsal.json');database=rehearsal['database']
    assert re.fullmatch('nightcap_dungeon_stage_[0-9a-f]{12}',database)
    assert rehearsal['status']=='passed' and rehearsal['native_contract_activation'] and rehearsal['public_content_preserved']
    old=d.r.compact('game')
    assert old['id']==OLD_GAME and old['started_at']==OLD_START and old['restarts']==m['baseline_restarts']==1
    assert old['running'] and old['health']=='unhealthy' and not old['oom_killed']
    d.save('recovery-started.json',{'reason':'Old world health port 9001 timed out; same process/image; no live feature SQL',
        'ordinary_preflight':'failed runtime continuity gate','game':old,'native_shutdown_flush_not_established':True})
    try:
        d.r.compose('stop','gateway')
        assert not d.r.state('gateway')['State']['Running']
        assert d.sql("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name LIKE 'nightcap_dungeon_%';").strip()=='0'
        d.audit_references()
        config=d.runtime_config()['server'];connection=config['database'];content=config.get('content_database') or connection
        assert connection['db']==content['db']=='peq'
        assert all(connection.get(k)==content.get(k) for k in ('host','port'))
        services={s:d.r.compact(s) for s in ('game','gateway','db','web','tunnel')}
        assert services['game']==old and services['db']['health']=='healthy'
        hashes=d.r.image_hashes(old['image_id'])
        assert {n:hashes['bin/'+n] for n in d.NAMES}==m['base_binaries']
        code="from pathlib import Path;import hashlib,json;r=[]\nfor p in Path('/proc').iterdir():\n if p.name.isdigit():\n  try:\n   e=p/'exe';n=e.resolve().name\n   if n in {'world','zone','ucs','loginserver'}:r.append([n,hashlib.sha256(e.read_bytes()).hexdigest()])\n  except (FileNotFoundError,PermissionError):pass\nprint(json.dumps(r))"
        processes=json.loads(d.r.out('docker','exec',old['id'],'python3','-c',code))
        assert sum(n=='zone' for n,h in processes)==12
        assert all(sum(n==k for n,h in processes)==1 for k in ('world','ucs','loginserver'))
        assert all(m['base_binaries'][n]==h for n,h in processes)
        d.q.verify_publication(m);d.r.closed_ports()
        live_content=d.content();assert live_content==d.content(database)
        for table in sorted(set(live_content)|{'rule_values','rule_sets','variables'}):
            assert schema(table,'peq')==schema(table,database),'Schema drift: '+table
        for table in ('rule_values','rule_sets','variables'):
            assert fingerprint_table(table,'peq')==fingerprint_table(table,database),'Configuration drift: '+table
        runtime=d.STAGE/'rehearsal-runtime'
        assert d.records(d.ROOT/'data/server/shared/items')==d.records(runtime/'before-items')
        assert d.sha(runtime/'shared/items')==rehearsal['item_cache_sha256']
        checked=d.compare_cache(d.records(runtime/'before-items'),d.records(runtime/'shared/items'))
        assert checked['all_records_sha256']==rehearsal['all_records_sha256']
        image=d.r.out('docker','image','inspect','--format','{{.Id}}','nightcap-game:dungeons-20261016').strip()
        p={'manifest_sha256':d.sha(d.STAGE/'manifest.json'),'old_image_id':old['image_id'],'old_hashes':hashes,
            'new_image_id':image,'services':services,'runtime':d.r.runtime(),'public':d.r.public(),'content':live_content,'policies':d.policies(),
            'recovery':{'old_runtime_health_verified':False,'reason':'Recorded unhealthy old world; direct controlled candidate cutover',
                'rehearsal_sha256':d.sha(d.r.EVIDENCE/'rehearsal.json'),'old_processes':processes}}
        assert d.r.image_hashes(image)==d.expected_image(p)
        layers=lambda value:json.loads(d.r.out('docker','image','inspect',value))[0]['RootFS']['Layers']
        before,after=layers(old['image_id']),layers(image)
        assert after[:len(before)]==before and len(after)==len(before)+1
        for name in d.REPLACE:assert 'not found' not in d.r.out('docker','run','--rm','--network','none','--entrypoint','ldd',image,'/opt/nightcap/bin/'+name)
        d.r.call('docker','run','--rm','--network','none','--entrypoint','python3',image,'-c',"import sys;sys.path.insert(0,'/opt/nightcap');import start;start.validate_native()")
        d.cache_contract(image,runtime/'shared/items')
        d.unchanged(p)
        assert d.r.compact('game')==services['game'] and d.r.compact('gateway')==services['gateway']
        d.save('preflight.json',p)
        print('Recovery checks passed with explicit unhealthy old baseline; gateway remains closed for controlled activation.',flush=True)
    except BaseException:
        d.hold('One-shot preflight recovery failed; no automatic replay or SQL restore')
        raise

if __name__=='__main__':
    assert __debug__;os.umask(0o077)
    with (d.ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
        d.q.require_no_gm_work();main()
