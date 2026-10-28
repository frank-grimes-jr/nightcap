"""Create a new, local-only paired release bundle; never signs, uploads or activates."""
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
BUILD = ROOT/'docs/items/paladin-weapon-grip/balance/progression/native-build-manifest.json'
NATIVE = '/tmp/nightcap-paladin-progression-20261028'
CONTAINER = 'akk-stack-eqemu-server-1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(out, client, capture):
    build = json.loads(BUILD.read_text())
    for name, digest in build['source_sha256'].items():
        source = ROOT/'server-mods/code'/name
        assert sha(source) == digest, name
    preflight = load_module('paladin_preflight', ROOT/'tools/paladin_grip_preflight.py')
    reference = json.loads(capture.read_text(encoding='utf-8'))
    reference_check = preflight.validate_fresh(reference)
    candidate = json.loads((client/'candidate.json').read_text())
    assert candidate['published'] is False and candidate['complete_inventory_count'] == 141
    assert set(candidate['assets']) == {'dinput8.dll', 'nightcap-patch-sites.json', 'nightcap-patches.cfg'}
    for name, pin in candidate['assets'].items():
        assert sha(client/'assets'/name) == pin['sha256']
        assert (client/'assets'/name).stat().st_size == pin['size']
    assert sha(client/'baseline-channel.json') == candidate['baseline_channel_sha256']
    out.mkdir(parents=True, exist_ok=False)
    (out/'bin').mkdir()
    # Strip only new copies. The retained debug binaries and objects stay intact.
    # Exact runtime mapping/section/header proof is required for every copy.
    code = r'''
import hashlib,importlib.util,json,subprocess
from pathlib import Path
root=Path(NATIVE); target=root/'release-bin-20261028'
assert not target.exists(), 'Existing release copy: inspect before retry'
for name,digest in PINS.items():
 assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
spec=importlib.util.spec_from_file_location('identity',HELPER)
identity=importlib.util.module_from_spec(spec);spec.loader.exec_module(identity)
target.mkdir();result={}
for name in PINS:
 subprocess.run(['strip','--strip-debug','-o',str(target/name),str(root/name)],check=True)
 result[name]=identity.verify(root/name,target/name)
print(json.dumps(result))
'''.replace('NATIVE', repr(NATIVE)).replace('PINS', repr(build['binaries'])).replace('HELPER', repr(NATIVE+'/elf_runtime_identity-release.py'))
    subprocess.run(['docker', 'cp', str(ROOT/'tools/elf_runtime_identity.py'), CONTAINER+':'+NATIVE+'/elf_runtime_identity-release.py'], check=True)
    proof = json.loads(subprocess.check_output(['docker','exec','-i',CONTAINER,'python3','-'], input=code.encode()))
    for name, result in proof.items():
        assert result['status'] == 'PASS' and result['original_sha256'] == build['binaries'][name]
        subprocess.run(['docker','cp',CONTAINER+':'+NATIVE+'/release-bin-20261028/'+name,str(out/'bin'/name)],check=True)
        assert sha(out/'bin'/name) == result['sha256']
    for name in preflight.QUESTS:
        target = out/'quests'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/'server-mods/quests'/name, target)
        before = out/'quest-preimages'/name
        before.parent.mkdir(parents=True, exist_ok=True)
        before.write_bytes(reference['scripts'][name]['source'].encode())
        assert sha(before) == reference['scripts'][name]['sha256']
    shutil.copytree(client, out/'client')
    (out/'evidence').mkdir()
    shutil.copyfile(BUILD, out/'evidence/native-build-manifest.json')
    shutil.copyfile(capture, out/'evidence/production-reference.json')
    (out/'evidence/runtime-identity.json').write_text(json.dumps(proof, indent=2)+'\n')
    files = {p.relative_to(out).as_posix():{'sha256':sha(p),'size':p.stat().st_size}
             for p in sorted(out.rglob('*')) if p.is_file()}
    report = {'status':'local unsigned release bundle; no production changes',
              'production_activated':False, 'signed_client_published':False,
              'source_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'source_contains_uncommitted_candidate':True,
              'source_sha256':build['source_sha256'], 'public_reference_check':reference_check,
              'native_binaries':proof, 'quests':list(preflight.QUESTS),
              'client_assets':candidate['assets'], 'baseline_client_release':candidate['baseline_release'],
              'monk_aa_changes':False, 'sql_migration':False,
              'owner_gameplay_accepted':False, 'files':files}
    (out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
    archive = out.with_suffix('.tar.gz')
    with tarfile.open(archive, 'x:gz') as tar:
        for path in sorted(out.rglob('*')):
            if not path.is_file():
                continue
            name = path.relative_to(out).as_posix()
            data = path.read_bytes()
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o755 if name.startswith('bin/') else 0o600
            tar.addfile(info, io.BytesIO(data))
    with tarfile.open(archive, 'r:gz') as tar:
        expected = {**files, 'manifest.json':{'sha256':sha(out/'manifest.json')}}
        assert set(tar.getnames()) == set(expected)
        for member in tar.getmembers():
            assert member.isfile()
            assert hashlib.sha256(tar.extractfile(member).read()).hexdigest() == expected[member.name]['sha256']
    receipt = {'archive_sha256':sha(archive), 'archive_size':archive.stat().st_size,
               'manifest_sha256':sha(out/'manifest.json'), 'members':len(files)+1,
               'runtime_identity':proof, 'client_assets':candidate['assets'],
               'public_reference_check':reference_check, 'production_changes':False}
    (HERE/'bundle.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--client', type=Path, required=True)
    parser.add_argument('--capture', type=Path, required=True)
    args = parser.parse_args()
    main(args.output.resolve(), args.client.resolve(), args.capture.resolve())
