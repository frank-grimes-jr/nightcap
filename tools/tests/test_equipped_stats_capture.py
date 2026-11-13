"""Execute actual server focus/bonus collection without a database or live player."""
from pathlib import Path
import unittest
import test_free_trade as native

ROOT=Path(__file__).resolve().parents[2]


class EquippedStatsCapture(unittest.TestCase):
    def test_quiet_poll_keeps_permission_checks_and_other_command_auditing(self):
        source=(ROOT/'server-mods/code/zone/command.cpp').read_text()
        dispatch=native.body(source,'int command_realdispatch(')
        quiet=dispatch.index('current_command->function == command_nightcapui')
        self.assertLess(dispatch.index('c->Admin()'),quiet)
        self.assertLess(dispatch.index('command_subsettings'),quiet)
        self.assertLess(quiet,dispatch.index('EVENT_GM_COMMAND'))
        self.assertLess(quiet,dispatch.index('RecordPlayerEventLogWithClient'))
        self.assertIn('sep.argnum == 1',dispatch[quiet:quiet+260])
        self.assertIn('!strcmp(sep.arg[1], "stats")',dispatch[quiet:quiet+260])
        self.assertIn('!strcmp(sep.arg[1], "inventory")',dispatch[quiet:quiet+260])
    def test_actual_collection_excludes_bags_training_ineligible_and_stacks_strongest(self):
        text=(ROOT/'server-mods/code/zone/gm_commands/nightcapui.cpp').read_text()
        bodies=native.body(text,'static void AddEquippedFocus(')+'\n'+native.body(text,'static NightcapStats::Snapshot CaptureEquippedStats(')
        fixture=r'''
#include "common/equipped_stats_protocol.h"
#include "common/nightcap_thj_behaviors.h"
#include <algorithm>
#include <cassert>
#include <map>
bool classic=false,thj=true;
enum {UseClassicSpellFocus=1,NightcapTHJBehaviors=2};
#define RuleB(category,key) (key==UseClassicSpellFocus?classic:thj)
#define RuleI(category,key) key
enum {ItemShieldingCap=35,ItemSpellShieldingCap=35,ItemDamageShieldCap=35,ItemDoTShieldingCap=35,
ItemDSMitigationCap=50,ItemAvoidanceCap=100,ItemAccuracyCap=150,ItemStunResistCap=35,ItemStrikethroughCap=35,
ItemHealAmtCap=750,ItemSpellDmgCap=750,ItemClairvoyanceCap=250,ItemCombatEffectsCap=100};
using uint8=uint8_t;using int16=int16_t;using uint32=uint32_t;
constexpr int EFFECT_COUNT=12;
namespace SpellEffect{constexpr int IncreaseSpellHaste=127,ReduceManaCost=132;}
struct Spell{int effect_id[12]={},base_value[12]={},limit_value[12]={};};
std::map<int,Spell> spells;
bool IsValidSpell(int id){return spells.count(id)>0;}
namespace EQ{
namespace item{constexpr int ItemEffectFocus=6,ItemEffectWorn=2;}
namespace invslot{constexpr int EQUIPMENT_BEGIN=0,EQUIPMENT_END=22,slotPowerSource=21;}
namespace invaug{constexpr int SOCKET_COUNT=6;}
struct ItemData{struct EffectData{int Effect=0,Type=0,Level=1;}Worn,Focus;uint32 Slots=0;bool allowed=true;};
struct ItemInstance{ItemData data;int level=1;bool common=true;std::map<int,ItemInstance*>aug;
 bool IsClassCommon(){return common;}const ItemData*GetItem(){return &data;}int GetItemRequiredLevel(bool){return level;}
 ItemInstance*GetAugment(int n){return aug.count(n)?aug[n]:nullptr;}};
}
struct Inv{std::map<int,EQ::ItemInstance*>items;EQ::ItemInstance*GetItem(int slot){return items.count(slot)?items[slot]:nullptr;}};
struct Bonuses{int ShieldBlock=0,DodgeChance=0;};
struct Client{Inv inv;bool shield=true;Bonuses item{1,10},spell{2,3},aa{4,5};
 Bonuses GetItemBonuses(){return item;}Bonuses GetSpellBonuses(){return spell;}Bonuses GetAABonuses(){return aa;}
 bool HasShieldEquipped(){return shield;}int GetShielding(){return 6;}int GetSpellShield(){return 12;}
 int GetDS(){return 8;}int GetDoTShield(){return 2;}int GetDSMit(){return 5;}int GetAvoidance(){return 24;}
 int GetAccuracy(){return 30;}int GetStunResist(){return 7;}int GetStrikeThrough(){return 8;}
 int GetHealAmt(){return 92;}int GetSpellDmg(){return 29;}int GetClair(){return 1;}int GetCombatEffects(){return 2;}
 int GetLevel(){return 50;}Inv&GetInv(){return inv;}bool CanEquipItem(const EQ::ItemData*d){return d->allowed;}};
namespace NightcapHunt{int OutputShieldBlock(Client&c){return c.shield?1:0;}int OutputHeadroom(Client&,bool heal){return heal?30:20;}}
// BODIES
int main(){using namespace NightcapStats;Client c;
 Spell haste;haste.effect_id[0]=127;haste.base_value[0]=15;spells[2341]=haste;
 Spell mana;mana.effect_id[0]=132;mana.base_value[0]=1;mana.limit_value[0]=10;spells[2344]=mana;
 EQ::ItemInstance armor,a,b,faerune,bag,training,invalid;
 a.data.Focus={2341,6,60};b.data.Focus={2344,6,60};faerune.data.Worn={3660,2,60};
 armor.aug[0]=&a;armor.aug[1]=&b;armor.aug[2]=&faerune;armor.aug[3]=&a;
 c.inv.items[2]=&armor;auto s=CaptureEquippedStats(c);
 assert(s.values[ShieldBlock]==7&&s.values[HuntBlock]==1&&s.values[Dodge]==18);
 assert(s.values[Heal]==92&&s.values[HealCap]==780&&s.values[SpellDamageCap]==770);
 assert(s.values[SpellHaste]==15&&s.values[ManaMax]==10&&s.values[Faerune]==1);
 c.shield=false;s=CaptureEquippedStats(c);assert(s.values[ShieldBlock]==0&&s.values[HuntBlock]==0);
 armor.level=60;s=CaptureEquippedStats(c);assert(s.values[SpellHaste]==0&&s.values[Faerune]==0);armor.level=1;
 armor.data.allowed=false;assert(CaptureEquippedStats(c).values[ManaMax]==0);armor.data.allowed=true;
 c.inv.items.clear();bag.aug=armor.aug;training.aug=armor.aug;c.inv.items[23]=&bag;c.inv.items[21]=&training;
 s=CaptureEquippedStats(c);assert(s.values[SpellHaste]==0&&s.values[ManaMax]==0&&s.values[Faerune]==0);
 training.data.Slots=1u<<21;assert(CaptureEquippedStats(c).values[Faerune]==1);
 c.inv.items.clear();c.inv.items[2]=&armor;a.data.Focus.Type=0;faerune.data.Worn.Type=0;
 s=CaptureEquippedStats(c);assert(s.values[SpellHaste]==0&&s.values[Faerune]==0&&s.values[ManaMax]==10);
 classic=true;assert(CaptureEquippedStats(c).values[ManaMax]==1);classic=false;
 b.data.Focus.Type=0;assert(CaptureEquippedStats(c).values[ManaMax]==0);
}
'''
        native.FreeTradeTests.compile_run(self,fixture.replace('// BODIES',bodies))


if __name__=='__main__':unittest.main()
