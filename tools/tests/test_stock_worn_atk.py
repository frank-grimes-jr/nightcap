import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import thj_stock_scaling as scaling
import test_free_trade as native


class StockWornAttackTests(unittest.TestCase):
    def test_scoped_policy_and_conflicting_sources(self):
        targets = scaling.worksheet_atk_targets()
        self.assertEqual(len(targets),157)
        self.assertEqual(len([i for i,v in targets.items() if int(scaling.stock()[i]['attack'])!=v]),135)
        base=scaling.stock()[26771]
        self.assertEqual([scaling.tier_target(base,t)['attack'] for t in (1,2,3)], [51,52,53])
        for ident, expected in [(40343,0),(11402,0),(28957,10),(21997,15),(9487,0),(68198,25),(7869,20)]:
            self.assertNotIn(ident,targets)
            self.assertEqual(scaling.top_target(scaling.stock()[ident])['attack'],expected)
        self.assertTrue(set(targets).isdisjoint(scaling.starter_retune.APPROVED_IDS | scaling.EPICS))

    def test_worn_cap_and_inventory_rating(self):
        # Compile the checked-in native functions and actual ATK assignment.
        bonuses=(native.CODE/'zone/bonuses.cpp').read_text(encoding='utf8')
        add=native.body(bonuses,'void Mob::AddItemBonuses(')
        start=add.index('const auto current_level = GetLevel();')
        end=add.index('b->HP += CalcItemBonus',start)
        assignment=next(line for line in add.splitlines() if 'b->ATK ' in line and 'item->Attack' in line)
        final=next(line for line in bonuses.splitlines() if 'itembonuses.ATK = std::min(itembonuses.ATK, CalcItemATKCap())' in line)
        cap=native.body((native.CODE/'zone/client_mods.cpp').read_text(encoding='utf8'),'int32 Client::CalcItemATKCap()')
        rating=native.body((native.CODE/'zone/client.cpp').read_text(encoding='utf8'),'uint32 Client::GetTotalATK()')
        recommended=native.body(bonuses,'int Mob::CalcRecommendedLevelBonus(')
        cpp=r"""
#include <algorithm>
#include <cassert>
#include <cstdint>
using uint8=uint8_t; using int32=int32_t; using uint32=uint32_t;
#define RuleI(group, rule) 250
#define RuleB(group, rule) true
namespace EQ { namespace skills { enum {SkillOffense}; } }
struct Bonuses { int ATK=0, ItemATKCap=0; };
struct Item {int Attack,required,recommended; int GetItemRequiredLevel(bool){return required;}
 uint8 GetItemRecommendedLevel(bool){return static_cast<uint8>(recommended);} };
struct Mob { static int CalcRecommendedLevelBonus(uint8,uint8,int); };
struct Client : Mob {
 Bonuses itembonuses,spellbonuses,aabonuses; int level=60;
 uint8 GetLevel(){return static_cast<uint8>(level);} bool IsClient(){return true;} bool IsNPC(){return false;}
 bool IsOfClientBotMerc(){return true;} int GetSkill(int){return 110;}
 int GetSTR(){return 180;} int GetPrimarySkillValue(){return 140;}
 int GroupLeadershipAAOffenseEnhancement(){return 0;} uint32 GetATK(){return 0;}
 int32 CalcItemATKCap(); uint32 GetTotalATK();
 void equip(Item *inst){auto *item=inst;auto *b=&itembonuses;
 bool is_ammo_item=false,is_augment=false;uint8 recommended_level_override=0;
""" + add[start:end] + assignment + '\n' + final + '\n}\n};\n' + recommended + '\n' + cap + r"""
#ifdef _MSC_VER
// The native rating deliberately truncates the double to an unsigned integer.
#pragma warning(push)
#pragma warning(disable:4244)
#endif
""" + rating + r"""
#ifdef _MSC_VER
#pragma warning(pop)
#endif
int main(){
 Client c;Item armguard{50,0,60};auto rate=[&](int worn,int atk){
  c.itembonuses.ATK=worn;armguard.Attack=atk;c.equip(&armguard);return c.GetTotalATK();};
 auto old=rate(0,50); assert(c.itembonuses.ATK==50); auto updated=rate(0,53);
 assert(c.itembonuses.ATK==53 && updated-old==4);
 c.level=50;old=rate(0,50);assert(c.itembonuses.ATK==42);
 updated=rate(0,53);assert(c.itembonuses.ATK==44 && updated-old==3);
 c.level=60;old=rate(199,50);updated=rate(199,53);
 assert(c.itembonuses.ATK==250 && updated-old==1);
 old=rate(200,50);updated=rate(200,53);assert(old==updated && c.itembonuses.ATK==250);
 c.aabonuses.ItemATKCap=10;old=rate(200,50);updated=rate(200,53);assert(updated-old==4);
 c.itembonuses.ItemATKCap=5;c.spellbonuses.ItemATKCap=5;assert(c.CalcItemATKCap()==270);
 armguard.required=65;old=rate(0,50);updated=rate(0,53);assert(old==updated && c.itembonuses.ATK==0);
}
"""
        native.FreeTradeTests.compile_run(self,cpp)

if __name__=='__main__':unittest.main()
