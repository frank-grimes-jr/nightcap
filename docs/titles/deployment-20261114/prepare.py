"""Create exact title-only hunks over the authenticated production source snapshot."""
import difflib
import hashlib
import json
from pathlib import Path
import tarfile

ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
ART=ROOT/'artifacts/titles-live-20261114'


def replace_once(text,old,new):
    assert text.count(old)==1,old
    return text.replace(old,new,1)


def prepare():
    source=ART/'source';source.mkdir(exist_ok=False)
    base=ART/'baseline-source'
    output={}
    for name in ['attack.cpp','client.cpp','command.cpp','command.h','titles.cpp']:
        output['zone/'+name]=(base/'zone'/name).read_text(encoding='utf-8')
    s=output['zone/attack.cpp']
    s='#include "zone/earned_titles.h"\n'+s
    start=s.index('bool NPC::Death(')
    at=s.index('\tm_combat_record.Stop();',start)+len('\tm_combat_record.Stop();')
    s=s[:at]+'\n\tNightcapTitles::RecordKill(this, give_exp_client, hunt_owned || is_merchant || is_ldon_treasure || IsQueuedForCorpse() || NightcapAshen::Transient(GetNPCTypeID()));'+s[at:]
    assert 'const bool hunt_owned =' in s and 'bool is_merchant' in s
    output['zone/attack.cpp']=s
    s='#include "zone/earned_titles.h"\n'+output['zone/client.cpp']
    s=replace_once(s,'\tdatabase.SaveCharacterSkill(CharacterID(), skillid, value);',
        '\tconst bool skill_saved = database.SaveCharacterSkill(CharacterID(), skillid, value);')
    start=s.index('void Client::SetSkill(');at=s.index('\n}',start)
    s=s[:at]+'\n\tif (skill_saved) { NightcapTitles::CheckSkill(this, static_cast<unsigned>(skillid)); }'+s[at:]
    output['zone/client.cpp']=s
    s='#include "zone/earned_titles.h"\n'+output['zone/command.cpp']
    s=replace_once(s,'\t\tcommand_add("itemxp",',
        '\t\tcommand_add("titles", "[page] - View earned titles and their requirements.", AccountStatus::Player, command_titles) ||\n\t\tcommand_add("itemxp",')
    tracked=(ROOT/'server-mods/code/zone/command.cpp').read_text(encoding='utf-8')
    definition=tracked[tracked.index('void command_titles(Client *c, const Seperator *sep)'):]
    assert definition.count('void command_titles(')==1
    s+='\n'+definition
    output['zone/command.cpp']=s
    if 'void command_titles(' not in output['zone/command.h']:
        output['zone/command.h']+='\nvoid command_titles(Client *c, const Seperator *sep);\n'
    s=output['zone/titles.cpp']
    s=replace_once(s,'#include "titles.h"','#include "titles.h"\n#include "zone/earned_titles.h"')
    s=replace_once(s,'extern WorldServer worldserver;','extern WorldServer worldserver;\n\n#include "earned_titles.inc"')
    s=replace_once(s,'return e != titles.end() ? e->prefix : "";', 'return e != titles.end() ? e->prefix : NightcapTitles::Name(title_id, false);')
    s=replace_once(s,'return e != titles.end() ? e->suffix : "";', 'return e != titles.end() ? e->suffix : NightcapTitles::Name(title_id, true);')
    s=replace_once(s,'\treturn eligible_titles;\n}', '\tNightcapTitles::AppendEligible(c, titles, eligible_titles);\n\treturn eligible_titles;\n}')
    output['zone/titles.cpp']=s
    for name in ['common/earned_title_policy.h','common/earned_title_catalog.h','zone/earned_titles.h','zone/earned_titles.inc']:
        output[name]=(ROOT/'server-mods/code'/name).read_text(encoding='utf-8')
    patch='';pins={}
    for name,text in output.items():
        previous=(base/name).read_text(encoding='utf-8') if (base/name).exists() else ''
        patch+=''.join(difflib.unified_diff(previous.splitlines(True),text.splitlines(True),
            fromfile='a/server-mods/code/'+name,tofile='b/server-mods/code/'+name,n=3))
        path=source/name;path.parent.mkdir(exist_ok=True,parents=True);path.write_text(text,encoding='utf-8',newline='\n')
        pins[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    (HERE/'feature.patch').write_text(patch,encoding='utf-8',newline='\n')
    (HERE/'source-delta.json').write_text(json.dumps(pins,indent=2)+'\n',encoding='utf-8')
    with tarfile.open(ART/'source.tar','w') as archive:
        for name in pins:archive.add(source/name,arcname=name)
    print('Prepared9reviewed title source files over authenticated current native baseline')


if __name__=='__main__':prepare()
