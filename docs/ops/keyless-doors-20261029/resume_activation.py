"""One-time continuation of the recorded pre-SQL hold acknowledgment timeout.

Runner injects ACTIVATE_SOURCE and the original pinned inputs. This never retries
the hold mutation or an attempted SQL commit. It reuses the reviewed finish path.
"""
import json


def resume(op):
    out=op['OUT']
    result=json.loads((out/'result.json').read_text())
    assert result['status']=='admission_hold_requested'
    assert result['main']==op['ORIGINAL_MAIN'] and result['backup_verified']
    assert result['admission_locks_before']==[]
    assert not any(k in result for k in ('started_at','changed_doors','admission_hold'))
    before=json.loads((out/'before.json').read_text())
    assert before['doors']==op['EXPECTED']['doors']
    for name,value in [('forward.sql',op['FORWARD']),('rollback.sql',op['ROLLBACK'])]:
        assert (out/name).read_text()==value
    namespace={'__name__':'capture'}
    exec(op['CAPTURE_SOURCE'],namespace)
    capture=namespace['capture']
    assert capture()['doors']==before['doors'], 'No continuation over changed doors'
    baseline=json.loads((out/'services-before.json').read_text())
    assert op['services']()==baseline
    workers=json.loads((out/'runtime-before.json').read_text())
    now=op['runtime']('probe')
    assert op['identities'](now)==op['identities'](workers)
    assert op['target_ids'](now)==op['target_ids'](workers)
    assert now['locks']==[75] and workers['locks']==[]
    assert not (out/'hold-interruption.json').exists(), 'Continuation already attempted'
    op['save']('hold-interruption.json',result)
    (out/'runtime-corrected.py').write_text(op['RUNTIME_SOURCE'])
    result['continuation_revision']=op['MAIN_REVISION']
    result['admission_hold']={'held':True,'zone_id':75,'before':[],'after':[75],
                              'other_locks_preserved':True,'reconciled_readback':True}
    result['status']='admission_held_draining'
    op['save']('result.json',result)
    return op['finish'](capture,before,baseline,workers,result)


if __name__=='__main__':
    namespace=dict(globals(),__name__='operator')
    exec(ACTIVATE_SOURCE,namespace)
    fcntl=namespace['fcntl'];root=namespace['ROOT']
    with (root/'.deployment.lock').open('a') as lock, open('/var/lock/nightcap-gm.lock','a') as gm:
        for f in (lock,gm):fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (root/'private/gm-maintenance.json').exists()
        print(json.dumps(resume(namespace),indent=2))
