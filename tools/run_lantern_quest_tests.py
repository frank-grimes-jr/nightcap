"""Run Perl boundary tests in the retained Linux development container."""
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]


def main():
    names=('server-mods/plugins/epic05.pl','server-mods/plugins/epic05_data.pl',
           'server-mods/quests/global/items/900501.pl','tools/tests/epic05_quests.t')
    sources={n:(ROOT/n).read_text(encoding='utf-8') for n in names}
    code=r'''
from pathlib import Path
import subprocess
p=Path('/tmp/nightcap-lantern-quest-qa');p.mkdir(exist_ok=True)
for n,s in SOURCES.items():
 f=p/n;f.parent.mkdir(exist_ok=True,parents=True);f.write_text(s)
r=subprocess.run(['perl',str(p/'tools/tests/epic05_quests.t'),str(p)],capture_output=True,text=True)
print(r.stdout);assert r.returncode==0,r.stderr
'''
    r=subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-'],input='SOURCES='+repr(sources)+'\n'+code,
                     text=True,encoding='utf-8',capture_output=True,timeout=120)
    (ROOT/'docs/adventure-journal/release-20261107/oath-dialogue-tests.txt').write_text(r.stdout+r.stderr,encoding='utf-8')
    print((r.stdout+r.stderr)[-4500:])
    if r.returncode:raise SystemExit(r.returncode)


if __name__=='__main__':main()
