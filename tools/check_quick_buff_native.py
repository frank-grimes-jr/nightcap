"""Compile Quick Buff's two complete translation units in an isolated snapshot.

No linking, installation, database writes, runtime restart or release is performed.
The added Client member requires a full zone rebuild before a future deployment.
"""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/releases/quick-buff-20261112'
REMOTE = r'''
from pathlib import Path
import hashlib,json,shlex,shutil,subprocess,tempfile
base=Path('/tmp/nightcap-last-lantern-20261107-v1')
old=Path('/tmp/nightcap-power-source-xp-display-20261103-v1')
dest=Path(tempfile.mkdtemp(prefix='nightcap-quick-buff-20261112-'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,pin in BASELINE.items():
 assert sha(base/'source'/name)==pin, 'Retained source differs from task baseline: '+name
shutil.copytree(base/'source',dest/'source')
for name,text in SOURCES.items():
 p=dest/'source'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
pch=dest/'cmake_pch.hxx'
pch.write_text((base/'cmake_pch.hxx').read_text().replace(str(base/'source'),str(dest/'source')))
flags=(old/'build/zone/CMakeFiles/zone.dir/flags.make').read_text()
parts=[next(l.split(' = ',1)[1] for l in flags.splitlines() if l.startswith(k+' = ')) for k in ('CXX_DEFINES','CXX_INCLUDES','CXX_FLAGS')]
args=['/usr/bin/clang++','-I'+str(dest/'source')]+shlex.split(' '.join(parts))+['-include',str(pch)]
results=[]
for unit in ('aa.cpp','spells.cpp'):
 command=args+['-fsyntax-only',str(dest/'source/zone'/unit)]
 with (dest/(unit+'.log')).open('w') as log:
  result=subprocess.run(command,cwd=old/'build',stdout=log,stderr=subprocess.STDOUT)
 if result.returncode:raise RuntimeError(unit+'\n'+(dest/(unit+'.log')).read_text()[-8000:])
 results.append(dict(unit=unit,status='PASS',command=command))
 print(unit+': PASS',flush=True)
assert all(sha(base/'source'/n)==h for n,h in BASELINE.items())
report=dict(status='PASS',scope='Complete native translation-unit syntax checks; not a full link or runtime test',
 directory=str(dest),retained_baseline=BASELINE,source_sha256={n:sha(dest/'source'/n) for n in SOURCES},compiles=results)
print('REPORT='+json.dumps(report),flush=True)
'''


def main():
    names = ('common/quick_buff.h', 'zone/aa_quick_buff.inc', 'zone/aa.cpp',
             'zone/client.h', 'zone/spells.cpp')
    sources = {n: (ROOT / 'server-mods/code' / n).read_text(encoding='utf-8') for n in names}
    baseline = {n: hashlib.sha256(subprocess.check_output(
        ['git', 'show', 'b7e404b2:server-mods/code/' + n], cwd=ROOT)).hexdigest()
        for n in names if n.endswith(('.cpp', 'client.h'))}
    result = subprocess.run(['docker', 'exec', '-i', 'akk-stack-eqemu-server-1', 'python3', '-'],
        input=f'SOURCES={sources!r}\nBASELINE={baseline!r}\n'+REMOTE,
        text=True, encoding='utf-8', capture_output=True, timeout=1800)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'native-compile.log').write_text(result.stdout+'\n'+result.stderr, encoding='utf-8')
    for line in result.stdout.splitlines():
        if line.startswith('REPORT='):
            (OUT / 'native-compile.json').write_text(json.dumps(json.loads(line[7:]), indent=2)+'\n')
        else:
            print(line)
    if result.returncode:
        print(result.stderr[-8000:])
        raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
