"""Archive only declared diagnostic evidence; never include runtime configuration."""
import json
from pathlib import Path
import tarfile

root=Path('/tmp/nightcap-balance-wpm-20261018')
assert Path.cwd()==root
matrix=json.loads((root/'matrix.json').read_text())
names=['matrix.json','matrix-results.json','native-build-manifest.json']
for case in matrix['cases']:
    name=case['id']
    assert name.replace('-','').isalnum()
    names.extend([name+'-input.json',name+'-result.json',name+'.log'])
with tarfile.open('/tmp/wpm-native-results.tar.gz','w:gz') as archive:
    for name in names:
        path=root/name
        if path.is_file():archive.add(path,arcname=name)
print(json.dumps({'files':len(names),'archive':'/tmp/wpm-native-results.tar.gz'}))
