"""Rebuild the preview and a private read-only AA probe against the retained MSVC Release inputs."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import zipfile

import capture

WS = Path('E:/EQ_Local_Dev')
ORIGINAL = WS/'artifacts/nightcap-hailstone-20261122'
FIXTURE = WS/'artifacts/cairnwright-creation-20261121'
BUILD = FIXTURE/'hs-build'
SRC = FIXTURE/'hailstone-client'
OUT = WS/'artifacts/classic-qa-20261127/hailstone'
VERIFIED = 'c34ee76c4cb2a61ce839f02d5ae739e6445c15556ed6576654a955289578ae50'


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def tlog(name, tool):
    return (BUILD/(name+'.dir')/'Release'/(name+'.tlog')/(tool+'.command.1.tlog')).read_text(encoding='utf-16').splitlines()


def tools():
    output=subprocess.check_output(['cmd','/d','/c',r'C:\BuildTools\VC\Auxiliary\Build\vcvars64.bat && set'],text=True)
    return dict(os.environ,**dict(line.split('=',1) for line in output.splitlines() if '=' in line and not line.startswith('=')))


def execute(tool, args, stem, env):
    rsp=OUT/(stem+'.rsp')
    rsp.write_text(args,encoding='utf-16')
    print(tool,stem,flush=True)
    subprocess.run([shutil.which(tool,path=env['Path']), '@'+str(rsp)],cwd=BUILD,env=env,check=True)


def compile_file(project, old, new, env):
    log=tlog(project,'CL')
    entry=str(old).upper()
    i=log.index('^'+entry)
    flags=log[i+1].replace(entry,'"'+str(new)+'"')
    obj=OUT/(new.stem+'.obj')
    flags,n=re.subn(r'(?i)/Fo"[^"\n]+"',lambda _: '/Fo"'+str(obj)+'"',flags)
    assert n==1
    flags=re.sub(r'(?i)/Fd"[^"\n]+"',lambda _: '/Fd"'+str(OUT/(new.stem+'.pdb'))+'"',flags)
    execute('cl.exe',f'/I"{old.parent}" '+flags,new.stem,env)
    return obj


def link(project, extras, old_obj, name, env):
    flags='\n'.join(tlog(project,'link')[1:])
    for opt,suffix in [('OUT','exe'),('PDB','pdb'),('IMPLIB','lib')]:
        flags,n=re.subn(r'(?i)/'+opt+r':"[^"\n]+"',lambda _: f'/{opt}:"{OUT/(name+"."+suffix)}"',flags)
        assert n==1
    if old_obj:
        assert flags.count(old_obj)==1
        flags=flags.replace(old_obj,'')
    execute('link.exe','\n'.join(['"'+str(o)+'"' for o in extras])+ '\n'+flags,name,env)
    return OUT/(name+'.exe')


def text_section(path):
    data=path.read_bytes()
    pe=struct.unpack_from('<I',data,0x3c)[0]
    count=struct.unpack_from('<H',data,pe+6)[0]
    table=pe+24+struct.unpack_from('<H',data,pe+20)[0]
    for index in range(count):
        section=table+index*40
        if data[section:section+8].rstrip(b'\0')==b'.text':
            size, offset=struct.unpack_from('<II',data,section+16)
            return data[offset:offset+size]
    raise ValueError('PE text section missing')


def replace_zip(original, result, replacements):
    with zipfile.ZipFile(original) as before, zipfile.ZipFile(result,'w') as after:
        seen=set()
        for info in before.infolist():
            old=before.read(info)
            new=replacements.get(info.filename,old)
            if info.filename in replacements:
                assert new!=old
                seen.add(info.filename)
            after.writestr(info,new)
        assert seen==replacements.keys()
    with zipfile.ZipFile(result) as check:
        assert check.testzip() is None


DIAGNOSTIC = r'''
            static bool reported_recall = false;
            if (!reported_recall && Clock::now() - in_zone_at > std::chrono::seconds(4) && conn.profile()) {
                reported_recall = true;
                const auto& state = conn.alt_adv();
                const auto* rank = state.get(22200);
                auto rows = conn.aa_list(1, game::AAFilter{});
                const bool visible = rank && std::find(rows.begin(), rows.end(), rank) != rows.end();
                std::printf("NIGHTCAP_RECALL class=%u catalog=%d owned=%d general=%d family=%d spell=%d title=%s hotkey_string=%s preview_label=%s\n",
                    unsigned(conn.profile()->class_), rank != nullptr, state.has(22200), visible,
                    rank ? rank->group : 0, rank ? rank->spell : 0,
                    rank ? conn.aa_display_name(*rank).c_str() : "",
                    rank ? conn.strings().db_string(unsigned(rank->hotkey_sid), 2).c_str() : "",
                    rank ? conn.aa_display_name(*rank).substr(0,63).c_str() : "");
            }
'''


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    env=tools()
    original_source=ORIGINAL/'nightcap-hailstone-source.zip'
    assert sha(original_source.read_bytes())==VERIFIED
    original_binary=ORIGINAL/'nightcap-hailstone.zip'
    with zipfile.ZipFile(original_binary) as z:
        original=(BUILD/'hailstone/hailstone.exe')
        assert original.read_bytes()==z.read('hailstone.exe')
    baseline=link('hailstone',[],None,'before',env)
    assert text_section(original)==text_section(baseline), 'Retained link inputs do not reproduce shipped code'
    patch=(capture.HERE.parents[2]/'qa/cairnwright-hailstone/nightcap-preview.patch').read_bytes()
    cut=patch.index(b'diff --git a/src/game/alt_adv.cpp ')
    replacements={}
    with zipfile.ZipFile(original_source) as z:
        for name in ('src/game/alt_adv.cpp','src/game/alt_adv.h'):
            f=OUT/name
            f.parent.mkdir(parents=True,exist_ok=True)
            original=z.read('hailstone/'+name)
            assert original.splitlines()==(SRC/name).read_bytes().splitlines()
            f.write_bytes(original)
    isolated_env=dict(os.environ,GIT_CEILING_DIRECTORIES=str(OUT.parent))
    subprocess.run(['git','apply','--no-index','--whitespace=nowarn','-'],cwd=OUT,env=isolated_env,input=patch[cut:],check=True)
    for n in ('src/game/alt_adv.cpp','src/game/alt_adv.h'):
        replacements['hailstone/'+n]=(OUT/n).read_bytes()
    changed=compile_file('hailstone_engine',SRC/'src/game/alt_adv.cpp',OUT/'src/game/alt_adv.cpp',env)
    assert b'cls > 17' in replacements['hailstone/src/game/alt_adv.cpp']
    fixture_source=OUT/'preview_regression.cpp'
    fixture_source.write_text(r'''#include "game/alt_adv.h"
int main() {
    using namespace hailstone::game;
    AltAbility ability;
    ability.classes = 1u << 17;
    if (!ability.class_allowed(17) || ability.class_allowed(16) || ability.class_allowed(0) || ability.class_allowed(18))
        return 1;
    ability.classes = 1u << 16;
    if (!ability.class_allowed(16) || ability.class_allowed(17))
        return 2;
    AltAdvState state;
    ability.refresh = 1;
    ability.timers = {3};
    const int now = 1800000000;
    state.set_timer(3, 0, now - 7, now);
    if (!state.readiness(ability, 0, now).ready) return 3;
    ability.refresh = 60;
    state.set_timer(3, now - 17, now - 7, now);
    const auto active = state.readiness(ability, 0, now);
    return active.ready || active.remaining != 50 || !state.readiness(ability, 0, now+50).ready;
}
''')
    test_obj=compile_file('playprobe',SRC/'tools/playprobe.cpp',fixture_source,env)
    test_exe=link('playprobe',[changed,test_obj],r'PLAYPROBE.DIR\RELEASE\PLAYPROBE.OBJ','preview_regression',env)
    subprocess.run([str(test_exe)],cwd=OUT,check=True)
    binary=link('hailstone',[changed],None,'hailstone',env)
    prior=SRC/'tools/playprobe.cpp'
    marker=b'            quest.step(conn);'
    data=prior.read_bytes()
    assert data.count(marker)==1
    private_source=OUT/'recall_probe.cpp'
    private_source.write_bytes(data.replace(marker,DIAGNOSTIC.encode()+marker))
    probe=compile_file('playprobe',prior,private_source,env)
    link('playprobe',[changed,probe],r'PLAYPROBE.DIR\RELEASE\PLAYPROBE.OBJ','recall_probe',env)
    for dll in ('SDL3.dll','zlib1.dll'):
        shutil.copyfile(BUILD/'Release'/dll,OUT/dll)
    replace_zip(original_binary,OUT/original_binary.name,{'hailstone.exe':binary.read_bytes()})
    replace_zip(original_source,OUT/original_source.name,replacements)
    result={n:sha((OUT/n).read_bytes()) for n in ('hailstone.exe','recall_probe.exe',original_binary.name,original_source.name)}
    result.update(predecessor_text=sha(text_section(baseline)),predecessor_source=VERIFIED,source_changes=list(replacements))
    (OUT/'build.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    main()

