"""Resume failed preflight using its authenticated immutable candidate; no rebuild."""
import fcntl,hashlib,importlib.util,json,os
from pathlib import Path
STAGE=Path('/opt/nightcap/releases/aa-pacing-million-20261021')
IMAGE='sha256:15a159c0f9a80d541856d7412e59d94baa6b29cc320c397cab9e3d44278ecfff'
PINS={'rollout.py': '9b309dec411b4809e969c920d88f060c2334bfca2ecf5c30fc6292dbbf7039e1', 'stage-manifest.json': '2f5d69124568702334624f1c35d16794dc1432862be61c05cd2eaa115ddf3b38'}

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def main():
    assert __debug__;os.umask(0o077)
    assert sha(STAGE/'rollout.py')==PINS['rollout.py']
    assert sha(STAGE/'manifest.json')==PINS['stage-manifest.json']
    spec=importlib.util.spec_from_file_location('release',STAGE/'rollout.py')
    op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op)
    op.initialize();r=op.r;m=op.manifest()
    with (op.ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (op.ROOT/'private/gm-maintenance.json').exists()
        assert op.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1'
        assert not op.EVIDENCE.exists(), 'Inspect prior evidence before retry'
        assert IMAGE!=m['base_image_id'] and r.state('game')['Image']==m['base_image_id']
        expected={**m['base_hashes'],'bin/zone':m['zone_sha256']}
        assert r.image_hashes(IMAGE)==expected
        def layers(image):return json.loads(r.out('docker','image','inspect',image))[0]['RootFS']['Layers']
        assert layers(IMAGE)[:-1]==layers(m['base_image_id'])
        previous=STAGE/'previous'
        assert not (STAGE/'previous-second-preflight').exists()
        for name,digest in m['quest_preimages'].items():
            assert sha(previous/name)==digest
        previous.rename(STAGE/'previous-second-preflight')
        def reuse(manifest):
            assert manifest==m
            assert r.out('docker','image','inspect','--format','{{.Id}}',IMAGE).strip()==IMAGE
            assert r.image_hashes(IMAGE)==expected
            return IMAGE
        op.build_image=reuse
        op.preflight()
        op.save(op.EVIDENCE/'reused-image.json',{'image':IMAGE,'wrapper_sha256':sha(Path(__file__)),'operator_sha256':PINS['rollout.py'],'disk_gates_unchanged':True})
if __name__=='__main__':main()
