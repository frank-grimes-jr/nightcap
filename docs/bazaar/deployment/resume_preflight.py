"""One-shot continuation after the recorded image-build disk-reserve failure.

Uses the already built image; does not rebuild, prune, stop or activate services.
"""
import fcntl,json,os,shutil
from pathlib import Path
import rollout as op


def resume():
    m=op.manifest();p=op.read(op.EVIDENCE/'preflight-started.json')
    assert not (op.EVIDENCE/'preflight.json').exists()
    assert not (op.EVIDENCE/'activation').exists()
    assert not (op.EVIDENCE/'preflight-resume-started.json').exists()
    assert p['manifest_sha256']==op.sha(op.STAGE/'manifest.json')
    failure=(op.STAGE/'preflight.log').read_text()
    assert 'assert shutil.disk_usage(ROOT).free>=RESERVE' in failure and failure.rstrip().endswith('AssertionError')
    reclaimed=op.read(op.EVIDENCE/'scoped-cache-reclaim-reconciled.json')
    assert reclaimed['cache_id']=='pyf6j6rkzq4pvi7al04hdmr6d' and reclaimed['cache_absent']
    assert reclaimed['services_unchanged'] and not reclaimed['activation_attempted']
    assert reclaimed['base_image']==m['base_image_id']
    assert all(op.r.compact(s)==v for s,v in p['services'].items())
    op.unchanged(p);op.base.health();op.startup.startup_guards();op.r.closed_ports()
    assert op.contract()==p['checks']
    assert op.sha(op.ROOT/'data/public/channel.json')==m['client_channel_sha256']
    op.r.running(m['base_image_id'],op.binaries(True),p['services']['game']['restarts'])
    assert shutil.disk_usage(op.ROOT).free>=op.RESERVE
    image=op.r.out('docker','image','inspect','--format','{{.Id}}','nightcap-game:commonlands-bazaar-20261026').strip()
    assert image==reclaimed['candidate_image']
    layers=lambda x:json.loads(op.r.out('docker','image','inspect',x))[0]['RootFS']['Layers']
    assert layers(image)[:-1]==layers(m['base_image_id'])
    assert op.r.image_hashes(m['base_image_id'])==m['base_hashes']
    assert op.r.image_hashes(image)=={**m['base_hashes'],'bin/zone':m['zone_sha256']}
    for candidate in (image,m['base_image_id']):
        assert 'not found' not in op.r.out('docker','run','--rm','--network','none','--entrypoint','ldd',candidate,'/opt/nightcap/bin/zone')
        op.r.call('docker','run','--rm','--network','none','--entrypoint','python3',candidate,'-c','import sys;sys.path.insert(0,"/opt/nightcap");import start;start.validate_native()')
        op.r.call('docker','run','--rm','--network','none','--entrypoint','/opt/nightcap/bin/loginserver',candidate,'--nightcap-crypto-self-test')
    op.save(op.EVIDENCE/'preflight-resume-started.json',{'image':image,'manifest_sha256':p['manifest_sha256'],'resume_script_sha256':op.sha(Path(__file__))})
    p['new_storage']=op.rehearse_storage();p['image']=image
    op.unchanged(p);op.base.health();op.startup.startup_guards();op.r.closed_ports()
    assert op.contract()==p['checks']
    assert all(op.r.compact(s)==v for s,v in p['services'].items())
    assert shutil.disk_usage(op.ROOT).free>=op.RESERVE
    op.save(op.EVIDENCE/'preflight-resume-verified.json',{'image':image,'checks':p['checks'],'free_bytes':shutil.disk_usage(op.ROOT).free,'services_unchanged':True,'activated':False})
    op.save(op.EVIDENCE/'preflight.json',p)
    print('Preflight continuation passed; services unchanged.',flush=True)


if __name__=='__main__':
    assert __debug__;os.umask(0o077);op.initialize()
    with (op.ROOT/'.deployment.lock').open('a') as lock,open('/var/lock/nightcap-gm.lock','a') as gm:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);fcntl.flock(gm,fcntl.LOCK_EX|fcntl.LOCK_NB)
        assert not (op.ROOT/'private/gm-maintenance.json').exists()
        assert op.sql("SELECT IS_FREE_LOCK('nightcap_gm_writes');").strip()=='1'
        resume()
