"""Execute the production grip policy and instance update with native C++."""
import unittest
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import test_free_trade as native


class PaladinWeaponGripTests(unittest.TestCase):
    compile_run = native.FreeTradeTests.compile_run

    def test_actual_packet_gate_rejects_slot_aliases(self):
        source = (native.CODE/'zone/client_packet.cpp').read_text(encoding='utf-8')
        cast = native.body(source, 'void Client::Handle_OP_CastSpell(')
        cast_gate = native.body(cast, 'if (slot == CastingSlot::Item || slot == CastingSlot::PotionBelt)')
        verify = native.body(source, 'void Client::Handle_OP_ItemVerifyRequest(')
        verify_gate = native.body(verify, 'if (slot_id < 0 || slot_id > 32767)')
        self.compile_run(r'''
#include "common/paladin_weapon_grip.h"
#include <cassert>
#include <cstdint>
using uint64=uint64_t;using int16=int16_t;
enum class CastingSlot {Gem,Item,PotionBelt};
#define LogDebug(...) ((void)0)
struct Item {unsigned id=5504;unsigned GetID()const{return id;}};
struct Inventory {
 Item item;int lookups=0;
 const Item *GetItem(int16 slot){++lookups;return slot==13?&item:nullptr;}
};
struct Client {
 Inventory m_inv;int enables=0,casts=0,toggles=0;
 void SendSpellBarEnable(int){++enables;}
 void Cast(int64_t encoded,CastingSlot slot){
  struct Packet {int64_t inventoryslot;int spell_id=288;} packet{encoded};
  auto *castspell=&packet;
''' + cast_gate + r'''
  ++casts;
 }
 void Verify(int32_t slot_id){
''' + verify_gate + r'''
  ++toggles;
 }
};
int main(){
 for(auto mode : {CastingSlot::Item,CastingSlot::PotionBelt}) {
  for(int64_t bad : {-1LL,32768LL,65549LL,2147483647LL,4294967295LL}) {
   Client c;c.Cast(bad,mode);assert(c.enables==1 && !c.casts && !c.m_inv.lookups);
   if(bad<=2147483647LL){c.Verify(int32_t(bad));assert(!c.toggles);}
  }
  Client c;c.Cast(13,mode);assert(c.enables==1 && !c.casts && c.m_inv.lookups==1);
  c.Verify(13);assert(c.toggles==1);
  c.m_inv.item.id=5379;c.Cast(13,mode);assert(c.casts==1);
 }
 Client gem;gem.Cast(-1,CastingSlot::Gem);assert(gem.casts==1 && !gem.m_inv.lookups);
}
''')

    def test_actual_handler_guards_commit_and_publication(self):
        source = (native.CODE/'zone/inventory.cpp').read_text(encoding='utf-8')
        handler = native.body(source, 'bool Client::TogglePaladinWeaponGrip(')
        fixture = (native.ROOT/'tools/tests/fixtures/paladin_weapon_grip.cpp').read_text(encoding='utf-8')
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)/'queries.sql'
            fixture = '#include <fstream>\n'+fixture.replace('int main() {', 'int main() {\nstd::ofstream queries(R"PATH('+output.as_posix()+')PATH");')
            self.compile_run(fixture.replace('// PRODUCTION_HANDLER', handler).replace('std::cout', 'queries'))
            queries = output.read_text().splitlines()
        self.verify_sql(queries)

    def verify_sql(self, queries, ascend=False):
        columns = ['character_id','slot_id','item_id','charges','color','augment_one','augment_two',
                   'augment_three','augment_four','augment_five','augment_six','instnodrop','custom_data',
                   'ornament_icon','ornament_idfile','ornament_hero_model','guid']
        row = [42,13,5504,32767,7,0,0,0,0,0,0,1,'',3,4,5,9]
        if ascend: row[2] = 10099
        if os.environ.get('NIGHTCAP_GRIP_DB_TEST') == '1':
            import pymysql
            details = json.loads(subprocess.check_output(['docker','inspect','akk-stack-mariadb-1'], text=True))[0]
            env = dict(v.split('=',1) for v in details['Config']['Env'] if '=' in v)
            password = env.get('MARIADB_ROOT_PASSWORD') or env.get('MYSQL_ROOT_PASSWORD')
            db = pymysql.connect(host='127.0.0.1',port=3307,user='root',password=password,database='peq',autocommit=True)
            self.addCleanup(db.close)
            cur = db.cursor()
            # Session-local shadow table. No real inventory rows are read/written.
            cur.execute('SHOW CREATE TABLE peq.inventory')
            definition = cur.fetchone()[1]
            self.assertTrue(definition.startswith('CREATE TABLE `inventory`'))
            cur.execute(definition.replace('CREATE TABLE `inventory`', 'CREATE TEMPORARY TABLE `inventory`', 1))
            placeholders = ','.join(['%s']*len(columns))
        else:
            db = sqlite3.connect(':memory:')
            self.addCleanup(db.close)
            cur = db.cursor()
            cur.execute('CREATE TABLE inventory ('+','.join(c+(' TEXT' if c=='custom_data' else ' INTEGER') for c in columns)+')')
            placeholders = ','.join(['?']*len(columns))
            queries = [q.replace('BINARY ', '') for q in queries]
        insert = 'INSERT INTO inventory ('+','.join(columns)+') VALUES ('+placeholders+')'
        select = 'SELECT '+','.join(columns)+' FROM inventory'
        def seed(values):
            cur.execute('DELETE FROM inventory')
            cur.execute(insert, values)
        for index, query in enumerate(queries):
            baseline = list(row)
            baseline[12] = '' if index==0 else 'nightcap_paladin_grip^1^'
            after = list(baseline)
            after[12] = 'nightcap_paladin_grip^1^' if index==0 else ''
            if ascend:
                after[2] = 810099
                after[12] = baseline[12]
            seed(baseline)
            cur.execute(query); self.assertEqual(cur.rowcount, 1)
            cur.execute(select); self.assertEqual(tuple(cur.fetchone()), tuple(after))
            cur.execute(query); self.assertEqual(cur.rowcount, 0, 'replay must not change grip again')
            for field in range(len(columns)):
                drift = list(baseline)
                drift[field] = 'NIGHTCAP_PALADIN_GRIP^1^' if field==12 else drift[field]+1
                seed(drift);cur.execute(query);self.assertEqual(cur.rowcount, 0, columns[field])
                cur.execute(select);self.assertEqual(tuple(cur.fetchone()), tuple(drift))
        seed(row[:12]+[None]+row[13:])
        cur.execute(queries[0]);self.assertEqual(cur.rowcount, 1, 'legacy NULL metadata')

    def test_epic_exchange_exact_saved_instance(self):
        source=(native.ROOT/'tools/tests/fixtures/paladin_weapon_grip.cpp').read_text().split('// PRODUCTION_HANDLER')[0]
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'exchange.sql'
            self.compile_run('#include <fstream>\n'+source+r'''
int main(){
 Item item;item.id=10099;item.charges=-1;
 std::ofstream out(R"PATH('''+output.as_posix()+r''')PATH");
 out << NightcapPaladinGrip::AscendSQL(42,13,item) << '\n';
 item.metadata="nightcap_paladin_grip^1^";
 out << NightcapPaladinGrip::AscendSQL(42,13,item) << '\n';
 item.id=810099;assert(NightcapPaladinGrip::AscendSQL(42,13,item).empty());
 item.id=10099;item.metadata="foreign^data^";assert(NightcapPaladinGrip::AscendSQL(42,13,item).empty());
}
''')
            self.verify_sql(output.read_text().splitlines(),ascend=True)

    def test_packet_routing_and_load_save_contract(self):
        source = (native.CODE/'zone/client_packet.cpp').read_text(encoding='utf-8')
        verify = native.body(source, 'void Client::Handle_OP_ItemVerifyRequest(')
        self.assertLess(verify.index('TogglePaladinWeaponGrip(slot_id)'), verify.index('spell_id = item->Click.Effect'))
        self.assertLess(verify.index('slot_id > 32767'), verify.index('TogglePaladinWeaponGrip(slot_id)'))
        cast = native.body(source, 'void Client::Handle_OP_CastSpell(')
        self.assertLess(cast.index('NightcapPaladinGrip::Supported'), cast.index('/* Memorized Spell */'))
        self.assertNotIn('TogglePaladinWeaponGrip', cast)
        instance = (native.CODE/'common/item_instance.cpp').read_text(encoding='utf-8')
        for signature in ('EQ::ItemInstance::ItemInstance(const ItemData*', 'EQ::ItemInstance::ItemInstance(SharedDatabase *'):
            self.assertIn('RefreshPaladinWeaponGrip()', native.body(instance, signature))
        for arg in ('const std::string& value', 'int value', 'float value', 'bool value'):
            self.assertIn('RefreshPaladinWeaponGrip()', native.body(instance, 'void EQ::ItemInstance::SetCustomData(const std::string& identifier, '+arg))
        db = (native.CODE/'common/shareddb.cpp').read_text(encoding='utf-8')
        self.assertIn('inst->SetCustomDataString(row.custom_data)', db)
        self.assertIn('e.custom_data         = inst->GetCustomDataString()', db)
        codec = (native.CODE/'common/patches/rof2.cpp').read_text(encoding='utf-8')
        self.assertIn('inst->GetUnscaledItem()', codec)
        projection = codec[codec.index('if (NightcapPaladinGrip::Supported(item->ID))'):]
        projection = projection[:projection.index('\n\t\t}')]
        self.assertIn('hdr.charges = 0xFFFFFFFF;', projection)
        self.assertIn('hdr.last_cast_time = 0;', projection)
        self.assertIn('ices.max_charges = NightcapPaladinGrip::Supported(item->ID) ? -1 : item->MaxCharges;', codec)

    def test_policy_and_owned_instance_projection(self):
        source = (native.CODE/'common/item_instance.cpp').read_text(encoding='utf-8')
        refresh = native.body(source, 'void EQ::ItemInstance::RefreshPaladinWeaponGrip(')
        methods = '\n'.join(native.body(source, signature) for signature in (
            'std::string EQ::ItemInstance::GetCustomDataString(',
            'void EQ::ItemInstance::SetCustomDataString(',
            'void EQ::ItemInstance::SetCustomData(const std::string& identifier, const std::string& value)',
            'void EQ::ItemInstance::DeleteCustomData('))
        split = native.body((native.ROOT/'tools/tests/fixtures/bazaar_custom_data.inc').read_text(),
                            'std::vector<std::string> Strings::Split(')
        deletion = native.body((native.CODE/'common/inventory_profile.cpp').read_text(),
                               'bool EQ::InventoryProfile::DeleteItem(')
        self.compile_run(r'''
#include "common/paladin_weapon_grip.h"
#include <cassert>
#include <cstring>
#include <map>
#include <string>
#include <vector>
using int16 = int16_t;
namespace Strings {std::vector<std::string> Split(const std::string&,const std::string&);}
namespace EQ {
struct ItemData {
 int Accuracy=0, Mana=0, AStr=0, AWis=0, HeroicStr=0, HeroicWis=0, HealAmt=0, SpellDmg=0;
 struct {int Level2=50;} Proc;
 unsigned ID = 5504; int ItemType = 1, Damage = 23, Delay = 45;
 struct { int Effect = 13, Type = 3, Level = 1, Level2 = 1; } Click;
 char ClickName[65] = "Complete Heal";
 int MaxCharges = 5, CastTime = 10000, CastTime_ = 10000, RecastDelay = 0, RecastType = -1;
};
struct ItemInstance {
 const ItemData *m_item; ItemData *m_scaledItem = nullptr;
 std::map<std::string, std::string> m_custom_data;
 int16 charges=1;
 int16 GetCharges() const {return charges;}
 void SetCharges(int16 value) {charges=value;}
 const ItemData *GetItem() const {return m_item;}
 bool IsStackable() const {return false;}
 bool IsExpendable() const {return m_item->Click.Type==3;}
 void RefreshPaladinWeaponGrip();
 std::string GetCustomDataString() const;
 void SetCustomDataString(const std::string&);
 void SetCustomData(const std::string&,const std::string&);
 void DeleteCustomData(const std::string&);
};
struct InventoryProfile {
 ItemInstance *stored=nullptr; static inline int discarded=0;
 ItemInstance *PopItem(int16) {auto *p=stored;stored=nullptr;return p;}
 void _PutItem(int16,ItemInstance *p) {stored=p;}
 static void MarkDirty(ItemInstance*) {++discarded;}
 bool DeleteItem(int16,int16);
};
}
''' + split + methods + refresh + deletion + r'''
int main() {
 using namespace NightcapPaladinGrip;
 struct Expected {unsigned id; int damage,delay,one_damage;};
 for (auto row : {Expected{5504,23,45,13}, {205504,31,45,18}, {405504,38,45,22}, {605504,46,45,26},
                  {11050,33,44,15}, {211050,44,44,20}, {411050,55,44,25}, {611050,66,44,30},
                  {10099,64,40,32}, {810099,72,40,36}}) {
   assert(Supported(row.id));
   EQ::ItemData item; item.ID=row.id;item.Damage=row.damage;item.Delay=row.delay;
   EQ::ItemInstance inst{&item};
   inst.RefreshPaladinWeaponGrip();
   assert(item.ItemType==1 && item.Damage==row.damage && item.Delay==row.delay);
   assert(item.Click.Effect==ClickSpell && item.Click.Type==5 && item.MaxCharges==5);
   assert(std::strcmp(item.ClickName,"Toggle Weapon Grip")==0);
   assert(item.Accuracy==FindProfile(row.id)->accuracy);
   if(row.id==10099) assert(item.Mana==50 && item.AStr==30 && item.AWis==30 && item.HeroicStr==8 && item.HeroicWis==8 && item.HealAmt==30 && item.SpellDmg==15 && item.Proc.Level2==45);
   if(row.id==810099) assert(item.HeroicWis==10 && item.HealAmt==35 && item.Proc.Level2==45);
   const auto original=item;
   for (int cycle=0;cycle<25;++cycle) {
    inst.SetCustomData(Key,std::string("1"));
    inst.RefreshPaladinWeaponGrip();
    assert(item.ItemType==0 && item.Damage==row.one_damage && item.Delay==30);
    auto projected=original;projected.ItemType=0;projected.Damage=row.one_damage;projected.Delay=30;
    assert(std::memcmp(&item,&projected,sizeof(item))==0);
    EQ::ItemData reload=original;
    EQ::ItemInstance loaded{&reload}; loaded.RefreshPaladinWeaponGrip();
    loaded.SetCustomDataString(inst.GetCustomDataString()); // DB/Bazaar reconstruction
    assert(reload.ItemType==0 && reload.Damage==row.one_damage && reload.Delay==30);
    EQ::ItemData copied=item; EQ::ItemInstance clone{&copied}; clone.m_custom_data=inst.m_custom_data;
    clone.DeleteCustomData(Key);
    assert(std::memcmp(&copied,&original,sizeof(item))==0);
    inst.DeleteCustomData(Key);
    assert(std::memcmp(&item,&original,sizeof(item))==0 && inst.GetCustomDataString().empty());
   }
 }
 assert(Supported(10099) && Supported(810099));
 for(unsigned id : {0u,5503u,5505u,210099u,410099u,610099u,810100u,805504u,811050u,1010099u,4294967295u}) assert(!Supported(id));
 EQ::ItemData other; other.ID=5379; EQ::ItemInstance unrelated{&other};
 unrelated.m_custom_data[Key]="1"; unrelated.RefreshPaladinWeaponGrip();
 assert(other.ItemType==1 && other.Click.Effect==13 && other.MaxCharges==5);
 EQ::ItemInstance empty{nullptr}; empty.RefreshPaladinWeaponGrip();
 assert(PlainMetadata("") && PlainMetadata(std::string(Key)+"^1^"));
 assert(!PlainMetadata("other^value^") && !PlainMetadata(std::string(Key)+"^2^"));
 for(unsigned id : {11050u,211050u,411050u,611050u,10099u,810099u}) {
  for(bool one_handed : {false,true}) {
   EQ::ItemData sword; sword.ID=id;sword.MaxCharges=0;
   EQ::ItemInstance inst{&sword};inst.RefreshPaladinWeaponGrip();
   if(one_handed)inst.SetCustomData(Key,std::string("1"));
   EQ::InventoryProfile inv;inv.stored=&inst;
   assert(inv.DeleteItem(23,1) && inv.stored==nullptr);
  }
 }
}
''')


if __name__ == '__main__':
    unittest.main()
