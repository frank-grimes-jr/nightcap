"""Isolated title build on the exact retained fixed-AA production linker inputs."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import shutil
import tarfile

ROOT=Path('/tmp/nightcap-titles-live-20261114-v1')
PARENT=Path('/tmp/nightcap-fixed-aa-duration-20261114')
ZONE='82d5e2d2573a440beac75dabce41f9271a20d579ebc9d6bf38a32a6ad0c1c314'
spec=importlib.util.spec_from_file_location('fixed_builder',PARENT/'native.py')
fixed=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixed)
b=fixed.builder


def context():
    try:
        source,build,objects,_,replacements,args,_,_=fixed.context('shipping')
    finally:
        b.PINS={'shipping':ZONE}
    old=PARENT/'shipping/candidate';proof=b.load(old/'build.json')
    assert proof['zone']==b.sha(old/'zone')==ZONE
    assert b.sha(old/'link-inputs.json')==proof['link_manifest_sha256']
    for name,pin in b.load(old/'link-inputs.json').items():assert b.sha(build/name)==pin,name
    for name,unit in proof['units'].items():
        obj=old/(name+'.o');assert b.sha(obj)==unit['candidate'];replacements[name]=obj
    return source,build,objects,old/'zone',replacements,args,old/'vfs.json',old/'zone.pch'


def effective(source,vfs,name):
    tree={row['name']:Path(row['external-contents']) for row in b.load(vfs)['roots']}
    return tree.get(str(source/name),source/name)


def command_unit(build):
    units=[p for p in (build/'zone/CMakeFiles/gm_commands_zone.dir/Unity').glob('*.cxx')
           if '/zone/command.cpp"' in p.read_text()]
    assert len(units)==1,units
    unit=units[0];target=str(unit.relative_to(build))+'.o'
    args=b.ninja(build,target)
    return unit,target,args[:args.index('-MD')]


def baseline():
    source,build,objects,previous,replacements,args,vfs,pch=context()
    folder=ROOT/'baseline';folder.mkdir(parents=True)
    names=b.linker('shipping',folder,build,objects,args,replacements)
    assert b.sha(folder/'zone')==ZONE
    report=dict(status='PASS',zone=ZONE,link_inputs={n:b.sha(build/n) for n in names},
                source=str(source),build=str(build),vfs=str(vfs),pch=str(pch))
    for name in ['zone/attack.cpp','zone/client.cpp','zone/command.cpp','zone/command.h','zone/titles.cpp']:
        path=effective(source,vfs,name);target=folder/'source'/name
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(path.read_bytes())
    unit,target,flags=command_unit(build)
    report['command_unit']=dict(source=str(unit),target=target,flags=flags)
    archive=build/'zone/libgm_commands_zone.a'
    member=unit.name+'.o'
    (folder/member).write_bytes(subprocess.check_output(['ar','p',str(archive),member]))
    report['command_archive']=dict(path=str(archive),sha256=b.sha(archive),member=member,
        member_sha256=b.sha(folder/member))
    b.save(folder/'build.json',report)
    print(json.dumps({k:report[k] for k in ['status','zone','source','command_unit','command_archive']},indent=2),flush=True)


def equal_object(original,rebuilt,folder,label):
    if b.sha(original)==b.sha(rebuilt):return 'exact'
    paths=[]
    for suffix,path in [('old',original),('rebuilt',rebuilt)]:
        target=folder/(label+'-'+suffix+'-no-debug.o')
        b.run(['objcopy','--strip-debug',str(path),str(target)],folder,folder/(label+'-'+suffix+'-strip.log'))
        paths.append(target)
    assert b.sha(paths[0])==b.sha(paths[1]),'Unmodified object code/relocations changed: '+label
    return 'identical after removing debug information'


def candidate():
    source,build,objects,previous,replacements,args,old_vfs,pch=context()
    base=b.load(ROOT/'baseline/build.json');assert base['zone']==b.sha(ROOT/'baseline/zone')==ZONE
    folder=ROOT/'candidate';folder.mkdir()
    wanted=b.load(ROOT/'source-delta.json')
    assert len(wanted)==9
    with tarfile.open(ROOT/'source.tar') as archive:
        members=archive.getmembers();assert {m.name for m in members}==set(wanted)
        for m in members:
            assert m.isfile() and '..' not in Path(m.name).parts
            data=archive.extractfile(m).read();assert hashlib.sha256(data).hexdigest()==wanted[m.name]
            path=folder/'source'/m.name;path.parent.mkdir(exist_ok=True,parents=True);path.write_bytes(data)
    tree={row['name']:Path(row['external-contents']) for row in b.load(old_vfs)['roots']}
    for name in wanted:tree[str(source/name)]=folder/'source'/name
    overlay=folder/'vfs.json'
    # Retain the LLVM overlay writer's version-first compact representation.
    overlay.write_text(json.dumps({'version':0,'use-external-names':False,'roots':[
        {'type':'file','name':name,'external-contents':str(path)} for name,path in tree.items()]}))
    new_pch=b.fresh_pch('shipping',build,objects,overlay,folder)
    report=dict(status='PASS',profile='shipping',baseline=ZONE,source_sha256=wanted,
                feature_patch_sha256=b.sha(ROOT/'feature.patch'),units={})
    for name in ['attack','client','titles']:
        print('Compiling native title unit: '+name,flush=True)
        old=replacements.get(name,build/objects/(name+'.cpp.o'))
        check=folder/('baseline-'+name+'.o')
        b.compile_unit('shipping',name,build,source,objects,pch,old_vfs,check)
        comparison=equal_object(old,check,folder,name)
        obj=folder/(name+'.o')
        b.compile_unit('shipping',name,build,source,objects,new_pch,overlay,obj)
        replacements[name]=obj
        report['units'][name]=dict(predecessor=b.sha(old),recompiled_predecessor=b.sha(check),
            source_reproduction=comparison,candidate=b.sha(obj))
    unit,target,flags=command_unit(build)
    old_archive=build/'zone/libgm_commands_zone.a';member=unit.name+'.o'
    prior=ROOT/'baseline'/member
    old_obj=folder/('baseline-'+member)
    b.run([*flags,'-o',str(old_obj),'-c',str(unit)],build,folder/'command-baseline.log')
    assert b.sha(old_obj)==b.sha(prior),'Unmodified command archive unit did not reproduce'
    obj=folder/member
    b.run([*flags,'-ivfsoverlay',str(overlay),'-o',str(obj),'-c',str(unit)],build,folder/'command-candidate.log')
    archive=folder/'libgm_commands_zone.a';shutil.copyfile(old_archive,archive)
    members=subprocess.check_output(['ar','t',str(old_archive)],text=True).splitlines()
    b.run(['ar','r',str(archive),str(obj)],build,folder/'archive.log')
    assert subprocess.check_output(['ar','t',str(archive)],text=True).splitlines()==members
    for m in members:
        if m!=member:
            assert subprocess.check_output(['ar','p',str(archive),m])==subprocess.check_output(['ar','p',str(old_archive),m]),m
    report['command_archive']=dict(member=member,member_before=b.sha(prior),member_after=b.sha(obj),
        archive_before=b.sha(old_archive),archive_after=b.sha(archive),other_members_preserved=len(members)-1)
    args=list(args);token=next(a for a in args if str(a).endswith('/libgm_commands_zone.a'))
    args[args.index(token)]=str(archive)
    names=b.linker('shipping',folder,build,objects,args,replacements)
    report['zone']=b.sha(folder/'zone');assert report['zone']!=ZONE
    binary=(folder/'zone').read_bytes()
    assert b'nightcap_title_settings' in binary and b'Title earned: %s.' in binary
    assert 'not found' not in subprocess.check_output(['ldd',str(folder/'zone')],text=True)
    for name,pin in base['link_inputs'].items():assert b.sha(build/name)==pin,name
    b.save(folder/'link-inputs.json',{name:b.sha(build/name) for name in names})
    report.update(link_input_count=len(names),link_manifest_sha256=b.sha(folder/'link-inputs.json'))
    b.save(folder/'build.json',report)
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['baseline','candidate'])
    args=parser.parse_args();baseline() if args.phase=='baseline' else candidate()
