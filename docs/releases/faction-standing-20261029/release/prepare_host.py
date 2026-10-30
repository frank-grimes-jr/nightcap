PINS={'runtime': {'path': '/opt/nightcap/releases/zone-hunt-20261009/runtime_ops.py', 'canonical_sha256': '2ea86415001b4f325da208202ab936989a166e607a950ad7142802e84c46a459'}, 'state': {'path': '/opt/nightcap/releases/classic-dungeons-rewards-20261022/rollout.py', 'canonical_sha256': '1fbb9cb7304982ab06c71e38c4aff349a1dae0443bdf91c55e945342b61c9af1', 'token_sha256': 'c2c265919a028baf3a4b8183c0de3ab38c3262282b88e684c63220d47bf942cc'}, 'startup': {'path': '/opt/nightcap/releases/aa-level-progression-20261023-v3/rollout.py', 'canonical_sha256': '2142ef0a4ce69caf067baada197d7aef269edc5382a1e440e6d5552b84e17dc0'}, 'market': {'path': '/opt/nightcap/releases/quest-tier-handins-20261022/rollout.py', 'canonical_sha256': 'cc59f172e3ec80eade848d389e10d3cb78a4e182624ebed7f675769b42de3ab7'}}
from pathlib import Path
import fcntl,hashlib,importlib.util,json,os,shutil,subprocess,ast,io,tokenize
ROOT=Path('/opt/nightcap/deploy/production');STAGE=Path('/opt/nightcap/releases/faction-standing-20261030-v1')
os.umask(0o077)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
with (ROOT/'.deployment.lock').open('a') as lock:
 fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 assert not STAGE.exists(),'Inspect retained stage before any continuation'
 helpers={};matches={}
 for name,pin in PINS.items():
  p=Path(pin['path']);matches[name]=hashlib.sha256(p.read_bytes().replace(b'\r\n',b'\n')).hexdigest()==pin['canonical_sha256']
  if name=='state':
   lines=p.read_text().splitlines(True)
   for node in reversed(ast.parse(p.read_text()).body):
    if isinstance(node,ast.FunctionDef) and node.name in ('market','verify_market'):
     assert not node.decorator_list and not node.args.defaults and not node.args.kw_defaults
     del lines[node.lineno-1:node.end_lineno]
   tokens=[(tokenize.tok_name[t.type],t.string) for t in tokenize.generate_tokens(io.StringIO(''.join(lines)).readline) if t.type not in (tokenize.COMMENT,tokenize.NL,tokenize.NEWLINE,tokenize.INDENT,tokenize.DEDENT)]
   matches[name]=hashlib.sha256(repr(tokens).encode()).hexdigest()==pin['token_sha256']
  helpers[name]={'path':str(p),'sha256':sha(p)}
 assert all(matches.values()),matches
 spec=importlib.util.spec_from_file_location('runtime',helpers['runtime']['path']);r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
 image=r.state('game')['Image'];assert image=='sha256:0dec2bfc8b2e83a30301c2fc203c5688d44a2b39cf354b5e0e0b2ba8ed38f9dd'
 hashes=r.image_hashes(image);assert hashes['bin/zone']=='796ebedabf14e525043f69cbcc6469d55667912b7b97281d5afe348d97730518'
 contract=Path('/opt/nightcap/releases/hate-layout-20261029-v1/runtime-contract.json')
 assert sha(contract)=='ef0773d9bcfef92b825b46edd5d166a53a26287ed417497df20bdab31e166bbe'
 containers=json.loads(subprocess.check_output(['docker','inspect',*subprocess.check_output(['docker','ps','-aq'],text=True).split()],text=True))
 mounts=[Path(m['Source']) for row in containers for m in row['Mounts']]
 candidates=[]
 for manifest in sorted(Path('/opt/nightcap/releases').glob('*/manifest.json')):
  try:
   m=json.loads(manifest.read_text());p=manifest.parent/'bin/zone';digest=m.get('files',{}).get('bin/zone')
   if not digest or not p.is_file() or p.stat().st_size<150*1024**2:continue
   if p.resolve()!=p or p.stat().st_nlink!=1 or any(p.is_relative_to(x) for x in mounts):continue
   if sha(p)!=digest:continue
   candidates.append({'path':str(p),'sha256':digest,'bytes':p.stat().st_size,'manifest_sha256':sha(manifest)})
  except (ValueError,KeyError):continue
 # Retain full inventory privately on the server. Return aggregate planning only.
 STAGE.mkdir(mode=0o700)
 baseline={'base_image_id':image,'base_hashes':hashes,'helpers':helpers,'contract':{'path':str(contract),'sha256':sha(contract)},'client_channel_sha256':sha(ROOT/'data/public/channel.json')}
 (STAGE/'baseline.json').write_text(json.dumps(baseline,indent=2)+'\n')
 (STAGE/'disk-plan.json').write_text(json.dumps(candidates,indent=2)+'\n')
 print(json.dumps({'status':'private host plan saved','helpers_match_reviewed_source':matches,'production_baseline_verified':True,'candidate_count':len(candidates),'candidate_bytes':sum(x['bytes'] for x in candidates),'free_bytes':shutil.disk_usage(ROOT).free,'services_changed':False,'private_inventory_exported':False}))
