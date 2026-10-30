"""Actual bonus dispatch and raw AC must ignore training, even with its rule off."""
import unittest
import test_free_trade as native


class ItemXPBonusTests(unittest.TestCase):
    def test_native_bonus_dispatch(self):
        bonuses = (native.CODE/'zone/bonuses.cpp').read_text(encoding='utf-8')
        client = (native.CODE/'zone/client_mods.cpp').read_text(encoding='utf-8')
        methods = native.body(bonuses, 'void Mob::CalcItemBonuses(StatBonuses* b)')
        methods += '\n' + native.body(client, 'int32 Client::GetRawItemAC()')
        native.FreeTradeTests.compile_run(self, r'''
#include <array>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
using int16=int16_t;using int32=int32_t;using uint32=uint32_t;
#define CHECK(x) do { if (!(x)) { std::fprintf(stderr,"line %d: %s\n",__LINE__,#x); std::exit(1); } } while(false)
int additive_type=2;
#define RuleI(category,rule) additive_type
#define safe_delete(value) delete value
namespace EQ {
namespace invslot {
 constexpr int16 BONUS_BEGIN=0,BONUS_SKILL_END=22,BONUS_STAT_END=21,
 slotPowerSource=21,slotAmmo=22,slotPrimary=13,slotSecondary=14,
 GUILD_TRIBUTE_BEGIN=30,GUILD_TRIBUTE_END=31;
}
namespace item {enum {ItemTypeShield=1,ItemType2HBlunt,ItemType2HSlash,
 ItemType2HPiercing,ItemType1HSlash,ItemEffectWorn};}
struct ItemData {uint32 Slots=4;int AC=100,ItemType=0;};
struct ItemInstance {
 ItemData definition;const ItemData* GetItem()const{return &definition;}
 bool IsClassCommon()const{return true;}int GetItemRequiredLevel(bool)const{return 1;}
 uint32 GetID()const{return 1001;}
};
}
struct Inventory {
 std::array<EQ::ItemInstance*,32> slots{};
 const EQ::ItemInstance* GetItem(int16 slot)const{return slots[slot];}
 const EQ::ItemInstance* operator[](int16 slot)const{return slots[slot];}
};
struct StatBonuses {int ShieldBlock=0,normal=0,worn=0;};
struct Tribute {int tribute=0,tier=0;};
struct Profile {bool tribute_active=false;std::array<Tribute,1> tributes{};};
namespace NightcapPaladinGrip {
 struct Grip {int shield_block=0;};
 const Grip* FindProfile(uint32){return nullptr;}
}
struct Database {const EQ::ItemInstance* CreateItem(int){return nullptr;}} database;
struct Client;
struct Mob {
 Inventory m_inv;bool client=true;Profile pp;
 Inventory& GetInv(){return m_inv;}bool IsClient()const{return client;}
 bool IsOfClientBot()const{return false;}bool IsMerc()const{return false;}
 Client* CastToClient();int GetLevel()const{return 50;}
 void ClearItemFactionBonuses(){}void SetShieldEquipped(bool){}
 void SetTwoHandBluntEquipped(bool){}void SetTwoHanderEquipped(bool){}
 void SetDualWeaponsEquipped(bool){}bool CanThisClassDualWield()const{return false;}
 void SetAttackTimer(){}
 void AddItemBonuses(const EQ::ItemInstance* item,StatBonuses* b,bool,bool,int=0,bool=false){b->normal+=item->GetItem()->AC;}
 void AdditiveWornBonuses(const EQ::ItemInstance* item,StatBonuses* b){b->worn+=item->GetItem()->AC;}
 void CalcItemBonuses(StatBonuses*);
};
struct Client:Mob {
 bool CanEquipItem(const EQ::ItemData*)const{return true;}
 Profile& GetPP(){return pp;}int LookupTributeItemID(int,int){return 0;}
 int32 GetRawItemAC();
};
Client* Mob::CastToClient(){return static_cast<Client*>(this);}
''' + methods + r'''
int main() {
 Client c;EQ::ItemInstance worn,training,power;
 worn.definition.AC=25;training.definition.AC=1000;
 power.definition.AC=7;power.definition.Slots=uint32{1}<<21;
 c.m_inv.slots[2]=&worn;c.m_inv.slots[21]=&training;
 StatBonuses b;c.CalcItemBonuses(&b);
 CHECK(b.normal==25);CHECK(b.worn==25);CHECK(c.GetRawItemAC()==25);
 c.m_inv.slots[21]=&power;b={};c.CalcItemBonuses(&b);
 CHECK(b.normal==32);CHECK(b.worn==32);CHECK(c.GetRawItemAC()==32);
 c.m_inv.slots[21]=nullptr;b={};c.CalcItemBonuses(&b);
 CHECK(b.normal==25);CHECK(b.worn==25);CHECK(c.GetRawItemAC()==25);
 // The suppression is client-specific and does not reinterpret NPC inventory.
 c.client=false;c.m_inv.slots[21]=&training;b={};c.CalcItemBonuses(&b);
 CHECK(b.normal==1025);CHECK(b.worn==1025);
}
''')


if __name__ == '__main__':
    unittest.main()
