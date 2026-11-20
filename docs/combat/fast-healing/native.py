from pathlib import Path
import importlib.util,json,subprocess,sys,shutil
R=Path('/tmp/nightcap-fast-healing-20261120')
OLD=Path('/tmp/nightcap-titles-automatic-20261114-v2/candidate')
STACK=Path('/tmp/nightcap-classic-stack-20261114/titles-candidate')
s=importlib.util.spec_from_file_location('suffix',OLD.parent/'native.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);b=m.b
src,build,objs,rep,args,_,_,_=m.context()
for n,v in b.load(OLD/'build.json')['units'].items():
 p=OLD/(n+'.o');assert b.sha(p)==v['candidate'];rep[n]=p
rep['client_packet']=STACK/'client_packet.o'
args=[str(STACK/'libcommon.a') if x==str(m.REST/'libcommon.a') else x for x in args]
def setup():
 base=R/'baseline';base.mkdir(exist_ok=True)
 b.linker('shipping',base,build,objs,args,rep)
 assert b.sha(base/'zone')=='289df4f2037bf4e7348278442ce43db0bba498a35680adc6d1fbe06e5b0869b8'
 tree={r['name']:Path(r['external-contents']) for r in b.load(STACK/'vfs.json')['roots']}
 p=tree.get(str(src/'zone/effects.cpp'),src/'zone/effects.cpp')
 (R/'before.cpp').write_bytes(p.read_bytes())
 for stage in ['reproduced','candidate']:
  folder=R/stage;folder.mkdir(exist_ok=True);path=folder/'source/zone/effects.cpp';path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(p.read_bytes())
  if stage=='candidate':subprocess.run(['patch','--fuzz=0','--forward','-p3'],cwd=folder/'source',input=(R/'feature.patch').read_bytes(),check=True)
  overlay=dict(tree);overlay[str(src/'zone/effects.cpp')]=path
  vfs=folder/'vfs.json';vfs.write_text(json.dumps({'version':0,'use-external-names':False,'roots':[{'type':'file','name':n,'external-contents':str(p)} for n,p in overlay.items()]}))
  b.compile_unit('shipping','effects',build,src,objs,STACK/'zone.pch',vfs,folder/'effects.o')
  rr=dict(rep);rr['effects']=folder/'effects.o';b.linker('shipping',folder,build,objs,args,rr)
  if stage=='reproduced':assert b.sha(folder/'zone')==b.sha(base/'zone'),'source reproduction mismatch'
 b.save(R/'build.json',{'baseline':{'zone':b.sha(base/'zone')},'binaries':{'zone':b.sha(R/'candidate/zone')},'patch':b.sha(R/'feature.patch'),'before_source':b.sha(R/'before.cpp'),'after_source':b.sha(R/'candidate/source/zone/effects.cpp')})
 print('PASS exact baseline and changed shipping zone',flush=True)
def measure():
 for name in ['shared','maps','plugins','quests','lua_modules']:
  p=R/name
  if not p.exists():p.symlink_to(Path('/tmp/nightcap-classic-stack-20261114')/name)
 shutil.copyfile('/tmp/nightcap-classic-stack-20261114/eqemu_config.json',R/'eqemu_config.json')
 (R/'logs').mkdir(exist_ok=True)
 flags=b.ninja(build,str(objs/'main.cpp.o'));flags=flags[:flags.index('-MD')];flags[flags.index('-include-pch')+2]=str(STACK/'zone.pch')
 b.run([*flags,'-ivfsoverlay',str(STACK/'vfs.json'),'-I'+str(src/'zone'),'-o',str(R/'probe.o'),'-c',str(R/'probe.cpp')],build,R/'probe.log')
 for stage in ['reproduced','candidate']:
  folder=R/stage;rr=dict(rep);rr['effects']=folder/'effects.o';rr['main']=Path('/tmp/nightcap-classic-stack-20261114/main.o')
  aa=list(args);aa.insert(1,str(R/'probe.o'));aa.insert(1,'-Wl,--wrap=_ZNSt13random_device9_M_getvalEv');diag=folder/'diagnostic';diag.mkdir(exist_ok=True);b.linker('shipping',diag,build,objs,aa,rr)
  with (diag/'run.log').open('w') as log:
   p=subprocess.run([diag/'zone','tests:balance','input.json',stage+'.json'],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=180)
  if p.returncode:raise RuntimeError((diag/'run.log').read_text()[-3000:])
 print('PASS native measurements',flush=True)
if __name__=='__main__':setup() if sys.argv[1]=='build' else measure()

