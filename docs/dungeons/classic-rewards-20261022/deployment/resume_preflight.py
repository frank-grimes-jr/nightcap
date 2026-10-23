"""Resume only the proven pre-mutation resource stop; never rebuild or replay SQL."""
import fcntl,hashlib,importlib.util,json,os,shutil
from pathlib import Path
STAGE=Path('/opt/nightcap/releases/classic-dungeons-rewards-20261022')
spec=importlib.util.spec_from_file_location('rollout',STAGE/'rollout.py')
op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op)
def main():
    assert __debug__;os.umask(0o077);op.initialize()
    with (op.ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (op.ROOT/'private/gm-maintenance.json').exists()
        assert op.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1'
        assert {p.name for p in op.EVIDENCE.iterdir()}=={'preflight-started.json','candidate-image.json'}
        assert not (STAGE/'rehearsal-runtime').exists(),'Rehearsal already began; inspect before resuming'
        p=op.load('preflight-started.json');m=op.manifest()
        assert p['manifest_sha256']==op.sha(STAGE/'manifest.json')
        assert all(op.r.compact(s)==v for s,v in p['services'].items())
        op.unchanged(p);op.startup_guards();op.script_guards(m);op.health()
        p['new_image_id']=op.load('candidate-image.json')['image']
        assert op.r.image_hashes(p['new_image_id'])=={**m['base_hashes'],**{'bin/'+n:h for n,h in m['binaries'].items()}}
        op.rehearsal(p);op.unchanged(p)
        assert all(op.r.compact(s)==v for s,v in p['services'].items())
        assert shutil.disk_usage(op.ROOT).free>=800*1024**2
        op.save('preflight.json',p)
        op.save('resume-preflight.json',{'helper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'reused_verified_image':True})
        print('Fresh live-content rehearsal passed; live services remain unchanged.',flush=True)
if __name__=='__main__':main()
