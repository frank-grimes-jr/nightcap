"""Compile the actual Quick Buff dispatcher against controlled native boundaries."""
import sys
import unittest
from pathlib import Path
from test_pet_equipment import compile_run, ROOT
sys.path.insert(0, str(ROOT / 'tools'))
from quick_buff_client import strings, DESCRIPTION


class QuickBuff(unittest.TestCase):
    def test_client_text_is_scoped_and_repeatable(self):
        raw = b'147^1^Quick Buff\r\n147^4^Passive haste\r\n999^4^Keep exactly\n'
        updated = strings(raw)
        self.assertIn(b'147^2^Quick Buff\r\n', updated)
        self.assertIn(b'147^3^Quick Buff\r\n', updated)
        self.assertIn(DESCRIPTION.encode('ascii'), updated)
        self.assertIn(b'999^4^Keep exactly\n', updated)
        self.assertEqual(strings(updated), updated)

    def test_client_text_rejects_missing_identity_or_duplicate_keys(self):
        for raw in (b'', b'147^1^Other AA\n147^4^old\n',
                    b'147^1^Quick Buff\n', b'147^1^Quick Buff\n147^4^a\n147^4^b\n'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                strings(raw)

    def test_native_dispatch(self):
        source = ROOT / 'server-mods/code/zone/aa_quick_buff.inc'
        self.assertTrue(source.exists(), 'Quick Buff is still passive; activated dispatcher missing')
        compile_run(r'''
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <set>
#include <vector>
#include "''' + (ROOT / 'server-mods/code/common/quick_buff.h').as_posix() + r'''"
using uint16=uint16_t;using int32=int32_t;
namespace EQ { namespace spells { enum class CastingSlot { AltAbility }; } }
namespace Chat { enum { Red, White }; }
enum { ST_Pet=14,ST_SummonedPet=38,eaSitting,eaStanding };
struct Spell { int target_type=5; } spells[100];
bool IsValidSpell(int s){return s>0&&s<20;}
bool IsBeneficialSpell(int s){return s!=2;}
bool IsBuffSpell(int s){return s!=3;}
bool IsDiscipline(int s){return s==4;}
struct Database {} database;
constexpr int pTimerAAStart=0x100000;
struct Client;using Mob=Client;
struct Client {
 bool m_quick_buff_active=false,dead=false,busy=false,unconscious=false;
 int mana=1000,max_mana=1000,appearance=eaStanding,checks=0,debits=0,breaks=0;
 int blocked=0,pet=50,level=50;bool recurse=false,delaytimer=false;
 struct Timer {bool enabled=false;bool Enabled(){return enabled;}} spellend_timer;
 std::vector<int> gems{1,2,3,4,5,6,7,8,9,1,65535},casts,targets;
 struct Timers { int key=0; void Clear(Database*,int k){key=k;} } p_timers;
 bool IsDead(){return dead;} bool IsUnconscious(){return unconscious;}
 bool IsCasting(){return busy;} int GetAppearance(){return appearance;}
 void SetAppearance(int a,bool){appearance=a;}
 int GetMaxMana(){return max_mana;} int GetMana(){return mana;}
 void SetMana(int v){mana=v;++debits;}
 std::vector<int> GetMemmedSpells(){return gems;}
 bool HasSpellScribed(int s){return s!=5;}
 int GetSpellMinLevel(int s){return s==6?255:s==10?51:1;} int GetLevel(){return level;}
 bool DoCastingChecksOnCaster(int s,EQ::spells::CastingSlot){++checks;return s!=blocked;}
 bool DoCastingChecksZoneRestrictions(bool,int s){return s!=7;}
 bool DoCastingChecksOnTarget(bool,int s,Client*){return s!=8;}
 Client* GetPet(){return pet?this:nullptr;} int GetPetID(){return pet;}
 int GetID(){return 10;}
 template<class... T> void Message(T...){}
 void CommonBreakInvisible(){++breaks;}
 void SendAlternateAdvancementTimer(int a,int b,int c){assert(a==48&&b==0&&c==0);}
 bool CastSpell(int s,int target,EQ::spells::CastingSlot,int time,int cost,void*,int item,int timer,int duration,void*,int rank){
  assert(time==0&&cost==0&&item==-1&&timer==pTimerAAStart+48&&duration==0);
  assert(rank==147||rank==148||rank==149);
  if(recurse){recurse=false;CastQuickBuff(rank);}
  casts.push_back(s);targets.push_back(target);return true;
 }
 void CastQuickBuff(int);
};
#include "''' + source.as_posix() + r'''"
int main(){
 Client c;c.CastQuickBuff(147);assert((c.casts==std::vector<int>{1,9}));
 assert(c.mana==500&&c.debits==1&&c.breaks==1&&c.p_timers.key==pTimerAAStart+48);
 c.CastQuickBuff(149);assert(c.mana==0&&c.casts.size()==4); // no cooldown, any earned rank
 c.CastQuickBuff(148);assert(c.casts.size()==4&&c.debits==2);
 Client odd;odd.max_mana=1001;odd.CastQuickBuff(147);assert(odd.mana==500);
 Client tiny;tiny.max_mana=1;tiny.mana=1;tiny.CastQuickBuff(147);assert(tiny.mana==0);
 Client poor;poor.mana=499;poor.CastQuickBuff(147);assert(poor.mana==499&&poor.casts.empty());
 Client empty;empty.gems={2,3,4,5,6,7,8,65535};empty.CastQuickBuff(147);assert(empty.debits==0);
 Client blocked;blocked.gems={1};blocked.blocked=1;blocked.CastQuickBuff(147);assert(blocked.debits==0);
 Client dead;dead.dead=true;dead.CastQuickBuff(147);assert(dead.checks==0&&dead.debits==0);
 Client busy;busy.busy=true;busy.CastQuickBuff(147);assert(busy.checks==0&&busy.debits==0);
 Client delay;delay.delaytimer=true;delay.CastQuickBuff(147);assert(delay.debits==0);
 Client timer;timer.spellend_timer.enabled=true;timer.CastQuickBuff(147);assert(timer.debits==0);
 Client high;high.gems={10};high.CastQuickBuff(147);assert(high.debits==0);
 Client nomana;nomana.max_mana=0;nomana.CastQuickBuff(147);assert(nomana.debits==0);
 Client pet;spells[9].target_type=ST_Pet;pet.CastQuickBuff(147);assert(pet.targets.back()==50);
 Client missing;missing.pet=0;missing.gems={9};missing.CastQuickBuff(147);assert(missing.debits==0);
 Client recursive;recursive.recurse=true;recursive.CastQuickBuff(147);assert(recursive.debits==1);
 struct Ability {int type=2;} ability;
 struct Rank {int id=149,spell=-1,recast_time=5,upper_hotkey_sid=-1,lower_hotkey_sid=-1;std::vector<int> effects{127};} rank;
 NightcapQuickBuff::Configure(48,ability,rank);
 assert(ability.type==3&&rank.effects.empty()&&rank.spell==8&&rank.recast_time==0);
 assert(rank.upper_hotkey_sid==147&&rank.lower_hotkey_sid==147);
 assert(NightcapQuickBuff::IsRank(147)&&NightcapQuickBuff::IsRank(149)&&!NightcapQuickBuff::IsRank(150));
}
''')


if __name__ == '__main__':
    unittest.main()
