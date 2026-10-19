"""Run and collect the prepared synthetic matrix after the paired build finishes."""
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[3]
REL=Path(__file__).resolve().parent
EVIDENCE=REL/'evidence'
CONTAINER='akk-stack-eqemu-server-1'
RUNTIME='/tmp/nightcap-balance-thj-parity-20261018'
BUILD='/tmp/nightcap-thj-parity-v1'


def run(*args,log=None):
    command=['docker','exec','--workdir',RUNTIME,CONTAINER,*args]
    if log:
        with (EVIDENCE/log).open('w') as stream:
            subprocess.run(command,stdout=stream,stderr=subprocess.STDOUT,check=True)
    else:
        subprocess.run(command,check=True)


def copy(source,target):
    subprocess.run(['docker','cp',CONTAINER+':'+source,str(EVIDENCE/target)],check=True)


def collect():
    subprocess.run(['python',str(REL/'prepare_analysis.py')],check=True)
    for name in ('verify_native_pairing.py','collect_native.py'):
        subprocess.run(['docker','cp',str(ROOT.parent/'thj-parity-native-input'/name),CONTAINER+':'+RUNTIME+'/'+name],check=True)
    run('python3','verify_native_pairing.py')
    run('python3','collect_native.py')
    copy('/tmp/thj-parity-native-results.tar.gz','native-results.tar.gz')
    copy(RUNTIME+'/native-pairing.json','native-pairing.json')
    copy(RUNTIME+'/native-build-manifest.json','diagnostic-build-manifest.json')
    subprocess.run(['python',str(REL/'analyze_native.py')],cwd=ROOT,check=True)
    print(json.dumps({'status':'passed','cases':47,'evidence':str(EVIDENCE)}))


def main():
    # Inspect only the non-secret identity before cache generation.
    preflight="""import json
from pathlib import Path
r=Path.cwd()
assert str(r)=='/tmp/nightcap-balance-thj-parity-20261018'
c=json.loads((r/'eqemu_config.json').read_text())['server']
assert c['database']['db']=='nightcap_thj_parity_20261018'
assert c['database']['username']=='nightcap_balance'
assert c['auto_database_updates']=='false'
assert not (r/'shared').is_symlink()
print('Verified synthetic runtime and cache directory')
"""
    run('python3','-c',preflight)
    copy(BUILD+'/manifest.json','native-build-manifest.json')
    print('Building synthetic item/spell caches',flush=True)
    run(BUILD+'/build/bin/shared_memory',log='cache-build.log')
    cache="""import hashlib,json
from pathlib import Path
r=Path.cwd(); files={}
for p in sorted((r/'shared').rglob('*')):
 if p.is_file():
  assert not p.is_symlink()
  files[p.relative_to(r).as_posix()]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
assert files
(r/'cache-manifest.json').write_text(json.dumps({'database':'nightcap_thj_parity_20261018','files':files,'scope':'synthetic caches only; regenerate for any activation target'},indent=2)+'\\n')
print('Recorded',len(files),'cache files')
"""
    run('python3','-c',cache)
    copy(RUNTIME+'/cache-manifest.json','cache-manifest.json')
    print('Linking native diagnostic with final production objects',flush=True)
    run('python3','build_native.py','--source',BUILD+'/source','--build-dir',BUILD+'/build',log='diagnostic-build.log')
    print('Running 47 native scenarios',flush=True)
    run('python3','run_matrix.py')
    collect()


if __name__=='__main__':
    main()
