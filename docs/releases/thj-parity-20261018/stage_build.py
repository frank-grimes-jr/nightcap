"""Stage exact combined source inputs; no installation or running-service writes."""
import hashlib,json,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
REL=Path(__file__).resolve().parent
STAGE=ROOT.parent/'thj-parity-build-input'
STAGE.mkdir(exist_ok=True)
previous=json.loads((ROOT/'docs/releases/wpm-melee-20261018/evidence/native-build-manifest.json').read_text())
expected={}
for name in sorted(set(previous['requested_sources'])|{'common/nightcap_spell_scaling.h'}):
    data=(ROOT/'server-mods/code'/name).read_bytes().replace(b'\r\n',b'\n')
    target=STAGE/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    expected[name]=hashlib.sha256(data).hexdigest()
(STAGE/'expected.json').write_text(json.dumps(expected,indent=2)+'\n')
text=(ROOT/'docs/releases/wpm-melee-20261018/build.py').read_text()
text=text.replace('/tmp/nightcap-wpm-pet-v1','/tmp/nightcap-thj-parity-v1').replace('/tmp/nightcap-wpm-pet-input','/tmp/nightcap-thj-parity-input')
text=text.replace("'world', 'zone', '-j3'","'world', 'zone', 'shared_memory', '-j2'").replace("('world', 'zone')","('world', 'zone', 'shared_memory')")
text=text.replace("'owner_gameplay_accepted': False", "'shared_memory_sha256': sha(ROOT / 'build/bin/shared_memory'), 'owner_gameplay_accepted': False")
(STAGE/'build.py').write_text(text)
refresh=(ROOT/'docs/releases/wpm-melee-20261018/refresh_build.py').read_text()
(STAGE/'refresh_build.py').write_text(refresh)
target=ROOT.parent/'thj-parity-build-input.tar'
with tarfile.open(target,'w') as archive:archive.add(STAGE,arcname='nightcap-thj-parity-input')
print(target)
