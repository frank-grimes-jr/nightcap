"""Regenerate the combined client delta, reusing only source-identical companion DLL."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];REL=Path(__file__).resolve().parent
handoff=json.loads((REL/'companion-final-snapshot.json').read_text());source=Path(handoff['source'])
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inputs={}
for folder in ('src','config','patches'):
    for path in (source/'eq-client-dll'/folder).rglob('*'):
        if path.is_file():
            name=path.relative_to(source);target=ROOT/name
            assert target.is_file() and path.read_bytes().replace(b'\r\n',b'\n')==target.read_bytes().replace(b'\r\n',b'\n'),str(name)
            inputs[name.as_posix()]={'companion_sha256':sha(path),'candidate_sha256':sha(target),
                'normalized_sha256':hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()}
manifest=json.loads((source/'docs/releases/wpm-melee-20261018/evidence/client-stage.json').read_text())
dll=source/'eq-client-dll/build/dinput8.dll'
assert sha(dll)==manifest['files']['dinput8.dll']['sha256'],'Companion DLL drift'
target=ROOT/'eq-client-dll/build/dinput8.dll';target.parent.mkdir(parents=True,exist_ok=True)
if target.exists():assert sha(target)==sha(dll),'Existing DLL differs'
else:target.write_bytes(dll.read_bytes())
out=ROOT.parent/'thj-parity-client-delta'
subprocess.run([sys.executable,str(ROOT/'docs/releases/wpm-melee-20261018/stage_client.py'),
    '--client','E:/EQ_Local_Dev/Client_RoF2_Dev/everquest_rof2','--output',str(out)],check=True,stdout=subprocess.DEVNULL)
report=json.loads((out/'manifest.json').read_text())
assert report['files']==manifest['files'],'Client delta unexpectedly differs from companion'
report.update(output=str(out),dll_source_inputs=inputs,
    pairing='Formula and numeric item changes need server/cache pairing; no extra client spell rows beyond the unchanged WPM/pet delta')
(REL/'evidence/client-stage.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'output':str(out),'status':report['status'],'files':len(report['files']),'source_files_verified':len(inputs)}))
