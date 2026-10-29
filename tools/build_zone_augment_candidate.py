"""Compile/link the augment delta against an authenticated retained Hate build.

Reads the baseline source/objects; writes only a new isolated /tmp candidate.
No development or production runtime installation or service restart.
"""
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
FILES = ('common/zone_hunt_policy.h', 'zone/zone_hunt.cpp')
CONTAINER = 'akk-stack-eqemu-server-1'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-manifest', required=True, type=Path)
    parser.add_argument('--baseline', default='/tmp/nightcap-hate-layout-20261029')
    args = parser.parse_args()
    raw = args.baseline_manifest.read_bytes()
    baseline = json.loads(raw)
    overlay = {p.relative_to(ROOT/'server-mods/code').as_posix():
               hashlib.sha256(p.read_bytes()).hexdigest()
               for p in (ROOT/'server-mods/code').rglob('*') if p.is_file()}
    assert set(overlay) == set(baseline['overlay_sources']), 'Overlay membership drift'
    # Git may check out CRLF while the retained source uses LF (or vice versa).
    # Authenticate raw baseline bytes first, then compare canonical line endings.
    probe = '''import pathlib,hashlib,json
root=pathlib.Path(BASE)/'source';normalized={}
for n,h in pins.items():
 data=(root/n).read_bytes();assert hashlib.sha256(data).hexdigest()==h,n
 normalized[n]=hashlib.sha256(data.replace(b'\\r\\n',b'\\n')).hexdigest()
print(json.dumps(normalized))
'''
    probe_input = f'BASE={args.baseline!r}\npins={baseline["overlay_sources"]!r}\n' + probe
    result = subprocess.run(['docker','exec','-i',CONTAINER,'python3','-'], input=probe_input,
                            text=True, encoding='utf-8', capture_output=True, check=True)
    normalized = json.loads(result.stdout)
    changed = {n: h for n, h in overlay.items() if
               hashlib.sha256((ROOT/'server-mods/code'/n).read_bytes().replace(b'\r\n', b'\n')).hexdigest() != normalized[n]}
    assert set(changed) == set(FILES), f'Unreviewed native delta: {list(changed)}'
    dest = '/tmp/nightcap-zone-augments-20261029-' + uuid.uuid4().hex[:12]
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode='w') as tar:
        for name in FILES:
            data = (ROOT/'server-mods/code'/name).read_bytes()
            entry = tarfile.TarInfo(name)
            entry.size = len(data)
            tar.addfile(entry, io.BytesIO(data))
    unpack = '''import sys,tarfile
from pathlib import Path
root=Path(%r);root.mkdir(exist_ok=False)
with tarfile.open(fileobj=sys.stdin.buffer,mode='r|') as archive:
 for entry in archive:
  assert entry.isfile() and entry.name in %r
  p=root/'input'/entry.name;p.parent.mkdir(parents=True,exist_ok=True)
  p.write_bytes(archive.extractfile(entry).read())
''' % (dest, FILES)
    subprocess.run(['docker','exec','-i',CONTAINER,'python3','-c',unpack], input=archive.getvalue(), check=True)
    remote = r'''
import hashlib,json,pathlib,shlex,subprocess
base=pathlib.Path(BASE);root=pathlib.Path(DEST)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,h in prior['all_sources'].items():
 assert sha(base/'source'/name)==h,'Baseline source drift: '+name
for name,h in changed.items():assert sha(root/'input'/name)==h
for name,row in prior['binaries'].items():assert sha(base/'build/bin'/name)==row['sha256']
commands=json.loads((base/'build/compile_commands.json').read_text())
unit=next(c for c in commands if c['file'].endswith('/zone/zone_hunt.cpp'))
cmd=shlex.split(unit['command']);cwd=pathlib.Path(unit['directory'])
# Compile full native headers with the new policy first in the include path.
# Remove PCH consumption; retain its ordinary includes as a text header.
for i in range(len(cmd)-4,-1,-1):
 if cmd[i:i+3]==['-Xclang','-include-pch','-Xclang']:del cmd[i:i+4]
cmd[1:1]=['-I'+str(root/'input')]
obj=root/'zone_hunt.cpp.o'
cmd[cmd.index('-o')+1]=str(obj)
cmd[cmd.index('-c')+1]=str(root/'input/zone/zone_hunt.cpp')
with (root/'compile.log').open('x') as log:
 result=subprocess.run(cmd,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
if result.returncode:print((root/'compile.log').read_text()[-9000:]);raise SystemExit(result.returncode)
link=shlex.split((cwd/'CMakeFiles/zone.dir/link.txt').read_text())
old='CMakeFiles/zone.dir/zone_hunt.cpp.o'
assert link.count(old)==1
inputs={str((cwd/t).resolve()):sha((cwd/t).resolve()) for t in link if t.endswith(('.o','.a'))}
baseline_link=list(link)
baseline_link[baseline_link.index('-o')+1]=str(root/'retained-zone')
with (root/'baseline-link.log').open('x') as log:
 result=subprocess.run(baseline_link,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
if result.returncode:print((root/'baseline-link.log').read_text()[-9000:]);raise SystemExit(result.returncode)
assert sha(root/'retained-zone')==prior['binaries']['zone']['sha256'],'Retained objects do not reproduce baseline zone'
link[link.index(old)]=str(obj)
link[link.index('-o')+1]=str(root/'zone')
with (root/'link.log').open('x') as log:
 result=subprocess.run(link,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
if result.returncode:print((root/'link.log').read_text()[-9000:]);raise SystemExit(result.returncode)
assert 'not found' not in subprocess.check_output(['ldd',str(root/'zone')],text=True)
for name,h in inputs.items():assert sha(pathlib.Path(name))==h,'Retained link input changed'
for name,h in prior['all_sources'].items():assert sha(base/'source'/name)==h
for name,row in prior['binaries'].items():assert sha(base/'build/bin'/name)==row['sha256']
report={'date':'2026-10-29','status':'native translation-unit compile and zone relink passed; not installed',
 'baseline_manifest_sha256':baseline_hash,'baseline_root':str(base),'candidate_root':str(root),
 'retained_source_count':len(prior['all_sources']),'retained_link_inputs':inputs,
 'changed_sources':changed,'source_overlay':overlay,'baseline_binaries':prior['binaries'],
 'zone_sha256':sha(root/'zone'),'object_sha256':sha(obj),
 'baseline_relink_sha256':sha(root/'retained-zone'),
 'commands':{'compile':cmd,'baseline_link':baseline_link,'link':link},'working_directory':str(cwd),
 'logs':{n:sha(root/n) for n in ('compile.log','baseline-link.log','link.log')},
 'scope':'Only zone_hunt.cpp recompiled with full headers, no PCH; unchanged objects/libraries authenticated and retained. Added inline helpers do not change existing ABI or behavior outside Award/Load.',
 'production_changed':False,'owner_accepted':False}
(root/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':report['status'],'zone_sha256':report['zone_sha256'],'candidate_root':str(root)}))
'''
    prefix = f'BASE={args.baseline!r}\nDEST={dest!r}\nprior={baseline!r}\nchanged={changed!r}\noverlay={overlay!r}\nbaseline_hash={hashlib.sha256(raw).hexdigest()!r}\n'
    # Feed large authenticated metadata through stdin instead of OS argv limits.
    subprocess.run(['docker','exec','-i',CONTAINER,'python3','-'], input=prefix+remote,
                   text=True, encoding='utf-8', check=True)
    data = subprocess.check_output(['docker','exec',CONTAINER,'cat',dest+'/manifest.json'])
    for name, digest in overlay.items():
        assert hashlib.sha256((ROOT/'server-mods/code'/name).read_bytes()).hexdigest() == digest
    out = ROOT/'docs/releases/zone-augments-20261029/native-build.json'
    out.write_bytes(data)


if __name__ == '__main__':
    main()
