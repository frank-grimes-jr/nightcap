"""Resume verification after a Docker cp failure; never repeats SQL or installs."""
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,'/opt/nightcap/releases/tunnel-courts-20260930')
import rollout as r
OPEN_ATTEMPTED=False

def main():
    global OPEN_ATTEMPTED
    m=r.manifest();r.verified_target()
    assert (r.EVIDENCE/'apply-started.json').exists()
    assert not (r.EVIDENCE/'verified-before-open.json').exists()
    assert not r.state('gateway')['State']['Running']
    r.verify_geometry_inputs(m);health=r.running(m);r.installed_files(m)
    r.exact(r.load('after-content.json'),allow_saved=True)
    expected={**r.load('preflight.json')['runtime'],**{e['target']:e['sha256'] for e in m['runtime']}}
    assert r.runtime_files()==expected,'Runtime drift'
    assert r.fingerprints()==r.load('preservation-before.json'),'Preservation drift'
    # Exec writes to the mounted tmpfs as the service user; docker cp refuses
    # read-only root filesystems even when the destination is a writable mount.
    code="from pathlib import Path;import sys;Path('/tmp/court-spires-test.t').write_bytes(sys.stdin.buffer.read())"
    subprocess.run(['docker','compose','exec','-T','game','python3','-c',code],cwd=r.ROOT,
                   input=(r.STAGE/'tools/tests/tunnel_spires_quests.t').read_bytes(),check=True)
    code="""from pathlib import Path
import shutil,subprocess,tempfile
with tempfile.TemporaryDirectory(prefix='court-quest-') as d:
 root=Path(d);(root/'plugins').mkdir();(root/'quests/ecommons').mkdir(parents=True)
 for name in ('tunnel_spires.pl','tunnel_spire_data.pl'):
  shutil.copyfile('/srv/nightcap/plugins/'+name,root/'plugins'/name)
 shutil.copyfile('/srv/nightcap/quests/ecommons/999527.pl',root/'quests/ecommons/999527.pl')
 subprocess.run(['perl','/tmp/court-spires-test.t',str(root)],check=True)
"""
    r.call('docker','compose','exec','-T','game','python3','-c',code)
    for e in m['runtime']:r.call('docker','compose','exec','-T','game','perl','-c','/srv/nightcap/'+e['target'])
    epoch=int(r.sql('SELECT epoch FROM nightcap_market_state;'))
    assert epoch==r.load('epoch-before.json')['epoch']+1
    assert sorted(r.sql('SELECT kind,COUNT(*),SUM(remaining) FROM nightcap_market_offers GROUP BY kind;').splitlines())==sorted(['find\t10\t10','sell\t20\t20','buy\t12\t12'])
    r.installed_files(m);r.exact(r.load('after-content.json'),allow_saved=True)
    assert r.runtime_files()==expected and r.fingerprints()==r.load('preservation-before.json')
    health=r.running(m)
    health.update(source_commit=m['source_commit'],preserved_tables=len(r.fingerprints()),runtime_files=3,exact_static_afterimages=True,epoch=epoch,installed_quest_assertions=26)
    r.save('verified-before-open.json',health)
    OPEN_ATTEMPTED=True
    r.compose('up','-d','--wait','--wait-timeout','60','gateway')
    assert r.state('gateway')['State']['Running']
    r.running(m)
    health['gateway_running']=True;r.save('activated.json',health)
    print(json.dumps(health),flush=True)

if __name__=='__main__':
    try:main()
    except BaseException:
        if OPEN_ATTEMPTED:
            try:r.compose('stop','gateway')
            except BaseException:
                r.call('docker','stop','--time','30',r.state('gateway')['Id'])
            assert not r.state('gateway')['State']['Running'],'Could not hold gateway closed'
        raise
