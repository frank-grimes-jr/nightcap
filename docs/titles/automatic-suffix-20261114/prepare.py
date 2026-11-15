"""Inject only reviewed title hooks into the effective shipping source."""
import difflib
import hashlib
import json
from pathlib import Path
import tarfile

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ART=ROOT/'artifacts/titles-live-20261114/automatic/shipping-v2'


def once(text,old,new):
    assert text.count(old)==1,old
    return text.replace(old,new,1)


def main():
    base=ART/'baseline-source';source=ART/'source';source.mkdir(exist_ok=True)
    assert not any(source.iterdir()),'Existing source candidate: inspect rather than overwrite'
    output={}
    for name in ['client_packet.cpp','client_process.cpp','exp.cpp','dungeon_service.cpp','task_manager.cpp','task_client_state.cpp','highkeep_rescue.inc']:
        key='zone/'+name;output[key]=(base/key).read_text(encoding='utf8')
    for key in output:
        if key.endswith('.cpp'):
            assert '#include "zone/earned_titles.h"' not in output[key]
            output[key]='#include "zone/earned_titles.h"\n'+output[key]
    key='zone/client_packet.cpp';s=output[key]
    start=s.index('void Client::CompleteConnect()');end=s.index('// connecting opcode handlers',start)
    block=s[start:end];pos=block.rindex('\n}')
    output[key]=s[:start]+block[:pos]+'\n\tNightcapTitles::RequestCheck(this);'+block[pos:]+s[end:]
    key='zone/client_process.cpp';output[key]=once(output[key],
        '\tif (!m_multiclass_state_valid || !m_pet_armor_transfer_valid || !m_pet_state_valid) { OnDisconnect(true); return false; }\n\tbool ret = true;',
        '\tif (!m_multiclass_state_valid || !m_pet_armor_transfer_valid || !m_pet_state_valid) { OnDisconnect(true); return false; }\n\tNightcapTitles::Pulse(this);\n\tbool ret = true;')
    key='zone/exp.cpp';s=output[key];start=s.index('void Client::SetLevel(');end=s.index('uint32 Client::GetEXPForLevel',start)
    block=s[start:end];at=block.rindex('\tSave();')+len('\tSave();')
    output[key]=s[:start]+block[:at]+'\n\tNightcapTitles::RequestCheck(this);'+block[at:]+s[end:]
    key='zone/dungeon_service.cpp';s=output[key];start=s.index('bool BeforeDeath(')
    at=s.index('\t\ttx.Commit();',start)+len('\t\ttx.Commit();')
    output[key]=s[:at]+'\n\t\tfor (auto c : completed) { NightcapTitles::RequestCheck(c); }'+s[at:]
    key='zone/highkeep_rescue.inc';output[key]=once(output[key],
        '\ttx.Commit(); state.rescued=true;',
        '\ttx.Commit(); state.rescued=true;\n\tfor (auto c : completed) { NightcapTitles::RequestCheck(c); }')
    key='zone/task_manager.cpp';output[key]=once(output[key],
        "\t\t// If the Rule to record non-optional task completion is not enabled, don't save it",
        "\t\tif (task_id==9515) { NightcapTitles::RequestCheck(client); }\n\t\t// If the Rule to record non-optional task completion is not enabled, don't save it")
    key='zone/task_client_state.cpp';s=output[key];start=s.index('bool ClientTaskState::RecordCompletedTaskFromLedger(')
    at=s.index('\tif (!saved.Success()) { return false; }',start)+len('\tif (!saved.Success()) { return false; }')
    output[key]=s[:at]+'\n\tif (task_id==9515) { NightcapTitles::RequestCheck(client); }'+s[at:]
    for name in ['zone/earned_titles.h','zone/earned_titles.inc']:
        output[name]=(ROOT/'server-mods/code'/name).read_text(encoding='utf8')
    patch='';pins={}
    for name,text in output.items():
        old=(base/name).read_text(encoding='utf8')
        patch+=''.join(difflib.unified_diff(old.splitlines(True),text.splitlines(True),fromfile='a/'+name,tofile='b/'+name,n=3))
        path=source/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf8',newline='\n')
        pins[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    (HERE/'feature.patch').write_text(patch,encoding='utf8',newline='\n')
    (HERE/'source-delta.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf8')
    with tarfile.open(ART/'source.tar','w') as archive:
        for name in pins:archive.add(source/name,arcname=name)
    print('Prepared nine source files; shipping hooks preserve all unrelated effective source')


if __name__=='__main__':main()
