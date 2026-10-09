import difflib,json,subprocess
from pathlib import Path
root=Path(__file__).parent;out=root/'hardened-input';out.mkdir(exist_ok=True)
repo=Path(r'C:/Users/verre/.codex/worktrees/zone-loot-hunt-forge/EQ_Local_Dev')
def git(*a):return subprocess.check_output(['git',*a],cwd=repo).decode('utf-8')
status=git('diff','--name-status','d5f273f','77f5d63','--','server-mods/code').splitlines()
parts=[];added=[];changed=[]
for row in status:
    kind,path=row.split('\t');name=path.removeprefix('server-mods/code/')
    new=git('show','77f5d63:'+path)
    if kind=='A' and name!='zone/zone.cpp':
        target=out/'added'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(new,encoding='utf-8',newline='\n');added.append(name);continue
    assert kind=='M' or name=='zone/zone.cpp'
    old=Path(r'E:/EQ_Local_Dev/akk-stack/code/zone/zone.cpp').read_text() if name=='zone/zone.cpp' else git('show','d5f273f:'+path)
    parts.extend(difflib.unified_diff(old.splitlines(keepends=True),new.splitlines(keepends=True),fromfile='a/'+name,tofile='b/'+name))
    changed.append(name)
(out/'changes.patch').write_text(''.join(parts),encoding='utf-8',newline='\n')
(out/'changed.json').write_text(json.dumps(changed))
(out/'added.json').write_text(json.dumps(added))
print(json.dumps({'patched':changed,'added':added}))
