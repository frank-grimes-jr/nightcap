"""Refresh an existing explicitly enumerated build input; no installation."""
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

ROOT=Path(__file__).resolve().parents[3]
STAGE=ROOT.parent/'wpm-build-input'


def main():
    expected=json.loads((STAGE/'expected.json').read_text())
    for name in expected:
        data=(ROOT/'server-mods/code'/name).read_bytes().replace(b'\r\n',b'\n')
        target=STAGE/'source'/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
        expected[name]=hashlib.sha256(data).hexdigest()
    (STAGE/'expected.json').write_text(json.dumps(expected,indent=2)+'\n')
    for name in ('build.py','refresh_build.py'):
        shutil.copyfile(Path(__file__).with_name(name),STAGE/name)
    target=ROOT.parent/'wpm-build-input.tar'
    with tarfile.open(target,'w') as archive:archive.add(STAGE,arcname='nightcap-wpm-pet-input')
    print(json.dumps({'files':len(expected),'archive':str(target)}))


if __name__=='__main__':main()
