import io,json,subprocess,tarfile
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
files=['zone/dungeon_service.cpp','zone/dungeon_service.h','common/dungeon_policy.h','common/dungeon_catalog.h','common/dungeon_contract.h']
buffer=io.BytesIO()
with tarfile.open(fileobj=buffer,mode='w') as archive:
    for name in files:
        data=(ROOT/'server-mods/code'/name).read_bytes().replace(b'\r\n',b'\n');info=tarfile.TarInfo(name);info.size=len(data);archive.addfile(info,io.BytesIO(data))
command=['docker','exec','-i','akk-stack-eqemu-server-1']
extract="""import pathlib,tarfile,sys
p=pathlib.Path('/tmp/nightcap-hate-keeper-input');p.mkdir(exist_ok=True)
archive=tarfile.open(fileobj=sys.stdin.buffer,mode='r|')
for member in archive:
 assert member.isfile() and member.name in %r
 target=p/member.name;target.parent.mkdir(exist_ok=True)
 # Stream extraction is safe after checking this exact local payload allowlist.
 member_path=target.resolve();assert p in member_path.parents
 target.write_bytes(archive.extractfile(member).read())
""" % files
subprocess.run(command+['python3','-c',extract],input=buffer.getvalue(),check=True)
subprocess.run(command+['python3','-'],input=(HERE/'build.py').read_bytes(),check=True)
subprocess.run(['docker','cp','akk-stack-eqemu-server-1:/tmp/nightcap-hate-keeper-build-v1/manifest.json',str(HERE/'build-manifest.json')],check=True)
