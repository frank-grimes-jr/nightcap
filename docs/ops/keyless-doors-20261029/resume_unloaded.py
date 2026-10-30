"""Continue the verified pre-SQL operation after Paineel naturally unloaded."""
import datetime
import json


def resume(op):
    out=op['OUT'];result=json.loads((out/'result.json').read_text())
    assert result['status']=='admission_held_draining'
    assert result['main']==op['ORIGINAL_MAIN'] and result['backup_verified']
    assert result['admission_locks_before']==[]
    assert result['admission_hold']['before']==[] and result['admission_hold']['after']==[75]
    assert result['admission_hold']['reconciled_readback'] is True
    assert not any(k in result for k in ('started_at','changed_doors'))
    previous=json.loads((out/'hold-interruption.json').read_text())
    assert previous['status']=='admission_hold_requested' and previous['main']==result['main']
    assert not (out/'unloaded-interruption.json').exists()
    before=json.loads((out/'before.json').read_text())
    assert before['doors']==op['EXPECTED']['doors']
    for name,value in [('forward.sql',op['FORWARD']),('rollback.sql',op['ROLLBACK'])]:
        assert (out/name).read_text()==value
    ns={'__name__':'capture'};exec(op['CAPTURE_SOURCE'],ns);capture=ns['capture']
    assert capture()['doors']==before['doors']
    baseline=json.loads((out/'services-before.json').read_text())
    workers=json.loads((out/'runtime-before.json').read_text())

    def verify_empty():
        assert op['services']()==baseline
        now=op['runtime']('probe')
        assert op['identities'](now)==op['identities'](workers)
        assert now['locks']==[75] and now['targets']==[], 'Affected zone loaded; stop for review'
        return now

    verify_empty()
    op['save']('unloaded-interruption.json',result)
    result.update(status='commit_started',started_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  continuation_revision=op['MAIN_REVISION'],
                  natural_unload_verified=True)
    op['save']('result.json',result)
    op['run'](['docker','compose','exec','-T','db','mariadb',
       '--defaults-extra-file=/run/secrets/db_backup_config','--batch','--raw','peq'],op['FORWARD'])
    after=capture()
    assert after['doors']==op['expected_after'](before)['doors']
    op['save']('after.json',after)
    verify_empty()
    result.update(status='committed_empty_zones_verified',
                  changed_doors=sum(bool(r['keyitem'] or r['lockpick']) for r in before['doors']))
    op['save']('result.json',result)
    op['run'](['docker','compose','exec','-T','game','python3','/opt/nightcap/start.py','--health'])
    assert capture()['doors']==after['doors']
    verify_empty()
    result['status']='refreshed_admission_release_pending'
    op['save']('result.json',result)
    result['admission_release']=op['runtime']('release',expected_locks=[75])
    result.update(status='activated_verified',applied_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
       total_doors=len(after['doors']),remaining_locks=0,
       preserved_other_doors=len(after['doors'])-result['changed_doors'],reload_targets=[],reload_logs={},
       refresh_policy='No affected zones loaded; normal loads read updated door content',
       service_and_worker_lifetimes_unchanged=True,health_passed=True,services=baseline,no_restart=True)
    op['save']('result.json',result)
    return result


if __name__=='__main__':
    namespace=dict(globals(),__name__='operator');exec(ACTIVATE_SOURCE,namespace)
    fcntl=namespace['fcntl'];root=namespace['ROOT']
    with (root/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        for f in (lock,gm):fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (root/'private/gm-maintenance.json').exists()
        print(json.dumps(resume(namespace),indent=2))
