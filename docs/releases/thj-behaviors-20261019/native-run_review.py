"""Independent extracted-native controls. Does not edit or load a live server.

The retirement method and resource guard/debit/effect blocks are taken verbatim
from the candidate. Persistence, target delivery, and timer storage are fixtures;
this proves their call boundary, not a database transaction or full zone runtime.
"""
from pathlib import Path
import datetime
import gzip
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = Path('E:/EQ_Local_Dev/artifacts/thj-behaviors-20261019/native-final-review')
OUT.mkdir(parents=True,exist_ok=True)
FILES = ['server-mods/code/zone/aa.cpp', 'server-mods/code/zone/spells.cpp',
         'server-mods/code/zone/spell_effects.cpp', 'server-mods/code/common/nightcap_thj_behaviors.h',
         'tools/fixtures/thj-behaviors-20261019.json.gz']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def block(source, signature):
    start = source.index(signature)
    brace = source.index('{', start)
    depth, end = 1, brace + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]


hashes = {path: sha(ROOT / path) for path in FILES}
aa = (ROOT / FILES[0]).read_text(encoding='utf-8')
spells = (ROOT / FILES[1]).read_text(encoding='utf-8')
effects = (ROOT / FILES[2]).read_text(encoding='utf-8')
retire = block(aa, 'bool Client::RetireTHJAbilities()')
finished = block(spells, 'bool Mob::SpellFinished(')
guard = finished[finished.index('const bool thj_resource'):finished.index('// Instant AAs, item effects')]
debit = block(finished, 'if (thj_resource) {\n\t\t// One debit')
failure = block(finished, 'else if(!SpellOnTarget(spell_id, spell_target, 0, true, resist_adjust, false, level_override))')
valor = block(effects, 'if (RuleB(Spells, NightcapTHJBehaviors) && spell_id == 2775 && caster && caster->IsClient())')
burn = block(effects, 'if (RuleB(Spells, NightcapTHJBehaviors) && caster && caster->IsClient() && NightcapTHJ::ManaBurn(spell_id))')
assert finished.index('const bool thj_resource') < finished.index('switch(CastAction)') < finished.index(debit) < finished.index('Set Recast Timer on spells.')
fixture = json.loads(gzip.decompress((ROOT / FILES[4]).read_bytes()))['tables']
abilities = {a['id']: a for a in fixture['aa_ability']}
ranks = {r['id']: r for r in fixture['aa_ranks']}
retired = (25, 252, 8300, 3521, 3522, 758)
catalog, setup = [], []
for aid in retired:
    a = abilities[aid]
    rid, costs = a['first_rank_id'], []
    while rid in ranks:
        r = ranks[rid]
        costs.append(r['cost'])
        rid = r['next_id']
    catalog.append(dict(ability=aid, first_rank=a['first_rank_id'], enabled=a['enabled'],
                        earned_count=len(costs), total_cost=sum(costs), charges=a['charges'], grant_only=a['grant_only']))
    setup.append('add(%d,%d,%d,%d,%d,%d,%d);' % (aid,a['first_rank_id'],len(costs),sum(costs),a['enabled'],a['charges'],a['grant_only']))

cpp = r'''
#include <cstdint>
#include <map>
#include <set>
#include <string>
#include <vector>
#include <iostream>
#include <stdexcept>
using uint16=uint16_t; using uint32=uint32_t; using uint64=uint64_t;
using int32=int32_t; using int64=int64_t;
bool enabled=true;
#define RuleB(category, name) enabled
int checks=0;
void check(bool ok,const char* message){++checks;if(!ok)throw std::runtime_error(message);}
struct Rank{uint32 current_value;int64 total_cost;};
struct Ability{
 uint32 id,first_rank_id; int enabled,charges,grant_only; Rank rank;
 Rank* GetRankByPointsSpent(uint32 value){return value==rank.current_value?&rank:nullptr;}
};
struct Zone{
 std::map<uint32,Ability> abilities;
 Ability* GetAlternateAdvancementAbilityByRank(uint32 key){
  auto it=abilities.find(key);return it==abilities.end()?nullptr:&it->second;
 }
} zone_state;
Zone* zone=&zone_state;
void add(uint32 aid,uint32 first,uint32 count,int64 cost,int active,int charges,int grant){
 zone->abilities.emplace(first,Ability{aid,first,active,charges,grant,{count,cost}});
}
using State=std::map<uint32,std::pair<uint32,uint32>>;
struct Client{
 State m_earned_aa_ranks,aa_ranks; uint32 wallet=17,spent=0;
 struct{uint32 expended_aa=9;}m_epp;
 bool valid=true,persist_ok=true;int persist_calls=0;
 bool HasValidEarnedAAState(){return valid;}
 void InvalidateEarnedAAState(){valid=false;}
 uint32 GetAAPoints(){return wallet;}
 bool PersistEarnedAAState(State earned,State usable,uint32 next,uint32 expended){
  ++persist_calls;
  if(!persist_ok){InvalidateEarnedAAState();return false;}
  uint64 sum=expended;
  for(const auto& e:earned)sum+=zone->GetAlternateAdvancementAbilityByRank(e.first)->rank.total_cost;
  m_earned_aa_ranks=std::move(earned);aa_ranks=std::move(usable);wallet=next;spent=static_cast<uint32>(sum);
  return true;
 }
 bool RetireTHJAbilities();
};
Client owned(){
 Client c;
 for(auto& e:zone->abilities){c.m_earned_aa_ranks[e.first]={e.second.rank.current_value,0};
  if(e.second.enabled)c.aa_ranks[e.second.id]={e.second.rank.current_value,0};}
 return c;
}
enum class CastingSlot{AltAbility,Item,PotionBelt};
namespace Chat{constexpr int SpellFailure=1;}
constexpr int focusFcHealPctIncoming=1,focusFcHealPctCritIncoming=2,focusFcHealAmtIncoming=3;
struct Mob{
 bool client=true,reject_effect=false;int64 maximum=10001,mana=10001,healed=0,damaged=0;
 int debit_calls=0,triggers=0,timer_commits=0,delivered=0,messages=0;
 int incoming_pct=0,incoming_crit_pct=0,incoming_flat=0,heal_rate=0,focus_calls=0;
 int GetFocusEffect(int type,uint16,Mob*){++focus_calls;return type==1?incoming_pct:type==2?incoming_crit_pct:incoming_flat;}
 int GetHealRate(){return heal_rate;}
 std::set<uint16> buffs;
 bool IsClient(){return client;}
 int64 GetMaxMana(){return maximum;}
 int64 GetMana(){return mana;}
 void SetMana(int64 value){mana=value;++debit_calls;}
 void TryTriggerOnCastRequirement(){++triggers;}
 void Message(int,const char*){++messages;}
 bool FindBuff(uint16 id){return buffs.count(id)!=0;}
 bool IsBuffSpell(uint16){return true;}
 bool IsBeneficialSpell(uint16 id){return id==2775;}
 uint16 healed_spell=0;
 void HealDamage(uint64 value,Mob*,uint16 spell){healed+=value;healed_spell=spell;}
 void Damage(Mob*,int64 value,uint16,int,bool,int,bool){damaged+=value;}
 void ApplyResourceEffect(uint16 spell_id,Mob* caster);
 bool SpellOnTarget(uint16 id,Mob* target,int,bool,int,bool,int){
  if(reject_effect)return false;
  ++delivered;target->ApplyResourceEffect(id,this);return true;
 }
 bool Complete(uint16 spell_id,Mob* spell_target,std::vector<Mob*> group={},
               CastingSlot slot=CastingSlot::AltAbility,bool isproc=false);
};
'''
cpp += '#include "' + (ROOT / FILES[3]).as_posix() + '"\n' + retire + '\n'
cpp += 'void Mob::ApplyResourceEffect(uint16 spell_id,Mob* caster){\nint buffslot=0;struct{int skill=0;}spell;\ndo{\n'+valor+'\n'+burn+'\n}while(false);\n}\n'
cpp += 'bool Mob::Complete(uint16 spell_id,Mob* spell_target,std::vector<Mob*> group,CastingSlot slot,bool isproc){\n'+guard
cpp += '\nint resist_adjust=0,level_override=0;\nif(spell_id==2775){for(auto* target:group)SpellOnTarget(spell_id,target,0,true,0,false,0);}\n'
cpp += failure+'\n'+debit+'\n++timer_commits;return true;\n}\n'
cpp += 'int main(){try{\n'+''.join(setup)+'\nadd(999999,65000,3,31,1,0,0);\n'
cpp += r'''
 uint64 expected=17;for(auto& e:zone->abilities)if(NightcapTHJ::RetiredAA(e.second.id))expected+=e.second.rank.total_cost;
 Client c=owned();check(c.RetireTHJAbilities(),"retire failed");
 check(c.wallet==expected,"refund not full canonical cost");
 check(c.m_earned_aa_ranks.size()==1&&c.m_earned_aa_ranks.count(65000),"retirement erased unrelated or retained retired ownership");
 check(c.aa_ranks.size()==1&&c.aa_ranks.count(999999),"usable projection wrong");
 check(c.spent==40&&c.m_epp.expended_aa==9,"spent/expended boundary wrong");
 check(c.persist_calls==1,"more than one persistence call");
 check(c.RetireTHJAbilities()&&c.wallet==expected&&c.persist_calls==1,"repeat load refunded twice");
 for(auto& e:zone->abilities){if(!NightcapTHJ::RetiredAA(e.second.id))continue;
  Client one;one.m_earned_aa_ranks[e.first]={e.second.rank.current_value,0};
  check(one.RetireTHJAbilities()&&one.m_earned_aa_ranks.empty()&&one.wallet==17+e.second.rank.total_cost,"individual/disabled family refund failed");
 }
 Client off=owned();auto pre=off.m_earned_aa_ranks;enabled=false;
 check(off.RetireTHJAbilities()&&off.wallet==17&&off.m_earned_aa_ranks==pre&&off.persist_calls==0,"disabled rule mutated state");enabled=true;
 Client bad=owned();bad.valid=false;
 check(!bad.RetireTHJAbilities()&&bad.persist_calls==0,"invalid session was persisted");
 Client failure=owned();auto saved=failure.m_earned_aa_ranks,active=failure.aa_ranks;failure.persist_ok=false;
 check(!failure.RetireTHJAbilities()&&failure.persist_calls==1,"persistence failure ignored");
 check(!failure.valid&&failure.wallet==17&&failure.m_earned_aa_ranks==saved&&failure.aa_ranks==active,"failed persist published partial refund");
 Client overflow=owned();overflow.wallet=UINT32_MAX;
 check(!overflow.RetireTHJAbilities()&&!overflow.valid&&overflow.wallet==UINT32_MAX&&overflow.persist_calls==0&&overflow.m_earned_aa_ranks==saved,"overflow published state");
 auto first=zone->abilities.begin()->first;auto original=zone->abilities.begin()->second;
 for(int mode=0;mode<5;++mode){
  zone->abilities[first]=original;auto& a=zone->abilities[first];
  if(mode==0)a.first_rank_id++;
  if(mode==1)a.rank.total_cost=-1;
  if(mode==2)a.charges=1;
  if(mode==3)a.grant_only=1;
  Client invalid=owned();if(mode==4)++invalid.m_earned_aa_ranks[first].first;
  check(!invalid.RetireTHJAbilities()&&!invalid.valid&&invalid.persist_calls==0&&invalid.wallet==17,"malformed retired ownership accepted");
 }zone->abilities[first]=original;
 std::cout<<"retirement checks="<<checks<<"\n";
 const int prior=checks;
 for(uint16 id:{8450,8451,8452,11068}){
  for(uint16 lock:{8450,8451,8452,11068}){
   Mob caster,target;target.buffs.insert(lock);
   check(!caster.Complete(id,&target)&&caster.mana==10001&&caster.debit_calls==0&&caster.timer_commits==0&&target.damaged==0,"cross-rank burn lockout consumed resource/timer");
  }
  Mob caster,target;const int cost=NightcapTHJ::PercentMana(caster.maximum,NightcapTHJ::ResourcePercent(id));
  caster.mana=cost-1;check(!caster.Complete(id,&target)&&caster.debit_calls==0&&caster.timer_commits==0&&target.damaged==0,"insufficient mana cast succeeded");
  caster.mana=cost;check(caster.Complete(id,&target)&&caster.mana==0&&caster.debit_calls==1&&caster.triggers==1&&caster.timer_commits==1&&target.damaged==int64(cost)*4,"exact mana/damage/debit boundary wrong");
  Mob failed,failedtarget;failed.reject_effect=true;
  check(!failed.Complete(id,&failedtarget)&&failed.mana==10001&&failed.debit_calls==0&&failed.timer_commits==0,"delivery failure consumed resource/timer");
  Mob missing;check(!missing.Complete(id,nullptr)&&missing.debit_calls==0&&missing.timer_commits==0,"missing target cast consumed resource/timer");
  Mob proc,proctarget;check(!proc.Complete(id,&proctarget,{},CastingSlot::AltAbility,true)&&proc.debit_calls==0,"proc converted resource");
  check(!proc.Complete(id,&proctarget,{},CastingSlot::Item)&&proc.debit_calls==0,"item-slot converted resource");
 }
 for(int count:{1,3,6}){
  Mob caster;std::vector<Mob> recipients(count);std::vector<Mob*> group;
  for(auto& recipient:recipients)group.push_back(&recipient);
  check(caster.Complete(2775,&recipients[0],group),"group Valor failed");
  check(caster.mana==5001&&caster.debit_calls==1&&caster.triggers==1&&caster.timer_commits==1&&caster.delivered==count,"group size multiplied debit/timer");
  for(auto& recipient:recipients)check(recipient.healed==10000,"recipient heal not 2HP per spent MP");
 }
 Mob focused,received;received.incoming_pct=20;received.incoming_crit_pct=30;received.heal_rate=25;received.incoming_flat=750;
 focused.incoming_pct=999;focused.incoming_flat=999999;
 check(focused.Complete(2775,&received,{&received})&&received.healed==19500&&received.healed_spell==2775,"recipient incoming modifier order wrong");
 check(focused.focus_calls==0&&received.focus_calls==3&&focused.debit_calls==1,"outgoing focus used or group cost changed");
 Mob debuffed,negative;negative.incoming_pct=-50;negative.heal_rate=-20;negative.incoming_flat=100;
 check(debuffed.Complete(2775,&negative,{&negative})&&negative.healed==4100,"incoming healing debuffs ignored");
 Mob blocked,immune;immune.incoming_pct=-200;
 check(blocked.Complete(2775,&immune,{&immune})&&immune.healed==0,"negative incoming healing wrapped unsigned");
 Mob low,recipient;low.mana=4999;
 check(!low.Complete(2775,&recipient,{&recipient})&&recipient.healed==0&&low.debit_calls==0&&low.timer_commits==0,"underfunded group Valor changed state");
 Mob zero,target;zero.maximum=0;check(!zero.Complete(8450,&target)&&zero.debit_calls==0,"zero max mana succeeded");
 std::cout<<"resource checks="<<(checks-prior)<<"\nPASS total="<<checks<<"\n";return 0;
 }catch(const std::exception& e){std::cerr<<"FAIL "<<e.what()<<"\n";return 1;}}
'''
(OUT / 'extracted_native_review.cpp').write_text(cpp, encoding='utf-8')
(OUT / 'build.cmd').write_text('@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat" >nul || exit /b 1\ncl /nologo /EHsc /W4 /std:c++17 extracted_native_review.cpp /Fe:extracted_native_review.exe >build.log 2>&1\nexit /b %errorlevel%\n')
build = subprocess.run(['cmd', '/d', '/c', str(OUT / 'build.cmd')], cwd=OUT, capture_output=True, text=True)
if build.returncode:
    raise RuntimeError((OUT / 'build.log').read_text(errors='replace') + build.stdout + build.stderr)
run = subprocess.run([str(OUT / 'extracted_native_review.exe')], cwd=OUT, capture_output=True, text=True)
stable = hashes == {path: sha(ROOT / path) for path in FILES}
report = dict(timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
              candidate_root=str(ROOT), source_sha256=hashes, source_stable_during_run=stable,
              retired_fixture=catalog, build_exit=build.returncode, test_exit=run.returncode,
              stdout=run.stdout, stderr=run.stderr,
              extracted=['Client::RetireTHJAbilities complete method','SpellFinished percent-resource guard',
                         'SpellFinished failed target-delivery branch','SpellFinished percent-resource debit',
                         'SpellEffect Act of Valor and Mana Burn branches'],
              limitations=['Persistence implementation is a fixture: proves no publication before acknowledgement, not SQL transaction atomicity.',
                           'Group delivery and timer commit are fixture boundaries; source-order assertion verifies guard/delivery/debit/native timer ordering.',
                           'Does not execute network/client packets, actual Group/Raid dispatch, full zone runtime, or player QA.'])
(OUT / 'verification.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
print(json.dumps(report, indent=2))
if run.returncode or not stable:
    raise SystemExit(1)
