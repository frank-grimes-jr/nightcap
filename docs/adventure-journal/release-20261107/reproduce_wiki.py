"""Reproduce the scoped public wiki, without publishing unrelated main previews."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent

def sha(data):return hashlib.sha256(data).hexdigest()

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--target',type=Path,required=True)
    target=parser.parse_args().target.resolve();assert target.is_relative_to(ROOT/'artifacts')
    assert not target.exists(),'Use a new isolated reproduction folder'
    proof=json.loads((HERE/'public-source-reproduction.json').read_text(encoding='utf-8'))
    patch=HERE/'published-source-overrides.patch';assert sha(patch.read_bytes())==proof['patch_sha256']
    target.mkdir(parents=True)
    for entry in proof['source_inputs']:
        path=target/entry['path'];assert path.resolve().is_relative_to(target)
        if not entry['base_exists']:continue
        data=subprocess.check_output(['git','show',proof['base_revision']+':'+entry['path']],cwd=ROOT)
        if path.suffix!='.png':data=data.replace(b'\r\n',b'\n')
        assert sha(data)==entry['base_sha256'],entry['path']
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    subprocess.run(['git','init','--quiet',str(target)],check=True)
    subprocess.run(['git','-c','core.autocrlf=false','apply','--unidiff-zero','--whitespace=nowarn',str(patch)],cwd=target,check=True)
    for entry in proof['source_inputs']:
        path=target/entry['path'];data=path.read_bytes()
        if path.suffix!='.png':data=data.replace(b'\r\n',b'\n');path.write_bytes(data)
        assert sha(data)==entry['sha256'],entry['path']
    subprocess.run([sys.executable,'build.py'],cwd=target/'wiki',check=True)
    expected=json.loads((ROOT/'artifacts/last-lantern-20261107/20261107-last-lantern-v2.tar.json').read_text())
    dist=target/'wiki/dist'
    actual={p.relative_to(dist).as_posix():sha(p.read_bytes()) for p in dist.rglob('*') if p.is_file()}
    assert actual==expected,'Public output drift'
    proof.update(status='PASS',public_files=len(actual),source_bytes_verified=True)
    (HERE/'public-source-reproduction.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'PASS','source_inputs':len(proof['source_inputs']),'public_files':len(actual)}))

if __name__=='__main__':main()
