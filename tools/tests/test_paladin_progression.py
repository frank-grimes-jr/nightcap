"""Execute production exchange/bonus logic; retained definitions and APIs are fixtures."""
import json
from pathlib import Path
import unittest
import test_free_trade as native


class ProgressionTests(unittest.TestCase):
    compile_run = native.FreeTradeTests.compile_run

    def test_free_exchange_preserves_identity_fields_and_handles_failures(self):
        fixture=(native.ROOT/'tools/tests/fixtures/paladin_weapon_grip.cpp').read_text().split('// PRODUCTION_HANDLER')[0]
        fixture=fixture.replace('constexpr int slotPrimary=13, slotSecondary=14;', 'constexpr int slotPrimary=13, slotSecondary=14, GENERAL_BEGIN=23, GENERAL_END=32;')
        fixture=fixture.replace('struct ItemData { int ItemType=1;', 'struct ItemData { unsigned ID=10099, AugSlotType[6]={7,7,7,7,7,7}; int ItemType=1;')
        fixture=fixture.replace('return id;}','return data.ID;}')
        fixture=fixture.replace('Item *GetAugment(uint8 i) {','Item *GetAugment(uint8 i) const {')
        fixture=fixture.replace('void DeleteCustomData(', 'void SetCustomDataString(const std::string &s){metadata=s;data.ItemType=s.empty()?1:0;}\n void DeleteCustomData(')
        fixture=fixture.replace('struct Inventory {', 'namespace EQ {using ItemInstance=Item;using ItemData=::ItemData;}\nstruct Inventory {\n Item stored;bool fail_put=false;\n int PutItem(int slot,const Item &i){if(fail_put)return -1;stored=i;slots[slot]=&stored;return slot;}')
        fixture=fixture.replace('Reply reply;', 'ItemData target{810099}; bool missing=false;\n const ItemData *GetItem(unsigned id){assert(id==810099);return missing?nullptr:&target;}\n Reply reply;')
        fixture=fixture.replace('bool TogglePaladinWeaponGrip(int32 slot_id);','bool AscendPaladinEpic();')
        method=native.body((native.CODE/'zone/inventory.cpp').read_text(),'bool Client::AscendPaladinEpic(')
        self.compile_run(fixture+method+r'''
int main(){
 for(bool one : {false,true}) {
  Item sword,aug; sword.augment=&aug;sword.metadata=one?"nightcap_paladin_grip^1^":"";
  sword.data.ItemType=one?0:1;
  Client c;c.m_inv.slots[23]=&sword;database={};database.observed=&sword;database.expected=sword.metadata;
  assert(c.AscendPaladinEpic());auto *after=c.m_inv.GetItem(23);
  assert(after->GetID()==810099 && after->metadata==sword.metadata && after->data.ItemType==sword.data.ItemType);
  assert(after->guid==sword.guid && after->charges==sword.charges && after->attuned && after->augment==&aug && after->color==sword.color && after->ornament==sword.ornament);
  assert(database.sql.find("SET item_id=810099 WHERE ")!=std::string::npos);
  assert(database.sql.find("AND item_id=10099")!=std::string::npos);
  assert(!c.AscendPaladinEpic() && database.queries==1); // replay cannot duplicate
 }
 for(int fail=0;fail<5;++fail){
  Item sword;Client c;c.m_inv.slots[23]=&sword;database={};database.observed=&sword;
  if(fail==0)database.reply.ok=false;if(fail==1)database.reply.rows=0;
  if(fail==2)database.throws=true;if(fail==3)c.m_inv.fail_put=true;if(fail==4)c.throw_packet=true;
  assert(!c.AscendPaladinEpic() && c.quarantines==1 && database.queries==1);
 }
 for(int guard=0;guard<9;++guard){
  Item sword,aug;Client c;c.m_inv.slots[23]=&sword;database={};database.observed=&sword;
  if(guard==0)c.dead=true;if(guard==1)c.auto_attack=true;if(guard==2)c.aggro=1;
  if(guard==3)sword.evolving=true;if(guard==4)sword.scaling=true;if(guard==5)sword.metadata="foreign^data^";
  if(guard==6)database.missing=true;
  if(guard==7){sword.augment=&aug;database.target.AugSlotType[0]=8;}
  if(guard==8){c.m_inv.slots.erase(23);c.m_inv.slots[13]=&sword;}
  assert(!c.AscendPaladinEpic() && database.queries==0 && sword.GetID()==10099);
 }
}
''')

    def test_conditional_block_uses_real_equipment_eligibility(self):
        source=(native.CODE/'zone/bonuses.cpp').read_text()
        start=source.index('\tconst auto *primary = GetInv().GetItem(EQ::invslot::slotPrimary);')
        end=source.index('\n\tif (CanThisClassDualWield())',start)
        self.compile_run(r'''
#include "common/paladin_weapon_grip.h"
#include <cassert>
namespace EQ {namespace invslot {constexpr int slotPrimary=13,slotSecondary=14;}
namespace item {constexpr int ItemType1HSlash=0,ItemTypeShield=8;}}
struct Data {int ItemType=0; bool allowed=true;};
struct Item {unsigned id=810099;Data data;int required=0;bool common=true;
 bool IsClassCommon()const{return common;}const Data* GetItem()const{return &data;}
 unsigned GetID()const{return id;}int GetItemRequiredLevel(bool)const{return required;}};
struct Inventory {Item *p=nullptr,*s=nullptr;const Item *GetItem(int slot)const{return slot==13?p:s;}};
struct Bonuses {int ShieldBlock=0;};
struct Client {Inventory inv;bool client=true;int level=45;
 const Inventory &GetInv()const{return inv;}bool IsClient()const{return client;}
 Client* CastToClient(){return this;}bool CanEquipItem(const Data *d)const{return d->allowed;}int GetLevel()const{return level;}
 void Calc(Bonuses *b){b->ShieldBlock=0;
''' + source[start:end] + r'''
 }};
int main(){
 for(unsigned id : {5504u,205504u,405504u,605504u,11050u,211050u,411050u,611050u,10099u,810099u}){
  Item p,s;p.id=id;s.data.ItemType=8;Client c;c.inv={&p,&s};Bonuses b;
  for(int repeat=0;repeat<25;++repeat){c.Calc(&b);assert(b.ShieldBlock==NightcapPaladinGrip::FindProfile(id)->shield_block);}
 }
 for(int control=0;control<11;++control){
  Item p,s;s.data.ItemType=8;Client c;c.inv={&p,&s};Bonuses b;
  if(control==0)c.inv.p=nullptr;if(control==1)c.inv.s=nullptr;if(control==2)p.data.ItemType=1;
  if(control==3)s.data.ItemType=0;if(control==4)p.data.allowed=false;if(control==5)s.data.allowed=false;
  if(control==6)p.required=46;if(control==7)s.required=46;if(control==8)c.client=false;
  if(control==9)p.id=123;if(control==10)p.common=false;
  c.Calc(&b);assert(b.ShieldBlock==0);
 }
}
''')

    def test_forge_scope_binding_and_later_quest(self):
        capture=json.loads((native.ROOT/'docs/items/paladin-weapon-grip/balance/production-reference-complete.json').read_text())
        for path in ['ecommons/Epic_Forgemaster.pl','poknowledge/Epic_Forgemaster.pl']:
            source=(native.ROOT/'server-mods/quests'/path).read_text()
            baseline=capture['scripts'][path]['source'].replace('\r\n','\n')
            # Every other class retains its original complete payment path.
            code=lambda text: [l.split('#',1)[0].strip() for l in text[text.index('    my @id ='):].splitlines() if l.split('#',1)[0].strip()]
            self.assertEqual(code(source), code(baseline))
            self.assertNotIn('3  => [10099]',source)
            self.assertIn('$npc->ReturnHandinItems($client);',source)
            self.assertIn('$client->AscendPaladinEpic();',source)
        binding=(native.CODE/'zone/perl_client.cpp').read_text()
        self.assertIn('package.add("AscendPaladinEpic", &Perl_Client_AscendPaladinEpic)',binding)
        path='hohonora/#Irak_Altil.lua'
        self.assertEqual((native.ROOT/'server-mods/quests'/path).read_text(),capture['scripts'][path]['source'].replace('e.other:HasItem(10099) or','e.other:HasItem(10099) or e.other:HasItem(810099) or'))


if __name__=='__main__':unittest.main()
