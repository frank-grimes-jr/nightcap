"""Compile changed native units against authenticated retained live source; never install."""
import hashlib
import json
from pathlib import Path
import subprocess
from augment_audit import ROOT, OUT

LIVE = '/tmp/nightcap-power-source-xp-display-20261103-v1'
DEST = '/tmp/nightcap-augment-audit-20261106-v2'
BASE = '1b443b5a'  # Audit patch base, never the feature branch's moving HEAD.
FILES = ['zone/zone_hunt.cpp', 'zone/zone_hunt.h', 'common/zone_hunt_policy.h',
         'zone/bonuses.cpp', 'zone/attack.cpp', 'zone/dungeon_service.cpp']
REMOTE = r'''
import hashlib,json,pathlib,subprocess,shutil,shlex,difflib
live=pathlib.Path(LIVE);dest=pathlib.Path(DEST)
sha=lambda b:hashlib.sha256(b).hexdigest()
normalized=lambda b:b.replace(b'\r\n',b'\n')
evidence={'status':'preflight','retained_source':LIVE,'files':{}}
for name in FILES:
 raw=(live/'source'/name).read_bytes()
 if normalized(raw).decode()!=BEFORE[name]:raise RuntimeError('Retained source differs from task base: '+name+'\n'+''.join(difflib.unified_diff(BEFORE[name].splitlines(True),normalized(raw).decode().splitlines(True)))[:18000])
 evidence['files'][name]={'base_sha256':sha(raw),'candidate_sha256':sha(AFTER[name].encode())}
flags=(live/'build/zone/CMakeFiles/zone.dir/flags.make').read_text()
parts={k:next(line.split(' = ',1)[1] for line in flags.splitlines() if line.startswith(k+' = ')) for k in ('CXX_DEFINES','CXX_INCLUDES','CXX_FLAGS')}
assert '# compile CXX with /usr/bin/clang++' in flags
evidence['flags_sha256']=sha(flags.encode())
units=[name for name in FILES if name.endswith('.cpp')]
dest.mkdir(exist_ok=False)
shutil.copytree(live/'source',dest/'source',symlinks=True)
for name in FILES:(dest/'source'/name).write_text(AFTER[name])
pch=(live/'build/zone/CMakeFiles/zone.dir/cmake_pch.hxx').read_text()
(dest/'cmake_pch.hxx').write_text(pch.replace(str(live/'source'),str(dest/'source')))
evidence['pch_header_sha256']=sha(pch.encode())
evidence['compiles']=[]
for unit in units:
 name=pathlib.Path(unit).name
 args=['/usr/bin/clang++']+shlex.split(' '.join(parts.values()))+['-c',str(live/'source'/unit)]
 args=[a.replace(str(live/'source'),str(dest/'source')) for a in args]
 out=dest/(name+'.o');args+=['-o',str(out)]
 args+=['-include',str(dest/'cmake_pch.hxx')]
 with (dest/(name+'.log')).open('w') as log:
  p=subprocess.run(args,cwd=dest,stdout=log,stderr=subprocess.STDOUT)
 if p.returncode:raise RuntimeError('Compile failed: '+str(dest/(name+'.log')))
 evidence['compiles'].append({'unit':name,'object_sha256':sha(out.read_bytes()),'log':str(dest/(name+'.log'))})
evidence['status']='PASS';evidence['scope']='four changed translation units; no link, install, production or player QA'
(dest/'evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
print(json.dumps(evidence))
'''


def main():
    before = {n: subprocess.check_output(['git', 'show', BASE + ':server-mods/code/' + n], cwd=ROOT).replace(b'\r\n', b'\n').decode() for n in FILES}
    # Reviewed existing live correction, absent from main's selective mirror.
    # Preserve actual Hate spawn mapping; never overwrite it with older source.
    old = '\t\t\t"FROM nightcap_dungeon_spawns p LEFT JOIN spawn2 s ON p.zone_id=186 AND s.id=p.spawn_id AND s.zone=\'hateplane\' "\n\t\t\t"WHERE p.zone_id={}",current.dungeon->zone));'
    new = '\t\t\t"FROM nightcap_dungeon_spawns p LEFT JOIN spawn2 s ON p.zone_id=186 AND s.id=({}) "\n\t\t\t"AND s.zone=\'hateplane\' AND s.version=0 AND s.spawngroupID=p.group_id "\n\t\t\t"WHERE p.zone_id={}",HateSpawnSourceSQL,current.dungeon->zone));'
    assert before['zone/dungeon_service.cpp'].count(old) == 1
    before['zone/dungeon_service.cpp'] = before['zone/dungeon_service.cpp'].replace(old, new)
    after = {n: (ROOT / 'server-mods/code' / n).read_text(encoding='utf-8') for n in FILES}
    inputs = dict(LIVE=LIVE, DEST=DEST, FILES=FILES, BEFORE=before, AFTER=after)
    prefix = ''.join(f'{k}={v!r}\n' for k, v in inputs.items())
    p = subprocess.run(['docker', 'exec', '-i', 'akk-stack-eqemu-server-1', 'python3', '-'],
                       input=prefix + REMOTE, text=True, encoding='utf-8', capture_output=True, timeout=900)
    if p.returncode:
        raise RuntimeError(p.stderr[-19000:])
    data = json.loads(p.stdout)
    (OUT / 'native-compile.json').write_text(json.dumps(data, indent=2) + '\n')
    print(json.dumps(data))


if __name__ == '__main__':
    main()
