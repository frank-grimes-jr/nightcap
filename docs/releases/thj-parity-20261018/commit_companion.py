"""Commit the exact reviewed handoff in the index, preserving integrated work files."""
import hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];REL=Path(__file__).resolve().parent
manifest=json.loads((REL/'companion-final-snapshot.json').read_text());source=Path(manifest['source'])
def git(*args,input=None):return subprocess.check_output(['git','-C',str(ROOT),*args],input=input)
assert git('branch','--show-current').decode().strip()=='feature/thj-item-spell-parity'
assert git('rev-parse','HEAD').decode().strip()=='a8e0a91382c23e52a0ffb2b79fb3f2c0c131f76a'
staged=set(git('diff','--cached','--name-only','-z').decode().rstrip('\0').split('\0'))-{''}
assert staged<=set(manifest['files']),'Index contains unrelated staged changes'
contents={name:(source/name).read_bytes() for name in manifest['files']}
for name,data in contents.items():assert hashlib.sha256(data).hexdigest()==manifest['files'][name],name
for name,data in contents.items():
    oid=git('hash-object','-w','--path='+name,'--stdin',input=data).decode().strip()
    if name in staged:assert git('ls-files','--stage','--',name).decode().split()[1]==oid,name
    git('update-index','--add','--cacheinfo','100644',oid,name)
# Unified patch context lines intentionally contain one leading space.
subprocess.run(['git','-C',str(ROOT),'diff','--cached','--check','--','.',':(exclude)**/*.patch'],check=True)
subprocess.run(['git','-C',str(ROOT),'commit','-m','feat: integrate reviewed pet and WPM scaling candidate'],check=True)
report={'commit':git('rev-parse','HEAD').decode().strip(),'files':len(contents),'source_manifest':'companion-final-snapshot.json',
        'scope':'exact reviewed companion import; integrated working files preserved; no main/test promotion'}
(REL/'companion-import-commit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
