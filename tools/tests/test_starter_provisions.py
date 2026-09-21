"""Exercise the native creation-only starter grant with bounded C++ dependencies."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from test_gameplay_policies import function


ROOT = Path(__file__).resolve().parents[2]
WORLD = ROOT / 'server-mods/code/world'


FIXTURE = r'''
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <map>
#include <memory>
#include <string>
#include <vector>
using uint32 = uint32_t;
using int16 = int16_t;
namespace EQ {
struct ItemData { uint32 ID=0, Classes=0, AC=0, Damage=0; };
struct ItemInstance {
 ItemData data;
 explicit ItemInstance(ItemData d):data(d){}
 const ItemData* GetItem() const { return &data; }
 int GetCharges() const { return 1; }
 uint32 GetColor() const { return 0; }
 uint32 GetAugmentItemID(int) const { return 0; }
 bool IsAttuned() const { return false; }
 uint32 GetOrnamentationIcon() const { return 0; }
 uint32 GetOrnamentationIDFile() const { return 0; }
 uint32 GetOrnamentHeroModel() const { return 0; }
 uint32 GetSerialNumber() const { return data.ID; }
};
namespace invslot {
 constexpr int EQUIPMENT_BEGIN=0, slotChest=1, slotPrimary=2, slotCursor=3;
 constexpr int BANK_BEGIN=5, BANK_END=5;
}
namespace invbag {
 constexpr int GENERAL_BAGS_BEGIN=4, CURSOR_BAG_END=4;
 constexpr int BANK_BAGS_BEGIN=6, BANK_BAGS_END=6;
}
namespace invaug { constexpr int SOCKET_BEGIN=0, SOCKET_END=5; }
struct InventoryProfile {
 std::map<int,ItemInstance> slots;
 int PutItem(int slot, const ItemInstance& item) { slots.insert_or_assign(slot,item); return slot; }
 const ItemInstance* GetItem(int slot) const {
  auto found=slots.find(slot); return found==slots.end()?nullptr:&found->second;
 }
};
}
struct PlayerProfile_Struct { uint32 class_=0, zone_id=1; char name[32]="Newchar"; };
struct SharedDatabase {
 std::map<uint32,EQ::ItemData> cache;
 EQ::ItemInstance* CreateItem(uint32 id,int) {
  auto found=cache.find(id); return found==cache.end()?nullptr:new EQ::ItemInstance(found->second);
 }
};
struct Result {
 bool success=true; int affected=1; size_t count=1;
 bool Success() const { return success; }
 int RowsAffected() const { return affected; }
 size_t RowCount() const { return count; }
};
struct Database {
 uint32 character_id=77;
 uint32 reserved_account=5, reserved_class=0, reserved_race=0;
 std::map<uint32,uint32> wallets;
 std::string query;
 int saved=0;
 int deleted=0;
 bool has_inventory=false, fail_reservation=false;
 bool reject_currency=false;
 uint32 GetCharacterID(const char*) const { return character_id; }
 bool SaveCharacterCreate(uint32, uint32, PlayerProfile_Struct*) { ++saved; return true; }
 bool DeleteCharacter(const std::string&) { ++deleted; return true; }
 Result QueryDatabase(const std::string& sql,bool) {
  query=sql;
  if(sql.find("SELECT id FROM character_data c WHERE ")==0) {
   if(fail_reservation) return {false,0,0};
   unsigned id=0,account=0;
   if(sql.find("WHERE id=")!=std::string::npos) {
    if(std::sscanf(sql.c_str(),"SELECT id FROM character_data c WHERE id=%u AND account_id=%u",&id,&account)!=2)
     return {false,0,0};
   } else {
    id=character_id;
    if(std::sscanf(sql.c_str(),"SELECT id FROM character_data c WHERE name='Newchar' AND account_id=%u",&account)!=1)
     return {false,0,0};
   }
   return {true,0,(id==character_id && account==reserved_account && reserved_class==0 &&
    reserved_race==0 && !wallets.count(id) && !has_inventory) ? size_t(1) : size_t(0)};
  }
  unsigned id=0,amount=0;
  if (std::sscanf(sql.c_str(),"INSERT INTO character_currency(id,platinum) VALUES(%u,%u)",&id,&amount)!=2 ||
      reject_currency || wallets.count(id)) return {false,0,0};
  wallets[id]=amount; return {true,1,1};
 }
} database;
struct InventoryRepository {
 struct Inventory {
  uint32 character_id=0, item_id=0, color=0, augment_one=0, augment_two=0,
   augment_three=0, augment_four=0, augment_five=0, augment_six=0,
   instnodrop=0, ornament_icon=0, ornament_idfile=0, ornament_hero_model=0, guid=0;
  int slot_id=0, charges=0;
 };
 static inline bool reject=false;
 static inline int insert_calls=0;
 static inline std::vector<Inventory> persisted;
 static Inventory NewEntity() { return {}; }
 static int InsertMany(Database&,const std::vector<Inventory>& rows) {
  ++insert_calls;
  if (reject) return 0;
  persisted=rows; return static_cast<int>(rows.size());
 }
};
struct ZoneStore {
 static ZoneStore* Instance() { static ZoneStore store; return &store; }
 const std::string& GetZoneName(uint32,bool) {
  static const std::string name="qeynos"; return name;
 }
};
namespace Strings {
 bool EqualFold(const std::string& a,const char* b) { return a==b; }
 std::string Escape(const std::string& value) { return value; }
}
namespace Zones { constexpr uint32 QEYNOS=1; }
namespace fmt {
 inline std::string one(const std::string& value) { return value; }
 inline std::string one(const char* value) { return value; }
 template<class T> std::string one(T value) { return std::to_string(value); }
 template<class... Args> std::string format(const char* pattern,const Args&... args) {
  std::string out=pattern;
  for(const auto& value:std::vector<std::string>{one(args)...}) {
   auto at=out.find("{}"); assert(at!=std::string::npos); out.replace(at,2,value);
  }
  return out;
 }
}
struct CharCreate_Struct { int marker=0; };
enum { OP_ApproveName=1 };
struct EQApplicationPacket {
 size_t size=0;
 unsigned char* pBuffer=nullptr;
 explicit EQApplicationPacket(int,size_t length):size(length),pBuffer(new unsigned char[length]{}){}
 ~EQApplicationPacket() { delete[] pBuffer; }
};
namespace EQ { namespace versions { constexpr uint32 maskTitaniumAndEarlier=1; } }
#define LogInfo(...) ((void)0)
#define safe_delete(value) do { delete value; value=nullptr; } while(0)
struct Client {
 char char_name[32]="Newchar";
 uint32 m_ClientVersionBit=0;
 bool StartInTutorial=false;
 PlayerProfile_Struct profile;
 EQ::InventoryProfile creation_inventory;
 int char_info_sent=0;
 uint32 GetAccountID() const { return 5; }
 void DumpPacket(const EQApplicationPacket*) {}
 void QueuePacket(const EQApplicationPacket*) {}
 void SendCharInfo() { ++char_info_sent; }
 bool OPCharCreate(char* name,CharCreate_Struct*) {
  std::strncpy(profile.name,name,sizeof(profile.name)-1);
  return StoreCharacter(GetAccountID(),&profile,&creation_inventory);
 }
 bool HandleCharacterCreatePacket(const EQApplicationPacket*);
 bool StoreCharacter(uint32,PlayerProfile_Struct*,EQ::InventoryProfile*);
};

// ACTUAL_STARTER_HEADER
// ACTUAL_STORE_CHARACTER
// ACTUAL_CREATE_HANDLER

int main() {
 SharedDatabase content;
 for (uint32 klass=1;klass<=16;++klass) {
  auto robe_id=998599u+klass, weapon_id=998619u+klass;
  content.cache[robe_id]={robe_id,1u<<(klass-1),10,0};
  content.cache[weapon_id]={weapon_id,1u<<(klass-1),0,5};
  PlayerProfile_Struct profile; profile.class_=klass;
  EQ::InventoryProfile inv;
  inv.PutItem(EQ::invslot::slotPrimary,EQ::ItemInstance({9997,0,0,1}));
  assert(NightcapStartingItems(content,profile,inv));
  assert(inv.GetItem(EQ::invslot::slotChest)->GetItem()->ID==robe_id);
  assert(inv.GetItem(EQ::invslot::slotPrimary)->GetItem()->ID==weapon_id);
 }
 PlayerProfile_Struct profile; profile.class_=1;
 EQ::InventoryProfile inv;
 for(uint32 legacy:{9997u,9998u,9999u,55623u}) {
  EQ::InventoryProfile defaults;
  defaults.PutItem(EQ::invslot::slotPrimary,EQ::ItemInstance({legacy,0,0,1}));
  assert(NightcapStartingItems(content,profile,defaults));
  assert(defaults.GetItem(EQ::invslot::slotChest)->GetItem()->ID==998600);
  assert(defaults.GetItem(EQ::invslot::slotPrimary)->GetItem()->ID==998620);
 }
 EQ::InventoryProfile empty;
 assert(NightcapStartingItems(content,profile,empty));
 inv.PutItem(EQ::invslot::slotPrimary,EQ::ItemInstance({9997,0,0,1}));
 EQ::InventoryProfile unusual;
 unusual.PutItem(EQ::invslot::slotPrimary,EQ::ItemInstance({76543,0,0,1}));
 assert(!NightcapStartingItems(content,profile,unusual));
 assert(!unusual.GetItem(EQ::invslot::slotChest));
 assert(unusual.GetItem(EQ::invslot::slotPrimary)->GetItem()->ID==76543);
 EQ::InventoryProfile occupied_chest;
 occupied_chest.PutItem(EQ::invslot::slotChest,EQ::ItemInstance({76544,0,1,0}));
 occupied_chest.PutItem(EQ::invslot::slotPrimary,EQ::ItemInstance({9997,0,0,1}));
 assert(!NightcapStartingItems(content,profile,occupied_chest));
 assert(occupied_chest.GetItem(EQ::invslot::slotChest)->GetItem()->ID==76544);
 assert(occupied_chest.GetItem(EQ::invslot::slotPrimary)->GetItem()->ID==9997);
 content.cache.erase(998620);
 assert(!NightcapStartingItems(content,profile,inv));
 assert(!inv.GetItem(EQ::invslot::slotChest));
 assert(inv.slots.at(EQ::invslot::slotPrimary).GetItem()->ID==9997);
 content.cache[998620]={998620,1,0,5};
 content.cache.erase(998600);
 assert(!NightcapStartingItems(content,profile,inv));
 assert(!inv.GetItem(EQ::invslot::slotChest));
 assert(inv.slots.at(EQ::invslot::slotPrimary).GetItem()->ID==9997);
 content.cache[998600]={998600,1,10,0};
 for (int defect=0;defect<4;++defect) {
  auto& robe=content.cache[998600]; auto& weapon=content.cache[998620];
  robe={998600,1,10,0}; weapon={998620,1,0,5};
  if(defect==0) robe.Classes=2;
  if(defect==1) weapon.Classes=2;
  if(defect==2) robe.AC=9;
  if(defect==3) weapon.Damage=0;
  assert(!NightcapStartingItems(content,profile,inv));
  assert(!inv.GetItem(EQ::invslot::slotChest));
  assert(inv.slots.at(EQ::invslot::slotPrimary).GetItem()->ID==9997);
 }
 profile.class_=0; assert(!NightcapStartingItems(content,profile,inv));
 profile.class_=17; assert(!NightcapStartingItems(content,profile,inv));

 Client client;
 profile.class_=1;
 database.character_id=81234;
 database.wallets.clear(); database.query.clear();
 InventoryRepository::reject=false;
 inv.slots.clear();
 inv.PutItem(EQ::invslot::slotChest,EQ::ItemInstance({998600,1,10,0}));
 inv.PutItem(EQ::invslot::slotPrimary,EQ::ItemInstance({998620,1,0,5}));
 assert(client.StoreCharacter(5,&profile,&inv));
 assert(database.wallets.at(81234)==100);
 assert(database.query=="INSERT INTO character_currency(id,platinum) VALUES(81234,100)");
 assert(InventoryRepository::persisted.size()==2);
 assert(InventoryRepository::persisted[0].character_id==81234);

 database.wallets[81234]=37;
 auto saved=database.saved, inserts=InventoryRepository::insert_calls;
 assert(!client.StoreCharacter(5,&profile,&inv));
 assert(database.wallets.at(81234)==37);
 assert(database.saved==saved && InventoryRepository::insert_calls==inserts);
 database.wallets.clear(); database.has_inventory=true;
 assert(!client.StoreCharacter(5,&profile,&inv));
 assert(database.saved==saved && InventoryRepository::insert_calls==inserts && database.wallets.empty());
 database.has_inventory=false; database.reserved_account=9;
 assert(!client.StoreCharacter(5,&profile,&inv));
 assert(database.saved==saved && InventoryRepository::insert_calls==inserts && database.wallets.empty());
 database.reserved_account=5; database.reserved_class=1;
 assert(!client.StoreCharacter(5,&profile,&inv));
 assert(database.saved==saved && InventoryRepository::insert_calls==inserts);
 database.reserved_class=0; database.reserved_race=1;
 assert(!client.StoreCharacter(5,&profile,&inv));
 assert(database.saved==saved && InventoryRepository::insert_calls==inserts);
 database.reserved_race=0; database.fail_reservation=true;
 assert(!client.StoreCharacter(5,&profile,&inv));
 assert(database.saved==saved && InventoryRepository::insert_calls==inserts);
 database.fail_reservation=false;
 database.wallets.clear(); database.query.clear();
 InventoryRepository::reject=true;
 assert(!client.StoreCharacter(5,&profile,&inv));
 assert(database.wallets.empty() && database.query.find("SELECT id FROM character_data")==0);
 InventoryRepository::reject=false;
 database.reject_currency=true;
 assert(!client.StoreCharacter(5,&profile,&inv));
 assert(database.wallets.empty());
 database.reject_currency=false;
 database.character_id=0; database.query.clear();
 assert(!client.StoreCharacter(5,&profile,&inv));
 assert(database.query.empty());

 // The real packet handler consumes the name before StoreCharacter and ignores replay.
 database.character_id=81234;
 database.wallets.clear(); database.saved=0; database.deleted=0;
 database.has_inventory=false; database.fail_reservation=false;
 InventoryRepository::insert_calls=0;
 Client session;
 session.creation_inventory=inv;
 EQApplicationPacket packet(0,sizeof(CharCreate_Struct));
 assert(session.HandleCharacterCreatePacket(&packet));
 assert(session.char_name[0]=='\0' && session.char_info_sent==1);
 assert(database.saved==1 && InventoryRepository::insert_calls==1 && database.wallets.at(81234)==100);
 assert(session.HandleCharacterCreatePacket(&packet));
 assert(database.saved==1 && InventoryRepository::insert_calls==1 && database.wallets.at(81234)==100);
 assert(database.deleted==0 && session.char_info_sent==1);
 // A stale approved name with an initialized reservation is consumed without deletion.
 Client stale;
 assert(stale.HandleCharacterCreatePacket(&packet));
 assert(stale.char_name[0]=='\0' && database.deleted==0);
 assert(database.saved==1 && InventoryRepository::insert_calls==1);
}
'''


class StarterProvisions(unittest.TestCase):
    def test_native_creation_grant(self):
        header = (WORLD / 'starter_provisions.h').read_text()
        client = (WORLD / 'client.cpp').read_text()
        store = function(client, 'bool Client::StoreCharacter(')
        handler = function(client, 'bool Client::HandleCharacterCreatePacket(')
        source = FIXTURE.replace('// ACTUAL_STARTER_HEADER', header).replace(
            '// ACTUAL_STORE_CHARACTER', store).replace('// ACTUAL_CREATE_HANDLER', handler)
        with tempfile.TemporaryDirectory(prefix='nightcap-starters-') as tmp:
            out = Path(tmp)
            (out / 'test.cpp').write_text(source)
            (out / 'build.cmd').write_text(
                '@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat" >nul || exit /b 1\n'
                'cl /nologo /EHsc /W4 /std:c++17 test.cpp /Fe:test.exe >build.log 2>&1\n'
                'exit /b %errorlevel%\n')
            build = subprocess.run(['cmd', '/d', '/c', str(out / 'build.cmd')], cwd=out)
            self.assertEqual(build.returncode, 0, (out / 'build.log').read_text())
            run = subprocess.run([str(out / 'test.exe')], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)


if __name__ == '__main__':
    unittest.main()
