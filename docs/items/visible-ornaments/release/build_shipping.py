"""Build from the retained production link inputs with only reviewed ornament deltas."""
import concurrent.futures
import json
import runpy
import shutil
import subprocess
from pathlib import Path

root = Path('/tmp/nightcap-ornaments-shipping-20261121')
aa = runpy.run_path('/tmp/nightcap-aa-purchase-latency-20261121/native.py')
source, build, objs, b = (aa[k] for k in ('source', 'build', 'objects', 'b'))
shipping = aa['shipping']
prev = aa['ROOT'] / 'candidate'
rest = Path('/tmp/nightcap-rest-test-20261114/shipping')
folder = root / 'candidate'
folder.mkdir(exist_ok=True)
base = root / 'baseline'
base.mkdir(exist_ok=True)
vfs = folder / 'vfs.json'
mapping = {r['name']:Path(r['external-contents']) for r in b.load(prev/'vfs.json')['roots']}
rep = dict(shipping.m.rep, aa=prev/'aa.o', spell_effects=shipping.C/'candidate/spell_effects.o')
args = list(shipping.m.args)
world_args = b.ninja(build,'bin/world')[2:-2]
world_args = [str(rest/'libcommon.a') if x=='bin/libcommon.a' else x for x in world_args]

def link_world(path, args):
    args=list(args)
    args[args.index('-o')+1]=str(path/'world.raw')
    b.run(args,build,path/'world-link.log')
    b.run(['objcopy','--strip-debug',str(path/'world.raw'),str(path/'world')],build,path/'world-strip.log')

def changed_sources():
    for dest in sorted((root/'after').rglob('*')):
        if not dest.is_file(): continue
        name = dest.relative_to(root/'after')
        before = root/'before'/name
        effective = mapping.get(str(source/name),source/name)
        target=folder/'source'/name
        target.parent.mkdir(parents=True,exist_ok=True)
        if not effective.exists():
            assert not before.exists(), name
            shutil.copyfile(dest,target)
        else:
            original=effective.read_bytes().replace(b'\r\n',b'\n')
            target.write_bytes(original)
            if name.as_posix()=='world/worlddb.cpp':
                assert not before.exists()
                # The source mirror first gained worlddb.cpp with this release.
                import difflib
                prior=(Path('/home/eqemu/code')/name).read_text()
                patch=''.join(difflib.unified_diff(prior.splitlines(True),dest.read_text().splitlines(True),'a','b'))
                assert len(patch.splitlines())<65 and 'NightcapOrnaments' in patch
            else:
                assert before.is_file(), name
                import difflib
                patch=''.join(difflib.unified_diff(before.read_text().splitlines(True),dest.read_text().splitlines(True),'a','b'))
            if patch:
                subprocess.run(['patch','--fuzz=0','--forward',str(target)],input=patch.encode(),check=True)
        mapping[str(source/name)]=target
    shipping.overlay(mapping,vfs)

def compiled(name):
    component=name.split('/')[0]
    if component=='zone':
        out=folder/(Path(name).stem+'.o')
        b.compile_unit('shipping',Path(name).stem,build,source,objs,folder/'zone.pch',vfs,out)
    else:
        target=component+'/CMakeFiles/'+component+'.dir/'+name.split('/',1)[1]+'.o'
        opt=b.ninja(build,target)
        opt=opt[:opt.index('-MD')]
        out=folder/(Path(name).name+'.o')
        b.run([*opt,'-ivfsoverlay',str(vfs),'-o',str(out),'-c',str(source/name)],build,out.with_suffix('.log'))
    print('Compiled',name,flush=True)
    return out

if __name__=='__main__':
    link_world(base,world_args)
    b.linker('shipping',base,build,objs,args,rep)
    hashes={n:b.sha(base/n) for n in ('world','zone')}
    assert hashes=={'world':'eafe45077715d7e91193c1a262227cffe61dcdb96a7cb0d1b8daf8a48b9f3466','zone':'04fcbf33eb30f8be9ff478be4af4d48f816364f222e737e20adf90de5d02cd43'},hashes
    changed_sources()
    b.fresh_pch('shipping',build,objs,vfs,folder)
    units=sorted(p.relative_to(root/'after').as_posix() for p in (root/'after').rglob('*.cpp'))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        objects=dict(zip(units,pool.map(compiled,units)))
    for name,obj in objects.items():
        if name.startswith('zone/'):rep[Path(name).stem]=obj
    def archive(cmd, old, name):
        new=folder/name
        shutil.copyfile(old,new)
        shared=[str(v) for k,v in objects.items() if k.startswith('common/')]
        b.run(['ar','r',str(new),*shared],build,folder/(name+'.log'))
        assert str(old) in cmd
        return [str(new) if x==str(old) else x for x in cmd]
    zone_lib=next(x for x in args if x.endswith('/libcommon.a'))
    args=archive(args,zone_lib,'zone-libcommon.a')
    world_args=archive(world_args,rest/'libcommon.a','world-libcommon.a')
    key='world/CMakeFiles/world.dir/worlddb.cpp.o'
    assert key in world_args
    world_args[world_args.index(key)]=str(objects['world/worlddb.cpp'])
    link_world(folder,world_args)
    b.linker('shipping',folder,build,objs,args,rep)
    for n in hashes:assert 'not found' not in subprocess.check_output(['ldd',str(folder/n)],text=True)
    b.save(root/'build.json',dict(baseline=hashes,binaries={n:b.sha(folder/n) for n in hashes},objects={k:b.sha(v) for k,v in objects.items()}))
    print('Shipping build linked and verified',flush=True)
