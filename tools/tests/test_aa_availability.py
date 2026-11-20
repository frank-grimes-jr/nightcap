"""Native AA purchase and wire-prerequisite regression; no live/player writes.

Extract actual methods with explicit engine doubles. All 696 legal one-to-three
class sets are exercised in every primary-class ordering. This is not an EQ
client UI test or a real SQL class-release transaction test.
"""
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

from test_gameplay_policies import ROOT, function
from verify_aa_tbs_native import STUBS
from test_aa_cooldown_identity import FIXTURE
from aa_tbs_policy import compile_policy

SOURCE = ROOT / 'server-mods/code'


def execute(source):
    with tempfile.TemporaryDirectory(prefix='aa-availability-') as temp:
        path = Path(temp)
        (path / 'test.cpp').write_text(source, encoding='utf-8')
        if os.name == 'nt':
            (path / 'build.cmd').write_text(
                '@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars64.bat" >nul || exit /b 1\n'
                f'cl /nologo /EHsc /W4 /std:c++17 /I"{SOURCE}" test.cpp /Fe:test.exe\n')
            cmd = ['cmd', '/d', '/c', str(path / 'build.cmd')]
        else:
            cmd = ['g++', '-std=c++17', '-I', str(SOURCE), 'test.cpp', '-o', 'test.exe']
        built = subprocess.run(cmd, cwd=path, capture_output=True, text=True)
        if built.returncode:
            raise AssertionError(built.stdout + built.stderr)
        run = subprocess.run([str(path / 'test.exe')], capture_output=True, text=True)
        if run.returncode:
            raise AssertionError(run.stdout + run.stderr)
        print(run.stdout.strip())


INCLUDES = r'''
#if __has_include("common/aa_availability.h")
#include "common/aa_availability.h"
#endif
#include <stdexcept>
void require(bool value, const char* why) {if(!value)throw std::runtime_error(why);}
int bits(unsigned value) {int n=0;while(value){n+=value&1;value>>=1;}return n;}
'''


class AAAvailability(unittest.TestCase):
    def test_no_rank_identity_or_cap_changes(self):
        config = json.loads((ROOT / 'config/aa-policy.json').read_text(encoding='utf-8'))
        tables = json.loads(gzip.decompress((ROOT / config['catalog']).read_bytes()))
        rows = compile_policy(tables, config)
        identities = [(r['rank_id'], r['ability_id'], r['ordinal']) for r in rows]
        digest = hashlib.sha256(json.dumps(identities, separators=(',', ':')).encode()).hexdigest()
        self.assertEqual(digest, '2d4a0460fe83624710a27f2532d811976bbf00fa30b520cc7d2141bedd748f68')

    def test_native_purchase_all_class_sets_and_ownership_projection(self):
        aa = (SOURCE / 'zone/aa.cpp').read_text(encoding='utf-8')
        client = (SOURCE / 'zone/client.cpp').read_text(encoding='utf-8')
        methods = '\n'.join(function(aa, s) for s in (
            'bool Mob::CanUseAlternateAdvancementRank(',
            'bool Mob::CanPurchaseAlternateAdvancementRank(',
            'bool Client::HasAlreadyPurchasedRank(',
            'bool Client::ReprojectEarnedAAs('))
        methods += '\n' + function(client, 'uint32 Client::GetEarnedAACount(')
        # Explicit engine boundary: walk the three fixture ranks. Eligibility,
        # purchase, duplicate detection and earned projection are actual methods.
        methods += r'''
int AA::Ability::GetMaxLevel(Mob* who){int count=0;for(auto* r=first;r;r=r->next){
 if(!who->CanUseAlternateAdvancementRank(r))break;++count;}return count;}
AA::Rank* AA::Ability::GetRankByPointsSpent(int n){if(!n)return nullptr;
 for(auto* r=first;r;r=r->next)if(r->current_value==n)return r;return nullptr;}
'''
        execute(STUBS + INCLUDES + methods + r'''
int main(){try {
 auto& a=zone->abilities[150];a.id=150;a.classes=32446u<<1;a.first_rank_id=446;
 auto& dep=zone->abilities[26];dep.id=26;dep.classes=15504u<<1;dep.first_rank_id=101;
 AA::Rank ranks[3];
 for(int n=0;n<3;++n){auto& r=ranks[n];r.id=446+n;r.current_value=n+1;r.expansion=4;
  r.base_ability=&a;r.cost=3;r.total_cost=3*(n+1);r.prereqs[26]=3;
  r.prev=n?&ranks[n-1]:nullptr;r.next=n<2?&ranks[n+1]:nullptr;}
 a.first=&ranks[0];
 AA::Rank expertise{101,3,3,1,&dep,nullptr};dep.first=&expertise;
 int cases=0,sets=0;
 for(unsigned raw=1;raw<65536;++raw){if(bits(raw)>3)continue;++sets;
  for(int primary=1;primary<=16;++primary){if(!(raw&(1u<<(primary-1))))continue;
   for(int ordinal=1;ordinal<=3;++ordinal){Client c;c.mask=raw<<1;c.class_id=primary;
    if(ordinal>1){c.aa_ranks[150]={ordinal-1,0};c.m_earned_aa_ranks[446]={ordinal-1,0};}
    bool eligible=(raw&32446)!=0,waived=(raw&16942)!=0;
    require(c.CanPurchaseAlternateAdvancementRank(&ranks[ordinal-1],true,true)==(eligible&&waived),
      "Mastery purchase blocked for independent non-expertise class or opened for caster without prerequisite");
    c.aa_ranks[26]={3,0};
    require(c.CanPurchaseAlternateAdvancementRank(&ranks[ordinal-1],true,true)==eligible,"owned prerequisite rejected");
    c.m_pp.aapoints=2;require(!c.CanPurchaseAlternateAdvancementRank(&ranks[ordinal-1],true,true),"price bypass");
    c.m_pp.aapoints=3;c.valid=false;require(!c.CanPurchaseAlternateAdvancementRank(&ranks[ordinal-1],true,true),"invalid ownership bypass");
    ++cases;
   }
  }
 }
 require(sets==696,"class-set coverage changed");
 Client c;c.mask=1u<<3;c.class_id=3;
 c.m_earned_aa_ranks[446]={3,0};require(c.ReprojectEarnedAAs(),"projection failed");
 require(c.aa_ranks.at(150).first==3,"owned rank lost");
 c.mask|=1u<<12;require(c.ReprojectEarnedAAs(),"class addition failed");
 require(c.aa_ranks.at(150).first==3,"adding caster removed hybrid access");
 c.mask=1u<<1;require(c.ReprojectEarnedAAs()&&c.aa_ranks.count(150)==0,"ineligible view retained");
 require(c.m_earned_aa_ranks.at(446).first==3,"projection erased earned rank");
 Client relog;relog.mask=1u<<3;relog.m_earned_aa_ranks=c.m_earned_aa_ranks;
 require(relog.ReprojectEarnedAAs()&&relog.aa_ranks.at(150).first==3,"relog failed to restore earned rank");
 require(!relog.CanPurchaseAlternateAdvancementRank(&ranks[2],true,true),"duplicate rank purchasable");
 Client npc;npc.client=false;npc.class_id=3;
 require(!npc.CanPurchaseAlternateAdvancementRank(&ranks[0],true,true),"NPC gained waiver");
#if __has_include("common/aa_availability.h")
 for(unsigned raw=0;raw<65536;++raw){
  require(NightcapAAAvailability::WaivesPrerequisite(150,26,raw<<1)==bool(raw&16942),"helper class scope");
  require(!NightcapAAAvailability::WaivesPrerequisite(151,26,raw<<1),"unrelated family waiver");
  require(!NightcapAAAvailability::WaivesPrerequisite(150,27,raw<<1),"unrelated dependency waiver");
 }
 require(!NightcapAAAvailability::WaivesPrerequisite(150,26,0x80000001u),"invalid class bits grant waiver");
#endif
 // Unrelated prerequisites stay mandatory, even on the corrected family.
 ranks[0].prereqs[999999]=1;Client missing;missing.mask=1u<<3;
 require(!missing.CanPurchaseAlternateAdvancementRank(&ranks[0],true,true),"missing prerequisite bypassed");
 std::cout<<"purchase_cases="<<cases<<" class_sets="<<sets<<" ownership_projection=passed\n";
 return 0;
}catch(const std::exception& e){std::cerr<<e.what();return 1;}}
''')

    def test_native_packet_prerequisites_are_per_client_and_preserve_shared_catalog(self):
        aa = (SOURCE / 'zone/aa.cpp').read_text(encoding='utf-8')
        fixture = FIXTURE.replace('/* TIMER_DECLARATIONS */', 'using pTimerType=uint32_t;')
        fixture = fixture.replace('void SetWritePosition(int) {} void WriteSInt32(int) {}',
            'std::vector<int> written; void SetWritePosition(int) {} void WriteSInt32(int value) {written.push_back(value);}')
        fixture = fixture.replace('std::vector<int> casts;', 'std::vector<int> wire;std::vector<int> casts;')
        fixture = fixture.replace('void QueuePacket(EQApplicationPacket* packet) {',
            'void QueuePacket(EQApplicationPacket* packet) { wire=packet->written;')
        methods = function(aa, 'void Client::SendAlternateAdvancementRank(')
        execute(fixture + INCLUDES + methods + r'''
int Client::GetAlternateAdvancementTimerSlot(int aid){return aid;}
int main(){try {
 for(int n=1;n<=3;++n){add_rank(150,445+n,n,-1,0,0,4,32446);zone->aa_ranks_values[445+n].prereqs={{26,3}};}
 int cases=0;
 for(unsigned raw=1;raw<65536;++raw){if(bits(raw)>3)continue;
  for(int primary=1;primary<=16;++primary){if(!(raw&(1u<<(primary-1))))continue;
   for(int n=1;n<=3;++n){Client c;c.held=raw<<1;c.primary=primary;c.SendAlternateAdvancementRank(150,n);
    if(!(raw&32446)){require(c.catalog.empty(),"ineligible packet published");continue;}
    require(c.catalog.size()==1,"eligible packet absent");bool waived=(raw&16942)!=0;
    require(c.catalog[0].total_prereqs==(waived?0:1),"packet prerequisite count disagrees with purchase access");
    require(c.wire==(waived?std::vector<int>{}:std::vector<int>{26,3}),"packet prerequisite payload mismatch");
    require(zone->aa_ranks_values[445+n].prereqs==std::map<int,int>{{26,3}},"shared catalog mutated");
    require(c.catalog[0].classes&(1u<<primary),"primary presentation hides eligible AA");++cases;
   }
  }
 }
 auto& first=zone->aa_ranks_values[446];first.prereqs[999999]=2;
 Client c;c.held=1u<<3;c.primary=3;c.SendAlternateAdvancementRank(150,1);
 require(c.catalog[0].total_prereqs==1&&c.wire==std::vector<int>{999999,2},"unrelated wire prerequisite stripped");
 require(first.prereqs.size()==2,"filter mutated shared prerequisite map");
 std::cout<<"packet_cases="<<cases<<" shared_catalog=preserved\n";return 0;
}catch(const std::exception& e){std::cerr<<e.what();return 1;}}
''')


if __name__ == '__main__':
    unittest.main(verbosity=2)
