"""Build diagnostic from exact current shipping objects; never deploy this binary."""
from pathlib import Path
import importlib.util,json,shutil,subprocess,sys
R=Path('/tmp/nightcap-classic-equipment-paths-20261121')
OLD=Path('/tmp/nightcap-classic-focus-coverage-20261120')
s=importlib.util.spec_from_file_location('prior_focus',OLD/'native.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
b,src,build,objs=m.b,m.src,m.build,m.objs
ORNAMENT=Path('/tmp/nightcap-ornaments-shipping-20261121')
EXPECTED='bceda35d719343d6e7f7ace503201a76ed47f136866f8ef94cdf95cf4c308f40'
def main():
    rep=dict(m.rep);rep['spell_effects']=OLD/'correction/candidate/spell_effects.o';rep['aa']=Path('/tmp/nightcap-aa-purchase-latency-20261121/candidate/aa.o')
    shipping=json.loads((ORNAMENT/'build.json').read_bytes())
    assert shipping['binaries']['zone']==EXPECTED
    for name in shipping['objects']:
        if name.startswith('zone/'):
            rep[Path(name).stem]=ORNAMENT/'candidate'/(Path(name).stem+'.o')
    link_args=[str(ORNAMENT/'candidate/zone-libcommon.a') if x.endswith('/libcommon.a') else x for x in m.args]
    reproduced=R/'reproduced';reproduced.mkdir(exist_ok=True)
    b.linker('shipping',reproduced,build,objs,link_args,rep)
    assert b.sha(reproduced/'zone')==EXPECTED,'current shipping reproduction mismatch'
    flags=b.ninja(build,str(objs/'main.cpp.o'));flags=flags[:flags.index('-MD')];index=flags.index('-include-pch');del flags[index-1:index+3]
    mapping=json.loads((ORNAMENT/'candidate/vfs.json').read_bytes())
    header=str(src/'zone/client.h');entry=next((x for x in mapping['roots'] if x['name']==header),None)
    original=Path(entry['external-contents'] if entry else header).read_text()
    edited=original
    for declaration in ('int64 CalcHPRegen(bool bCombat = false);','int64 CalcManaRegen(bool bCombat = false);'):
        assert edited.count(declaration)==1
        edited=edited.replace(declaration,'public: '+declaration+' private:')
    exposed=R/'client-probe-access.h';exposed.write_text(edited)
    if entry:entry['external-contents']=str(exposed)
    else:mapping['roots'].append({'type':'file','name':header,'external-contents':str(exposed)})
    vfs=R/'probe-vfs.json';vfs.write_text(json.dumps(mapping))
    b.run([*flags,'-ivfsoverlay',str(vfs),'-I'+str(src/'zone'),'-o',str(R/'probe.o'),'-c',str(R/'probe.cpp')],build,R/'probe.log')
    rep['client']=OLD/'client-diagnostic.o';rep['main']=Path('/tmp/nightcap-classic-stack-20261114/main.o')
    args=list(link_args);args[1:1]=[str(R/'probe.o'),'-Wl,--wrap=_ZNSt13random_device9_M_getvalEv','-Wl,--wrap=gettimeofday','-Wl,--wrap=time']
    diag=R/'diagnostic';diag.mkdir(exist_ok=True);b.linker('shipping',diag,build,objs,args,rep)
    b.save(R/'native-build.json',{'shipping_zone':EXPECTED,'diagnostic_zone':b.sha(diag/'zone'),'probe':b.sha(R/'probe.cpp'),'adapter':'Retained diagnostic login-completion constructor, clock, RNG and test entry point only. Two regen declarations exposed only to probe compilation; no layout or combat formula modifications.'})
    for name in ['maps','plugins','quests','lua_modules']:
        p=R/name
        if not p.exists():p.symlink_to(Path('/tmp/nightcap-classic-stack-20261114')/name)
    shutil.copyfile('/tmp/nightcap-classic-stack-20261114/eqemu_config.json',R/'eqemu_config.json');(R/'logs').mkdir(exist_ok=True)
    print('PASS current shipping reproduction and defense diagnostic build',flush=True)
def measure():
    pins=json.loads((R/'runtime.json').read_bytes())
    for name,expected in pins['caches'].items():assert b.sha(R/'shared'/name)==expected
    with (R/'run.log').open('w') as log:
        p=subprocess.run([R/'diagnostic/zone','tests:balance',sys.argv[2],sys.argv[3]],cwd=R,stdout=log,stderr=subprocess.STDOUT,timeout=900)
    if p.returncode:raise RuntimeError((R/'run.log').read_text()[-7000:])
    print('PASS native defense/pressure measurement',flush=True)
if __name__=='__main__':main() if sys.argv[1]=='build' else measure()
