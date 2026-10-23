"""Package verified candidate artifacts. No production mutation."""
from pathlib import Path
import hashlib,json,shutil,subprocess,tarfile
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
build=json.loads((HERE/'native-build-manifest.json').read_text())
assert build['status']=='fresh complete native build passed'
for n,h in build['candidate_sources'].items():
 assert hashlib.sha256((ROOT/'server-mods/code'/n).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==h,n
p=HERE/'package';p.mkdir(exist_ok=False);(p/'bin').mkdir()
for name,digest in build['binaries'].items():
 subprocess.run(['docker','cp','akk-stack-eqemu-server-1:/tmp/nightcap-aa-level-progression-v1/build/bin/'+name,str(p/'bin'/name)],check=True)
 assert sha(p/'bin'/name)==digest
for name in ('rollout.py','runtime-contract.json'):shutil.copyfile(HERE/name,p/name)
inputs=json.loads((HERE/'package-inputs.json').read_text())
base=next(x['image'] for x in json.loads((HERE/'production-before.json').read_text())['services'] if x['service']=='game')
m={'base_image_id':base,'base_hashes':inputs['base_hashes'],'prior_operator_sha256':inputs['prior_operator_sha256'],'rules_before':inputs['rules_before'],'replacement_binaries':build['binaries'],'binaries':{**{n:inputs['base_hashes']['bin/'+n] for n in ('world','zone','shared_memory','loginserver','ucs')},**build['binaries']},'replacement_bytes':sum((p/'bin'/n).stat().st_size for n in build['binaries']),'client_channel_sha256':sha(HERE/'client/baseline/channel.json'),'files':{q.relative_to(p).as_posix():sha(q) for q in p.rglob('*') if q.is_file()},'source_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()}
(p/'manifest.json').write_text(json.dumps(m,indent=2)+'\n',encoding='utf-8')
out=Path('E:/EQ_Local_Dev/artifacts/aa-level-progression-20261023/server.tar.gz')
with tarfile.open(out,'w:gz',compresslevel=1) as t:
 for q in sorted(p.rglob('*')):
  if q.is_file():
   name=q.relative_to(p).as_posix();info=t.gettarinfo(str(q),arcname=name);info.mode=0o755 if name.startswith('bin/') else 0o644
   with q.open('rb') as f:t.addfile(info,f)
receipt={'status':'verified package; not deployed','archive':str(out),'archive_sha256':sha(out),'archive_bytes':out.stat().st_size,'replacement_bytes':m['replacement_bytes'],'manifest_sha256':sha(p/'manifest.json'),'binaries':m['binaries'],'source_revision':m['source_revision']}
(HERE/'package-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8');print(json.dumps(receipt))
