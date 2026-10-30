"""Verify the dev Hunt delta against the completed item-XP build; never install."""
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile
import uuid

ROOT = Path(__file__).resolve().parents[1]
CONTAINER = 'akk-stack-eqemu-server-1'
FILES = {'common/zone_hunt_policy.h', 'zone/zone_hunt.cpp'}


def main():
    folder = ROOT/'docs/items/power-source-xp'
    raw = (folder/'native-build.json').read_bytes().replace(b'\r\n', b'\n')
    prior = json.loads(raw)
    baseline_hash = json.loads((folder/'verification.json').read_bytes())['full_build']['manifest_sha256']
    assert hashlib.sha256(raw).hexdigest() == baseline_hash
    overlay = {p.relative_to(ROOT/'server-mods/code').as_posix():
               hashlib.sha256(p.read_bytes().replace(b'\r\n', b'\n')).hexdigest()
               for p in (ROOT/'server-mods/code').rglob('*') if p.is_file()}
    inputs = {n: (ROOT/'server-mods/code'/n).read_bytes() for n in FILES}
    for name, data in inputs.items():
        dev = subprocess.check_output(['git','show','origin/dev:server-mods/code/'+name], cwd=ROOT)
        assert dev.replace(b'\r\n', b'\n') == data.replace(b'\r\n', b'\n'), name
    changed = {n: hashlib.sha256(data).hexdigest() for n, data in inputs.items()}
    dest = '/tmp/nightcap-item-xp-integration-' + uuid.uuid4().hex[:12]
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode='w') as tar:
        for name, data in inputs.items():
            entry = tarfile.TarInfo(name); entry.size = len(data)
            tar.addfile(entry, io.BytesIO(data))
    unpack = '''import sys,tarfile
from pathlib import Path
root=Path(DEST);root.mkdir(exist_ok=False)
with tarfile.open(fileobj=sys.stdin.buffer,mode='r|') as archive:
 for entry in archive:
  assert entry.isfile() and entry.name in FILES
  p=root/'input'/entry.name;p.parent.mkdir(parents=True,exist_ok=True)
  p.write_bytes(archive.extractfile(entry).read())
'''
    subprocess.run(['docker','exec','-i',CONTAINER,'python3','-c',
                    f'DEST={dest!r}\nFILES={FILES!r}\n'+unpack], input=archive.getvalue(), check=True)
    remote = r'''
import hashlib,json,re,shlex,shutil,subprocess
from pathlib import Path
root=Path(DEST);base=Path(prior['candidate_root']);source=root/'source'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
canonical=lambda p:hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
assert sha(base/'manifest.json')==baseline_hash
for n,h in prior['all_sources'].items():assert sha(base/'source'/n)==h,'Baseline source drift: '+n
for n,row in prior['binaries'].items():assert sha(base/'build/bin'/n)==row['sha256']
assert {n for n,h in overlay.items() if n not in prior['all_sources'] or canonical(base/'source'/n)!=h}==FILES
for n,h in changed.items():assert sha(root/'input'/n)==h
old=(base/'source/common/zone_hunt_policy.h').read_text()
new=(root/'input/common/zone_hunt_policy.h').read_text()
start=new.index('// A real spawn');end=new.index('inline bool BeginDeathRoll',start)
assert new[:start]+new[end:]==old,'Existing header declarations/definitions changed'
assert re.findall(r'^inline bool (\w+)\(',new[start:end],re.M)==['RegularCombatSpawn','AugmentDeathEligible']
# Only zone_hunt.cpp calls the two added inline helpers. Existing objects retain
# identical used definitions, layouts and rule indices; no old PCH is consumed.
for n in prior['all_sources']:
 if n.endswith(('.cpp','.h')) and n not in FILES:
  text=(base/'source'/n).read_text(errors='replace')
  assert 'RegularCombatSpawn' not in text and 'AugmentDeathEligible' not in text,n
source.mkdir()
for n in prior['all_sources']:
 p=source/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(base/'source'/n,p)
for n in FILES:shutil.copy2(root/'input'/n,source/n)
commands=json.loads((base/'build/compile_commands.json').read_text())
units=[c for c in commands if c['file']==str(base/'source/zone/zone_hunt.cpp')]
assert len(units)==1
unit=units[0];cwd=Path(unit['directory']);cmd=shlex.split(unit['command'])
for i in range(len(cmd)-4,-1,-1):
 if cmd[i:i+3]==['-Xclang','-include-pch','-Xclang']:del cmd[i:i+4]
for i in range(len(cmd)-3):
 if cmd[i:i+3]==['-Xclang','-include','-Xclang']:
  pch=root/'zone-hunt-pch.hxx'
  pch.write_text(Path(cmd[i+3]).read_text().replace(str(base/'source'),str(source)))
  cmd[i+3]=str(pch)
cmd=[s.replace(str(base/'source'),str(source)) for s in cmd]
old_object=(cwd/cmd[cmd.index('-o')+1]).resolve()
obj=root/'zone_hunt.cpp.o';cmd[cmd.index('-o')+1]=str(obj)
def run(label,command):
 print(label,flush=True)
 with (root/(label+'.log')).open('x') as log:r=subprocess.run(command,cwd=cwd,stdout=log,stderr=subprocess.STDOUT)
 if r.returncode:print((root/(label+'.log')).read_text()[-9000:]);raise SystemExit(r.returncode)
run('compile',cmd)
link=shlex.split((cwd/'CMakeFiles/zone.dir/link.txt').read_text())
link_inputs={str((cwd/t).resolve()):sha((cwd/t).resolve()) for t in link if t.endswith(('.o','.a'))}
baseline=list(link);baseline[baseline.index('-o')+1]=str(root/'retained-zone')
run('baseline-link',baseline)
assert sha(root/'retained-zone')==prior['binaries']['zone']['sha256'],'Baseline relink differs'
matches=[i for i,t in enumerate(link) if t.endswith('.o') and (cwd/t).resolve()==old_object]
assert len(matches)==1
link[matches[0]]=str(obj);link[link.index('-o')+1]=str(root/'zone')
run('integration-link',link)
dependencies=subprocess.check_output(['ldd',str(root/'zone')],text=True)
assert 'not found' not in dependencies
for n,h in link_inputs.items():assert sha(Path(n))==h,'Retained link input changed'
for n,h in prior['all_sources'].items():assert sha(base/'source'/n)==h
for n,row in prior['binaries'].items():assert sha(base/'build/bin'/n)==row['sha256']
pins={**prior['all_sources'],**changed}
for n,h in pins.items():assert sha(source/n)==h
report={'date':'2026-10-30','status':'integration compile/relink passed; not installed',
 'candidate_root':DEST,'baseline_root':str(base),'baseline_manifest_sha256':baseline_hash,
 'all_sources':pins,'changed_sources':changed,'normalized_overlay':overlay,
 'retained_link_inputs':link_inputs,'baseline_relink_sha256':sha(root/'retained-zone'),
 'zone_sha256':sha(root/'zone'),'zone_ldd':dependencies,'object_sha256':sha(obj),
 'unchanged_paired_binaries':{n:prior['binaries'][n] for n in ('world','shared_memory')},
 'commands':{'compile':cmd,'baseline_link':baseline,'integration_link':link},
 'logs':{n:sha(root/(n+'.log')) for n in ('compile','baseline-link','integration-link')},
 'scope':'Existing dev Hunt policy adds two inline helpers used only by zone_hunt.cpp. That unit is rebuilt with current headers and without old PCH. All other used definitions/layouts/rule indices are unchanged. Retained inputs first reproduce the full item-XP zone byte-for-byte; world/shared_memory retain the matching full-build hashes.',
 'production_changed':False,'owner_accepted':False}
(root/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print(report['status'],flush=True)
'''
    prefix = (f'DEST={dest!r}\nprior={prior!r}\nFILES={FILES!r}\noverlay={overlay!r}\n'
              f'changed={changed!r}\nbaseline_hash={baseline_hash!r}\n')
    print('Isolated integration: '+dest, flush=True)
    subprocess.run(['docker','exec','-i',CONTAINER,'python3','-'], input=prefix+remote,
                   text=True, encoding='utf-8', check=True)
    assert all(hashlib.sha256((ROOT/'server-mods/code'/n).read_bytes()).hexdigest()==h for n,h in changed.items())
    data = subprocess.check_output(['docker','exec',CONTAINER,'cat',dest+'/manifest.json'])
    (folder/'integration-native-build.json').write_bytes(data)


if __name__ == '__main__':
    main()
