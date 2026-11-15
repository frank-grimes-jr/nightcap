"""Title-only follow-up on the reproduced post-combat rest shipping inputs."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tarfile

ROOT=Path('/tmp/nightcap-titles-automatic-20261114-v2')
PARENT=Path('/tmp/nightcap-titles-live-20261114-v1')
REST=Path('/tmp/nightcap-rest-test-20261114/shipping')
FIRST=Path('/tmp/nightcap-titles-automatic-20261114-v1')
TITLE_BASE='f35b4e3db6dd87f2eb5e62a916543508988df87c53ae9355ee2f4fae53fe2602'
BASE='d9ab889ad7f9c40a7e3066810b201f802f211c2c2d870637d4d775e6f691ca0b'
spec=importlib.util.spec_from_file_location('title_predecessor',PARENT/'native.py')
prior=importlib.util.module_from_spec(spec);spec.loader.exec_module(prior)
b=prior.b
UNITS=['titles','client_packet','client_process','exp','dungeon_service','task_manager','task_client_state']
FILES=['zone/earned_titles.h','zone/earned_titles.inc','zone/client_packet.cpp','zone/client_process.cpp','zone/exp.cpp',
       'zone/dungeon_service.cpp','zone/highkeep_rescue.inc','zone/task_manager.cpp','zone/task_client_state.cpp']


def context():
    source,build,objects,_,replacements,args,_,_=prior.context()
    old=PARENT/'candidate';proof=b.load(old/'build.json')
    assert proof['zone']==b.sha(old/'zone')==TITLE_BASE
    for name,unit in proof['units'].items():
        obj=old/(name+'.o');assert b.sha(obj)==unit['candidate'];replacements[name]=obj
    archive=old/'libgm_commands_zone.a'
    assert b.sha(archive)==proof['command_archive']['archive_after']
    args=list(args);token=next(a for a in args if str(a).endswith('/libgm_commands_zone.a'))
    args[args.index(token)]=str(archive)
    for name,pin in b.load(old/'link-inputs.json').items():assert b.sha(build/name)==pin,name
    rest=b.load(REST/'build.json')
    assert rest['baseline']['zone']==TITLE_BASE and rest['binaries']['zone']==b.sha(REST/'zone')==BASE
    assert rest['binaries']['world']==b.sha(REST/'world')=='eafe45077715d7e91193c1a262227cffe61dcdb96a7cb0d1b8daf8a48b9f3466'
    for name in ['client','client_mods']:replacements[name]=REST/(name+'.o')
    assert 'bin/libcommon.a' in args
    args=[str(REST/'libcommon.a') if a=='bin/libcommon.a' else a for a in args]
    return source,build,objects,replacements,args,REST/'vfs.json',REST/'zone.pch',archive


def baseline():
    source,build,objects,replacements,args,vfs,pch,archive=context()
    folder=ROOT/'baseline';folder.mkdir(parents=True)
    inputs=b.linker('shipping',folder,build,objects,args,replacements)
    assert b.sha(folder/'zone')==BASE
    pins={}
    for name in FILES:
        original=prior.effective(source,vfs,name);pins[name]=b.sha(original)
        target=folder/'source'/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(original.read_bytes())
    b.save(folder/'build.json',dict(status='PASS',zone=BASE,source_sha256=pins,
        link_inputs={n:b.sha(build/n) for n in inputs},command_archive_sha256=b.sha(archive)))
    print('PASS: current shipping baseline reproduced; nine effective files exported',flush=True)


def candidate():
    source,build,objects,replacements,args,old_vfs,pch,archive=context()
    baseline=b.load(ROOT/'baseline/build.json')
    assert baseline['zone']==b.sha(ROOT/'baseline/zone')==BASE
    folder=ROOT/'candidate';folder.mkdir()
    wanted=b.load(ROOT/'source-delta.json');assert set(wanted)==set(FILES)
    with tarfile.open(ROOT/'source.tar') as bundle:
        assert set(m.name for m in bundle.getmembers())==set(FILES)
        for m in bundle.getmembers():
            assert m.isfile();data=bundle.extractfile(m).read();assert hashlib.sha256(data).hexdigest()==wanted[m.name]
            path=folder/'source'/m.name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    tree={r['name']:Path(r['external-contents']) for r in b.load(old_vfs)['roots']}
    for name in wanted:tree[str(source/name)]=folder/'source'/name
    overlay=folder/'vfs.json'
    overlay.write_text(json.dumps({'version':0,'use-external-names':False,'roots':[
        {'type':'file','name':n,'external-contents':str(p)} for n,p in tree.items()]}))
    new_pch=b.fresh_pch('shipping',build,objects,overlay,folder)
    report=dict(status='PASS',profile='shipping',baseline=BASE,source_sha256=wanted,
        feature_patch_sha256=b.sha(ROOT/'feature.patch'),units={},command_archive_preserved=b.sha(archive))
    for name in UNITS:
        print('Compiling shipping unit: '+name,flush=True)
        old=replacements.get(name,build/objects/(name+'.cpp.o'))
        # Rest replaced client/client_mods and the common rule library only.
        # These seven incumbent objects and all nine effective source files are
        # unchanged, so retain their already completed exact recompile proof.
        first=b.load(FIRST/'candidate/build.json');first_base=b.load(FIRST/'baseline/build.json')
        assert baseline['source_sha256']==first_base['source_sha256']
        check=FIRST/'candidate'/('baseline-'+name+'.o')
        assert b.sha(old)==b.sha(check)==first['units'][name]['predecessor']==first['units'][name]['recompiled_predecessor']
        match='exact'
        obj=folder/(name+'.o')
        b.compile_unit('shipping',name,build,source,objects,new_pch,overlay,obj)
        replacements[name]=obj
        report['units'][name]=dict(predecessor=b.sha(old),recompiled_predecessor=b.sha(check),source_reproduction=match,
            recompile_evidence=b.sha(FIRST/'candidate/build.json'),candidate=b.sha(obj))
    inputs=b.linker('shipping',folder,build,objects,args,replacements)
    report['zone']=b.sha(folder/'zone');assert report['zone']!=BASE
    assert 'not found' not in subprocess.check_output(['ldd',str(folder/'zone')],text=True)
    for name,pin in baseline['link_inputs'].items():assert b.sha(build/name)==pin,name
    assert b.sha(archive)==baseline['command_archive_sha256']
    b.save(folder/'link-inputs.json',{n:b.sha(build/n) for n in inputs})
    report.update(link_input_count=len(inputs),link_manifest_sha256=b.sha(folder/'link-inputs.json'))
    b.save(folder/'build.json',report)
    print(json.dumps(report),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('phase',choices=['baseline','candidate']);a=p.parse_args()
    baseline() if a.phase=='baseline' else candidate()
