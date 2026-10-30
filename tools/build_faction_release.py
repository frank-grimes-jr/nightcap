"""Compile/link only approved faction standings against the Hate build.

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
FILES = ('common/faction_standing.h', 'zone/faction_standing.inc', 'zone/command.cpp', 'zone/command.h')
NEW_FILES = {'common/faction_standing.h', 'zone/faction_standing.inc'}
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
    assert set(overlay) == set(baseline['overlay_sources']) | NEW_FILES, 'Overlay membership drift'
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
               n not in normalized or hashlib.sha256((ROOT/'server-mods/code'/n).read_bytes().replace(b'\r\n', b'\n')).hexdigest() != normalized[n]}
    assert set(changed) == set(FILES), f'Unreviewed native delta: {list(changed)}'
    dest = '/tmp/nightcap-faction-release-20261030-' + uuid.uuid4().hex[:12]
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
import hashlib,json,pathlib,re,shlex,shutil,subprocess
base=pathlib.Path(BASE);root=pathlib.Path(DEST)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,h in prior['all_sources'].items():
 assert sha(base/'source'/name)==h,'Baseline source drift: '+name
for name,h in changed.items():assert sha(root/'input'/name)==h
for name,row in prior['binaries'].items():assert sha(base/'build/bin'/name)==row['sha256']
# Copy complete headers so quoted includes and pragma-once use one coherent tree.
shutil.copytree(base/'source',root/'source',symlinks=True)
for name in changed:
 dest=root/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True)
 shutil.copyfile(root/'input'/name,dest)
# The shared command header adds only a declaration, without an ABI/layout change.
old_header=(base/'source/zone/command.h').read_text()
new_header=(root/'source/zone/command.h').read_text()
assert new_header.replace('void command_factions(Client *c, const Seperator *sep);\n','')==old_header
commands=json.loads((base/'build/compile_commands.json').read_text())
compiled={};compile_commands={}
for unit_name in ('command.cpp',):
 if unit_name=='command.cpp':
  matches=[c for c in commands if 'gm_commands_zone.dir/Unity/' in c['file'] and str(base/'source/zone/command.cpp') in pathlib.Path(c['file']).read_text()]
  assert len(matches)==1,'Ambiguous command unity unit'
  unit=matches[0];unity=pathlib.Path(unit['file'])
  unity_text=unity.read_text()
  members=re.findall(r'^#include "([^"]+)"',unity_text,re.M)
  assert members.count(str(base/'source/zone/command.cpp'))==1
  assert all(str(pathlib.Path(m).relative_to(base/'source')) in prior['all_sources'] for m in members)
  assert all(not line.strip() or line.startswith('/*') or line.startswith('#include ') for line in unity_text.splitlines())
  new_unit=root/unity.name;new_unit.write_text(unity_text.replace(str(base/'source'),str(root/'source')))
 else:
  unit=next(c for c in commands if c['file'].endswith('/zone/'+unit_name))
  new_unit=root/'source/zone'/unit_name
 cmd=shlex.split(unit['command']);cwd=pathlib.Path(unit['directory'])
 # Recompile with full native headers and no old PCH consumption.
 for i in range(len(cmd)-4,-1,-1):
  if cmd[i:i+3]==['-Xclang','-include-pch','-Xclang']:del cmd[i:i+4]
 for i in range(len(cmd)-3):
  if cmd[i:i+3]==['-Xclang','-include','-Xclang']:
   text=pathlib.Path(cmd[i+3]).read_text().replace(str(base/'source'),str(root/'source'))
   h=root/(unit_name+'-pch.hxx');h.write_text(text);cmd[i+3]=str(h)
 cmd=[t.replace(str(base/'source'),str(root/'source')) for t in cmd]
 obj=root/(new_unit.name+'.o');cmd[cmd.index('-o')+1]=str(obj);cmd[cmd.index('-c')+1]=str(new_unit)
 with (root/(unit_name+'-compile.log')).open('x') as log:
  result=subprocess.run(cmd,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
 if result.returncode:print((root/(unit_name+'-compile.log')).read_text()[-9000:]);raise SystemExit(result.returncode)
 compiled[unit_name]=obj;compile_commands[unit_name]=cmd
link=shlex.split((cwd/'CMakeFiles/zone.dir/link.txt').read_text())
inputs={str((cwd/t).resolve()):sha((cwd/t).resolve()) for t in link if t.endswith(('.o','.a'))}
baseline_link=list(link)
baseline_link[baseline_link.index('-o')+1]=str(root/'retained-zone')
with (root/'baseline-link.log').open('x') as log:
 result=subprocess.run(baseline_link,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
if result.returncode:print((root/'baseline-link.log').read_text()[-9000:]);raise SystemExit(result.returncode)
assert sha(root/'retained-zone')==prior['binaries']['zone']['sha256'],'Retained objects do not reproduce baseline zone'
# Replace exactly the rebuilt unity member in a private copy of its archive.
lib=root/'libgm_commands_zone.a';old_lib=cwd/'libgm_commands_zone.a'
shutil.copyfile(old_lib,lib)
old_members=subprocess.check_output(['/usr/bin/ar','t',str(old_lib)],text=True).splitlines()
member=compiled['command.cpp'].name;assert old_members.count(member)==1
subprocess.run(['/usr/bin/ar','r',str(lib),str(compiled['command.cpp'])],check=True)
subprocess.run(['/usr/bin/ranlib',str(lib)],check=True)
assert subprocess.check_output(['/usr/bin/ar','t',str(lib)],text=True).splitlines()==old_members
for name in old_members:
 if name!=member:
  assert hashlib.sha256(subprocess.check_output(['/usr/bin/ar','p',str(old_lib),name])).digest()==hashlib.sha256(subprocess.check_output(['/usr/bin/ar','p',str(lib),name])).digest()
assert link.count('libgm_commands_zone.a')==1;link[link.index('libgm_commands_zone.a')]=str(lib)
link[link.index('-o')+1]=str(root/'zone')
with (root/'link.log').open('x') as log:
 result=subprocess.run(link,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
if result.returncode:print((root/'link.log').read_text()[-9000:]);raise SystemExit(result.returncode)
assert 'not found' not in subprocess.check_output(['ldd',str(root/'zone')],text=True)
for name,h in inputs.items():assert sha(pathlib.Path(name))==h,'Retained link input changed'
for name,h in prior['all_sources'].items():assert sha(base/'source'/name)==h
for name,row in prior['binaries'].items():assert sha(base/'build/bin'/name)==row['sha256']
for name,h in {**prior['all_sources'],**changed}.items():assert sha(root/'source'/name)==h,'Candidate source drift: '+name
report={'date':'2026-10-30','status':'native translation-unit compile and zone relink passed; not installed',
 'baseline_manifest_sha256':baseline_hash,'baseline_root':str(base),'candidate_root':str(root),
 'retained_source_count':len(prior['all_sources']),'retained_link_inputs':inputs,
 'changed_sources':changed,'source_overlay':overlay,'baseline_binaries':prior['binaries'],
 'zone_sha256':sha(root/'zone'),'object_sha256':{n:sha(p) for n,p in compiled.items()},
 'baseline_relink_sha256':sha(root/'retained-zone'),
 'commands':{'compile':compile_commands,'baseline_link':baseline_link,'link':link},'working_directory':str(cwd),
 'logs':{n:sha(root/n) for n in ('command.cpp-compile.log','baseline-link.log','link.log')},
 'scope':'Only the complete command.cpp unity unit recompiled against a complete isolated source tree with full headers and no PCH. Unchanged objects/libraries reproduce the retained baseline binary exactly. command.h adds only the factions declaration; other new display helpers are private to command.cpp.',
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
    out = ROOT/'docs/releases/faction-standing-20261029/release/native-build.json'
    out.write_bytes(data)


if __name__ == '__main__':
    main()
