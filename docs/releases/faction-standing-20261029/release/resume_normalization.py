"""Continue only the proved pre-shutdown three-field Hate B normalization."""
from pathlib import Path
import argparse,copy,hashlib,importlib.util,json,os
ROOT=Path('/opt/nightcap/deploy/production')
STAGE=Path('/opt/nightcap/releases/faction-standing-20261030-v1')

def reconcile(before,current,proof):
    assert proof['public']['exact_preflight_checksum_reproduced'] is True
    assert proof['public']['fields']==['map_file_name','content_flags','content_flags_disabled']
    assert proof['before']==before['content']['zone']!=proof['after']
    expected={**before['content'],'zone':proof['after']}
    assert current==expected,'Additional content drift requires separate audit'
    result=copy.deepcopy(before);result['content']=expected
    return result

def load_operator():
    spec=importlib.util.spec_from_file_location('faction_original',STAGE/'rollout.py')
    op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op);op.initialize()
    return op

def original_preflight_read(op):
    original=op.read
    def read(path):
        if path==STAGE/'evidence/preflight.json':return original(STAGE/'evidence/preflight-resumed.json')
        return original(path)
    return read

def verify_clone(op,before,proof):
    rows=op.sql('''CREATE TEMPORARY TABLE faction_zone_resume LIKE zone;
INSERT INTO faction_zone_resume SELECT * FROM zone;
SELECT COUNT(*) FROM faction_zone_resume WHERE id=163 AND zoneidnumber=186 AND version=0 AND map_file_name='' AND content_flags='' AND content_flags_disabled='';
CHECKSUM TABLE faction_zone_resume EXTENDED;
UPDATE faction_zone_resume SET map_file_name=NULL,content_flags=NULL,content_flags_disabled=NULL WHERE id=163;
CHECKSUM TABLE faction_zone_resume EXTENDED;
DROP TEMPORARY TABLE faction_zone_resume;''').splitlines()
    assert len(rows)==3 and rows[0]=='1'
    assert rows[1].split('\t')[-1]==proof['after']
    assert rows[2].split('\t')[-1]==before['content']['zone']==proof['before']

def dispatch(op,action):
    return {'activate':op.transition,'open':op.open_access,'rollback':lambda:op.transition(True),'open-rollback':lambda:op.open_access(True)}[action]()

def main():
    import fcntl
    assert __debug__;os.umask(0o077)
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('activate','open','rollback','open-rollback'));args=parser.parse_args()
    with (ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
        op=load_operator();assert not (ROOT/'private/gm-maintenance.json').exists()
        assert op.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1'
        before=op.read(STAGE/'evidence/preflight.json')
        assert before['manifest_sha256']==op.sha(STAGE/'manifest.json')
        proof=op.read(STAGE/'zone-normalization-proof.json')
        reconciled=reconcile(before,op.content(),proof)
        verify_clone(op,before,proof)
        if args.action=='activate':
            assert not (STAGE/'evidence/activation').exists(),'Original activation must have stopped before mutation'
            assert not (STAGE/'evidence/preflight-resumed.json').exists(),'Never replay continuation'
            log=(STAGE/'action-activate.log').read_text()
            assert 'Content/rule drift' in log and 'unchanged(p);startup.startup_guards()' in log
            assert all(op.r.compact(name)==value for name,value in before['services'].items())
            op.save(STAGE/'evidence/normalization-continuation.json',{'failed_action_sha256':op.sha(STAGE/'action-activate.log'),'proof_sha256':op.sha(STAGE/'zone-normalization-proof.json'),'original_preflight_sha256':op.sha(STAGE/'evidence/preflight.json'),'scope':'Preserve exact three-field native null-to-empty normalization; no live content write'})
            op.save(STAGE/'evidence/preflight-resumed.json',reconciled)
        else:
            receipt=op.read(STAGE/'evidence/normalization-continuation.json')
            assert receipt['failed_action_sha256']==op.sha(STAGE/'action-activate.log')
            assert receipt['proof_sha256']==op.sha(STAGE/'zone-normalization-proof.json')
            assert receipt['original_preflight_sha256']==op.sha(STAGE/'evidence/preflight.json')
            assert op.read(STAGE/'evidence/preflight-resumed.json')==reconciled
        op.read=original_preflight_read(op)
        dispatch(op,args.action)

if __name__=='__main__':main()
