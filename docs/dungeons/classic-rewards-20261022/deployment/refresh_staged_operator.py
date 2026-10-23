"""Refresh only operator/manifest before first preflight; binary payload immutable."""
import ast,hashlib,json,subprocess
from upload import SSH,STAGE,ARTIFACTS,HERE
def main():
    folder=ARTIFACTS/'deployment-package-v2'
    manifest=json.loads((HERE/'package-manifest.json').read_text())
    old_manifest=json.loads(json.dumps(manifest))
    root=HERE.parents[3];base=(root/'docs/releases/aa-pacing-million-20261021/rollout.py').read_text()
    funcs='\n\n'.join(ast.get_source_segment(base,n) for n in ast.parse(base).body if isinstance(n,ast.FunctionDef) and n.name in ('market','verify_market'))
    text=(HERE/'rollout.py').read_text().replace('# market()/verify_market() are copied exactly from the reviewed October21\n# operator by prepare_local.py and pin the native once-per-startup rotation.',funcs)
    assert 'def market():' in text
    digest=hashlib.sha256(text.encode()).hexdigest();old_operator=manifest['files']['rollout.py']
    manifest['files']['rollout.py']=digest
    source='stage_name='+repr(STAGE)+'\nold_manifest='+repr(old_manifest)+'\nold_operator='+repr(old_operator)+'\noperator='+repr(text)+'\nmanifest='+repr(manifest)+'\n'+r'''
import hashlib,json,os
from pathlib import Path
stage=Path(stage_name)
assert not (stage/'evidence').exists(),'Cannot alter a preflighted release'
assert json.loads((stage/'manifest.json').read_text())==old_manifest
assert hashlib.sha256((stage/'rollout.py').read_bytes()).hexdigest()==old_operator
for name,digest in manifest['files'].items():
    if name!='rollout.py':assert hashlib.sha256((stage/name).read_bytes()).hexdigest()==digest
for name,value in [('rollout.py',operator),('manifest.json',json.dumps(manifest,indent=2)+'\n')]:
    tmp=stage/(name+'.reviewed');tmp.write_text(value);tmp.chmod(0o600);os.replace(tmp,stage/name)
print(json.dumps({'operator_sha256':manifest['files']['rollout.py'],'stage':str(stage)}))
'''
    result=subprocess.run(SSH+['sudo -n python3 -'],input=source,text=True,capture_output=True,timeout=60)
    if result.returncode:raise RuntimeError(result.stderr[-1800:])
    (folder/'rollout.py').write_text(text,encoding='utf-8')
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (HERE/'package-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(result.stdout)
if __name__=='__main__':main()
