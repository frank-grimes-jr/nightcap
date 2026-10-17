'''Compile the actual server recommendation method against a captured legal catalog.
Database/transport/purchase predicates are controlled boundaries; this is not a
full zone build or visual acceptance of the RoF2 window.
'''
import gzip,json,os,re,subprocess,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0,str(ROOT/'tools'))
from aa_tbs_policy import compile_policy

PREFIX=r'''
#include <cassert>
#include <map>
#include <cstdarg>
#include <cstdio>
#include <sstream>
#include <iostream>
#include "ui_state.h"
using uint32=uint32_t;
namespace fmt {
 template<class...T> std::string format(std::string text,T...args) {
  auto add=[&](const auto& value){std::ostringstream s;s<<value;auto at=text.find("{}");assert(at!=std::string::npos);text.replace(at,2,s.str());};
  (add(args),...);return text;
 }
}
namespace EQ {namespace skills {enum {SkillRoundKick,SkillTigerClaw,SkillEagleStrike,SkillDragonPunch,SkillFlyingKick,SkillMend,SkillBackstab,SkillArchery,SkillThrowing};}}
namespace Chat {enum {White};}
struct Client;
struct Rank {int id;uint32 current_value;int ability;std::map<int,int> prereqs;};
struct Ability {int id,first_rank_id;uint32 classes;bool charges=false,grant_only=false;std::vector<Rank> ranks;
 uint32 GetMaxLevel(Client*) {return static_cast<uint32>(ranks.size());}
 Rank* GetRankByPointsSpent(uint32 n) {return n && n<=ranks.size()?&ranks[n-1]:nullptr;}
};
struct Zone {std::map<int,Ability> abilities;std::map<int,int> owners;
 Ability* GetAlternateAdvancementAbility(int id){auto it=abilities.find(id);return it==abilities.end()?nullptr:&it->second;}
 unsigned GetZoneID(){return 63;} unsigned GetInstanceID(){return 0;}
} fixture;
Zone* zone=&fixture;
struct Client {
 bool m_nightcap_ui_enabled=true,m_nightcap_aa_recommendations_enabled=true,valid=true;
 uint32 m_nightcap_ui_generation=1,mask=1;std::string m_nightcap_aa_recommendations_cache;
 std::map<int,uint32> owned;bool skills=true,pet=true;nightcap::UIState ui;std::vector<std::string> messages;
 Client(){assert(ui.Consume("[NCUI1]S|1|42|63|0|7|1|0|0|Testplayer"));}
 bool HasValidEarnedAAState(){return valid;}
 unsigned CharacterID(){return 42;} unsigned GetID(){return 7;}
 unsigned GetAA(int rank,uint32*){return owned[fixture.owners.at(rank)];}
 bool CanUseAlternateAdvancementRank(Rank* rank){return rank && (fixture.abilities.at(rank->ability).classes&mask);}
 bool HasAlreadyPurchasedRank(Rank* r){return owned[r->ability]>=r->current_value;}
 bool CanPurchaseAlternateAdvancementRank(Rank* r,bool price,bool grant){assert(!price && grant);
  if(!CanUseAlternateAdvancementRank(r) || HasAlreadyPurchasedRank(r))return false;
  for(auto p:r->prereqs)if(owned[p.first]<static_cast<uint32>(p.second))return false;return true;
 }
 int GetSkill(int){return skills?5:0;} void* GetPet(){return pet?this:nullptr;}
 std::vector<unsigned> GetMulticlassList(){return {1,2,3};} unsigned GetClassPet(unsigned){return 0;}
 void Message(int,const char* pattern,...) {char s[256];va_list args;va_start(args,pattern);auto n=vsnprintf(s,sizeof(s),pattern,args);va_end(args);assert(n>0 && n<256);messages.emplace_back(s);assert(ui.Consume(s));}
 void SendAARecommendations();
};
'''


class Recommendations(unittest.TestCase):
    def test_native_sender_catalog_and_identity(self):
        config=json.loads((ROOT/'config/aa-policy.json').read_text())
        tables=json.loads(gzip.decompress((ROOT/config['catalog']).read_bytes()))
        legal=compile_policy(tables,config)
        abilities={x['id']:x for x in tables['aa_ability']}
        entries=[int(x) for x in re.findall(r'\{(\d+),\d+,\d+,\d+,\w+\}',(ROOT/'server-mods/code/common/aa_recommendations.h').read_text())]
        self.assertGreater(len(entries),25)
        self.assertEqual(len(entries),len(set(entries)))
        self.assertTrue(set(entries)<=set(x['ability_id'] for x in legal))
        setup=[]
        for aid in sorted({x['ability_id'] for x in legal}):
            a=abilities[aid]
            setup.append(f'fixture.abilities[{aid}]={{{aid},{a["first_rank_id"]},{a["classes"]}}};')
        for row in legal:
            aid=row['ability_id'];rid=row['rank_id']
            prereqs=','.join('{'+str(k)+','+str(v)+'}' for k,v in row['prereqs'].items())
            setup.append(f'fixture.abilities[{aid}].ranks.push_back({{{rid},{row["ordinal"]},{aid},{{{prereqs}}}}});fixture.owners[{rid}]={aid};')
        body=r"""
 unsigned combinations=0;
 for(unsigned a=0;a<16;++a)for(unsigned b=a;b<16;++b)for(unsigned c=b;c<16;++c){
  Client p;p.mask=(1u<<a)|(1u<<b)|(1u<<c);p.SendAARecommendations();
  assert(p.ui.RecommendationsReady() && p.ui.RecommendationCount()<=10 && p.ui.RecommendationCount()>=3);
  for(auto& pair:fixture.owners)if(p.ui.Recommended(pair.first))assert(fixture.abilities.at(pair.second).classes&p.mask);
  const auto before=p.messages.size();p.SendAARecommendations();assert(p.messages.size()==before);
  ++combinations;
 }
 Client p;p.mask=(1u<<2)|(1u<<0)|(1u<<6);p.SendAARecommendations();
 auto health=fixture.abilities.at(28).first_rank_id;assert(p.ui.Recommended(health));
 p.owned[28]=1;p.SendAARecommendations();assert(!p.ui.Recommended(health));
 assert(p.ui.Recommended(fixture.abilities.at(28).ranks[1].id));
 for(auto& a:fixture.abilities)p.owned[a.first]=a.second.GetMaxLevel(&p);
 p.SendAARecommendations();assert(p.ui.RecommendationCount()==0);
 p.owned[206]=0;p.skills=false;p.SendAARecommendations();
 assert(p.ui.Recommendation(fixture.abilities.at(206).first_rank_id).find("Later:")==0);
 p.skills=true;p.SendAARecommendations();assert(p.ui.Recommendation(fixture.abilities.at(206).first_rank_id).find("Later:")!=0);
 p.mask=1;p.SendAARecommendations();assert(p.ui.RecommendationCount()==0); // released Monk
 p.mask=1u<<6;p.owned[206]=5;p.owned[97]=0;p.owned[17]=0;p.SendAARecommendations();
 assert(p.ui.Recommended(fixture.abilities.at(17).first_rank_id)); // prerequisite surfaced
 assert(p.ui.Recommendation(fixture.abilities.at(97).first_rank_id).find("Needs prerequisite:")==0);
 Client old;old.m_nightcap_aa_recommendations_enabled=false;old.SendAARecommendations();assert(old.messages.empty());
 Client invalid;invalid.valid=false;invalid.SendAARecommendations();assert(invalid.messages.empty());
 std::cout<<combinations<<" class combinations; purchase, completion, skills, prerequisites, release and cache controls passed\n";
"""
        source=PREFIX+'\n#include "'+str(ROOT/'server-mods/code/zone/aa_recommendations.inc').replace('\\','/')+'"\nint main(){\n'+'\n'.join(setup)+body+'}\n'
        with tempfile.TemporaryDirectory(prefix='aa-recommendations-') as tmp:
            tmp=Path(tmp);cpp=tmp/'test.cpp';exe=tmp/'test.exe';cpp.write_text(source)
            command=['cl','/nologo','/EHsc','/std:c++17','/I'+str(ROOT/'eq-client-dll/src'),str(cpp),'/Fo:'+str(tmp)+'\\','/Fe:'+str(exe)]
            subprocess.run(command,check=True,cwd=tmp)
            subprocess.run([str(exe)],check=True)

if __name__=='__main__':unittest.main()
