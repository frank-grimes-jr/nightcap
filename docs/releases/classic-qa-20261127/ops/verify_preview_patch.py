"""Apply the whole preview patch against pristine upstream and compare its output to shipped source."""
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import zipfile

from build_preview import OUT, SRC, capture

BASE='45cf0cf6489f30f39f660c6791a85d4e531d6f8f'
data=(capture.HERE.parents[2]/'qa/cairnwright-hailstone/nightcap-preview.patch').read_bytes().replace(b'\r\n',b'\n')
names=[n.decode() for n in re.findall(rb'^diff --git a/(\S+) b/\1\r?$',data,re.M)]
assert names and len(names)==len(set(names))
with tempfile.TemporaryDirectory(dir=OUT) as temp, zipfile.ZipFile(OUT/'nightcap-hailstone-source.zip') as archive:
    work=Path(temp)
    for name in names:
        row=subprocess.run(['git','show',BASE+':'+name],cwd=SRC,capture_output=True)
        if row.returncode:
            assert ('new file mode' in data.split(('diff --git a/'+name+' b/'+name).encode(),1)[1].split(b'@@',1)[0].decode())
            continue
        target=work/name
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(row.stdout)
    env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(work.parent))
    for options in (['--check'],[]):
        subprocess.run(['git','apply','--no-index','--whitespace=nowarn',*options,'-'],input=data,cwd=work,env=env,check=True)
    for name in names:
        assert (work/name).read_bytes().splitlines()==archive.read('hailstone/'+name).splitlines(),name
result={'upstream':BASE,'applied_files':len(names),'matches_paired_source':True}
(OUT/'patch-check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))

