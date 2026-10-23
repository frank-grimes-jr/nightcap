"""Stage only reviewed native test inputs in an isolated development directory."""
import io,tarfile,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
DEST='/tmp/nightcap-level-aa-tests-20261023'
files=['tools/tests/test_passive_aa.py','tools/tests/test_level_aa.py','tools/tests/test_level_aa_integration.py','server-mods/code/zone/exp.cpp','server-mods/code/zone/client.cpp','server-mods/code/zone/client_packet.cpp','server-mods/code/zone/zonedb.cpp','server-mods/code/zone/gm_commands/aa_exp.cpp']
if (ROOT/'server-mods/code/common/aa_progression.h').exists():
 files.append('server-mods/code/common/aa_progression.h')
buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w') as tar:
 for name in files:
  data=(ROOT/name).read_bytes(); info=tarfile.TarInfo(name); info.size=len(data); tar.addfile(info,io.BytesIO(data))
code="""
import tarfile,sys,pathlib
p=pathlib.Path(%r);p.mkdir(exist_ok=True)
archive=tarfile.open(fileobj=sys.stdin.buffer,mode='r|')
for member in archive:
 assert member.isfile() and member.name in %r
 target=(p/member.name).resolve();assert p in target.parents
 target.parent.mkdir(parents=True,exist_ok=True)
 target.write_bytes(archive.extractfile(member).read())
""" % (DEST,files)
subprocess.run(['docker','exec','-i','akk-stack-eqemu-server-1','python3','-c',code],input=buf.getvalue(),check=True)
name=sys.argv[1] if len(sys.argv)>1 else 'test_level_aa'
assert name in ('test_level_aa','test_passive_aa','test_level_aa_integration')
r=subprocess.run(['docker','exec','akk-stack-eqemu-server-1','python3',DEST+'/tools/tests/'+name+'.py','--compiler','clang++'],text=True,capture_output=True)
print(r.stdout+r.stderr)
if len(sys.argv)>2:
 assert sys.argv[2] in ('red-native.txt','green-native.txt','legacy-native.txt','integration-native.txt')
 (Path(__file__).parent/sys.argv[2]).write_text(r.stdout+r.stderr,encoding='utf-8')
sys.exit(r.returncode)
