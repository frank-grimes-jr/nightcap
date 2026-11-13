"""Isolated current-native reproduction and Inventory protocol compile/link."""
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    p=argparse.ArgumentParser();p.add_argument('--payload',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();payload=args.payload;out=args.output.resolve()
    shipping=Path('/tmp/nightcap-dot-no-initial-20261112-v3')
    full=Path('/tmp/nightcap-quick-buff-full-20261112-v1')
    proof=json.loads((shipping/'native-build.json').read_text());assert proof['status']=='PASS'
    assert proof['binary_sha256']['candidate']=='7b61b5acdf3ba89b5326ac1bf13bb777fe7f02ea00a8cde622a10bc3835e8bf5'
    assert out.parent==Path('/tmp') and not out.exists();out.mkdir()
    for name,pin in proof['source_sha256'].items():assert sha(shipping/'source'/name)==pin,name
    for name,pin in proof['retained_inputs'].items():assert sha(name)==pin,name
    source=out/'source';shutil.copytree(shipping/'source',source,symlinks=True)
    subprocess.run(['patch','--batch','--no-backup-if-mismatch','--fuzz=0','-p3','-i',str((payload/'server.patch').resolve())],cwd=source,check=True)
    (source/'common/inventory_stats_protocol.h').write_bytes((payload/'inventory_stats_protocol.h').read_bytes())
    changed=[p.relative_to(source).as_posix() for p in source.rglob('*') if p.is_file() and
             (p.relative_to(source).as_posix() not in proof['source_sha256'] or sha(p)!=proof['source_sha256'][p.relative_to(source).as_posix()])]
    expected=['common/inventory_stats_protocol.h','zone/client.h','zone/command.cpp','zone/gm_commands/nightcapui.cpp']
    assert sorted(changed)==sorted(expected),changed
    # A nonvirtual function parameter changes no Client members/vtable/inline method.
    old=(shipping/'source/zone/client.h').read_text();new=(source/'zone/client.h').read_text()
    assert new==old.replace('void RefreshEquippedStats();','void RefreshEquippedStats(bool include_inventory = false);')
    build=full/'build/zone';commands=[]
    def compile_unit(flags_path,unit,obj):
        flags={}
        for line in flags_path.read_text().splitlines():
            if line.startswith(('CXX_DEFINES =','CXX_INCLUDES =','CXX_FLAGS =')):
                key,value=line.split(' = ',1);flags[key]=shlex.split(value.replace(str(full/'source'),str(source)))
        command=['/usr/bin/clang++',*flags['CXX_DEFINES'],*flags['CXX_INCLUDES'],*flags['CXX_FLAGS'],
                 '-MD','-MF',str(obj)+'.d','-c',str(unit),'-o',str(obj)]
        commands.append(command);subprocess.run(command,check=True)
    unities=list((build/'CMakeFiles/gm_commands_zone.dir/Unity').glob('*.cxx'))
    units=[p for p in unities if any(name in p.read_text() for name in ('/gm_commands/nightcapui.cpp','/zone/command.cpp'))]
    assert 1<=len(units)<=2,units
    objects=[]
    for original in units:
        unit=out/original.name;unit.write_text(original.read_text().replace(str(full/'source'),str(source)))
        obj=out/(unit.name+'.o');objects.append(obj)
        compile_unit(build/'CMakeFiles/gm_commands_zone.dir/flags.make',unit,obj)
    retained=dict(proof['retained_inputs'])
    # The previous proof's baseline link used its predecessor spell TU. Replace
    # exactly that input with the already-deployed candidate's reviewed object.
    current_spell=shipping/'spell_effects.cpp.o';assert sha(current_spell)==proof['candidate_object_sha256']
    names={}
    for name in retained:names.setdefault(Path(name).name,[]).append(name)
    def unique(name):assert len(names[name])==1,(name,names[name]);return names[name][0]
    gm_old=Path(unique('libgm_commands_zone.a'));gm_new=out/'libgm_commands_zone.a';shutil.copyfile(gm_old,gm_new)
    members=subprocess.check_output(['ar','t',str(gm_old)],text=True).splitlines();assert all(p.name in members for p in objects)
    subprocess.run(['ar','r',str(gm_new),*map(str,objects)],check=True)
    assert subprocess.check_output(['ar','t',str(gm_new)],text=True).splitlines()==members
    link=shlex.split((build/'CMakeFiles/zone.dir/link.txt').read_text())
    for i,token in enumerate(link):
        if token.endswith(('.o','.a')):link[i]=unique(Path(token).name)
    spell_index=link.index(unique('spell_effects.cpp.o'));link[spell_index]=str(current_spell)
    active_inputs={s:sha(s) for s in link if s.endswith(('.o','.a'))}
    outputs={}
    for mode in ('baseline','candidate'):
        invocation=list(link);binary=out/(mode+'-zone');invocation[invocation.index('-o')+1]=str(binary)
        if mode=='candidate':
            invocation[invocation.index(str(gm_old))]=str(gm_new)
        subprocess.run(invocation,cwd=build,check=True)
        subprocess.run(['strip','--strip-debug','-o',str(binary)+'.stripped',str(binary)],check=True)
        outputs[mode]=sha(str(binary)+'.stripped')
        if mode=='baseline':assert outputs[mode]==proof['binary_sha256']['candidate'],outputs
    assert all(sha(name)==pin for name,pin in active_inputs.items())
    result={'status':'PASS','scope':'Current deployed predecessor reproduction and two translation-unit Inventory-only compile/link; Client layout unchanged',
            'baseline_reproduced':True,'source_delta':sorted(changed),'binary_sha256':outputs,
            'shipping_source':str(shipping),'retained_inputs':active_inputs,'compile_commands':commands,
            'new_objects':{str(p):sha(p) for p in [*objects,gm_new]},
            'source_sha256':{p.relative_to(source).as_posix():sha(p) for p in source.rglob('*') if p.is_file()}}
    (out/'native-build.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','baseline_reproduced','source_delta','binary_sha256')}))


if __name__=='__main__':main()
