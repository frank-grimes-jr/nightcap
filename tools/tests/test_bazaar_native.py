"""Compile actual native quote/purchase guards with a bounded Client fixture."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[2]

def function(source,signature):
    start=source.index(signature);brace=source.index('{',start);depth=1;end=brace+1
    while depth:
        depth+=(source[end]=='{')-(source[end]=='}');end+=1
    return source[start:end]

FIXTURE=r'''
#include "common/bazaar_escrow.h"
#include <cassert>
#include <cstring>
#include <map>
#include <string>
#include <vector>
using uint32=uint32_t;using uint64=uint64_t;
using NightcapBazaar::Number;
uint64 clock_value=100;uint64 Now(){return clock_value;}
constexpr unsigned BazaarByDirectToInventory=2;
namespace Chat {constexpr int Yellow=1;}
namespace EQ {namespace versions {enum class ClientVersion {Old,RoF2};}}
struct TraderBuy_Struct {unsigned trader_id=NightcapBazaar::BrokerID,method=2,price=1000,item_id=1001,quantity=1;char serial_number[17]="0000000000000001";};
struct EQApplicationPacket {unsigned size;unsigned char *pBuffer;};
struct BazaarSearchResultsFromDB_Struct {unsigned trader_id,serial_number,cost,item_id,charges;bool stackable;};
struct Client {
 struct BazaarQuote {uint32 price,item_id,quantity;uint64 deadline;};
 std::map<uint32,BazaarQuote> m_bazaar_quotes;
 bool safe=true,commit=true;int failures=0,success=0,calls=0;NightcapBazaar::Request captured{};
 EQ::versions::ClientVersion version=EQ::versions::ClientVersion::RoF2;
 bool BazaarSessionReady(){return safe;}
 EQ::versions::ClientVersion ClientVersion(){return version;}
 void TradeRequestFailed(const EQApplicationPacket*){++failures;}
 void ReturnTraderReq(const EQApplicationPacket*,unsigned,unsigned){++success;}
 void Message(int,const char*){}
 bool CompleteBazaarRequest(const NightcapBazaar::Request &request){++calls;captured=request;return commit;}
 bool HandleBazaarPurchase(const EQApplicationPacket*);
 void RememberBazaarResults(const std::vector<BazaarSearchResultsFromDB_Struct>&);
};
'''
CASES=r'''
int main(){
 TraderBuy_Struct input;EQApplicationPacket packet{sizeof(input),reinterpret_cast<unsigned char*>(&input)};
 auto fresh=[](){Client c;c.RememberBazaarResults({{NightcapBazaar::BrokerID,1,1000,1001,5,true}});return c;};
 {
  auto c=fresh();assert(c.HandleBazaarPurchase(&packet));assert(c.calls==1&&c.success==1&&!c.failures);
  assert(c.captured.op==NightcapBazaar::Operation::Buy&&c.captured.listing==1&&c.captured.quantity==1&&c.captured.unit_price==1000);
  assert(c.m_bazaar_quotes.empty());assert(c.HandleBazaarPurchase(&packet));assert(c.calls==1&&c.failures==1);
 }
 for(unsigned condition=0;condition<12;++condition){
  auto c=fresh();input=TraderBuy_Struct{};packet.size=sizeof(input);
  switch(condition){
   case 0:input.price=999;break;case 1:input.item_id=1002;break;case 2:input.quantity=0;break;
   case 3:input.quantity=6;break;case 4:input.serial_number[16]='x';break;
   case 5:std::strcpy(input.serial_number,"1;DROP TABLE");break;
   case 6:c.m_bazaar_quotes[1].deadline=99;break;case 7:c.safe=false;break;
   case 8:c.version=EQ::versions::ClientVersion::Old;break;case 9:c.m_bazaar_quotes.clear();break;
   case 10:input.method=1;break;case 11:input.method=99;break;
  }
  assert(c.HandleBazaarPurchase(&packet));assert(c.failures==1&&c.calls==0&&c.success==0);
 }
 input=TraderBuy_Struct{};
 {auto c=fresh();packet.size=sizeof(input)-1;assert(!c.HandleBazaarPurchase(&packet));assert(!c.calls&&!c.failures);packet.size=sizeof(input);}
 {auto c=fresh();input.trader_id=45;assert(!c.HandleBazaarPurchase(&packet));assert(!c.calls&&!c.failures);input=TraderBuy_Struct{};}
 {auto c=fresh();c.commit=false;assert(c.HandleBazaarPurchase(&packet));assert(c.failures==1&&c.calls==1&&!c.success&&c.m_bazaar_quotes.empty());}
 {auto c=fresh();c.RememberBazaarResults({{77,2,1000,1002,1,false}});assert(c.m_bazaar_quotes.empty());}
 {auto c=fresh();input.quantity=5;assert(c.HandleBazaarPurchase(&packet));assert(c.captured.quantity==5&&c.success==1);}
}
'''

RESTORE_FIXTURE = r'''
#include "common/bazaar_escrow.h"
#include <array>
#include <cassert>
#include <memory>
#include <map>
#include <string>
using namespace NightcapBazaar;
using uint32=uint32_t;using uint8=uint8_t;using uint16=uint16_t;using int16=int16_t;
namespace Strings {std::vector<std::string> Split(const std::string&,const std::string&);}
namespace EQ {
namespace invslot {constexpr int slotCursor=33;}
namespace invbag {constexpr int SLOT_COUNT=10;}
namespace invaug {constexpr unsigned SOCKET_COUNT=6;}
struct ItemInstance {
 unsigned id=1001,color=0,icon=0,file=0;int charges=1,hero=0;bool attuned=false;
 std::array<unsigned,6> aug{};std::map<std::string,std::string> m_custom_data;
 bool IsClassBag()const{return false;}
 bool IsStackable()const{return id==1002;}
 const ItemInstance *GetItem(unsigned)const{return nullptr;}
 unsigned GetID()const{return id;}int GetCharges()const{return charges;}unsigned GetColor()const{return color;}
 unsigned GetAugmentItemID(unsigned i)const{return aug[i];}bool IsAttuned()const{return attuned;}
 std::string GetCustomDataString() const;unsigned GetOrnamentationIcon()const{return icon;}
 unsigned GetOrnamentationIDFile()const{return file;}int GetOrnamentHeroModel()const{return hero;}int GetSerialNumber()const{return 999;}
 void SetCharges(int v){charges=v;}void SetColor(unsigned v){color=v;}void SetAttuned(bool v){attuned=v;}
 void SetCustomDataString(const std::string&);
 void SetCustomData(const std::string&,const std::string&);void DeleteCustomData(const std::string&);void SetOrnamentIcon(unsigned v){icon=v;}
 void SetOrnamentationIDFile(unsigned v){file=v;}void SetOrnamentHeroModel(int v){hero=v;}
};
}
struct DB {
 EQ::ItemInstance *CreateItem(unsigned id,int charges,unsigned a,unsigned b,unsigned c,unsigned d,unsigned e,unsigned f){
  if(id==9999)return nullptr;
  auto item=new EQ::ItemInstance;item->id=id;item->charges=charges==0?1:charges;item->aug={a,b,c,d,e,f};
  for(auto &augment:item->aug)if(augment==9999)augment=0;
  return item;
 }
} database;
struct Inventory {
 std::vector<EQ::ItemInstance> cursor{EQ::ItemInstance{}};
 auto cursor_cbegin()const{return cursor.cbegin();}auto cursor_cend()const{return cursor.cend();}
 const EQ::ItemInstance *GetItem(int)const{return &cursor.front();}
};
struct Client {Inventory inv;Inventory &GetInv(){return inv;}unsigned CharacterID()const{return 1;}};
bool Transferable(const EQ::ItemInstance*){return true;}
'''
RESTORE_CASES = r'''
int main(){
 Row row={"1","33","1001","0","123","201","0","0","0","0","0","1","7461675E726172655E","72","73","-7","123456"};
 auto restored=Restore(row);assert(restored&&restored->GetCharges()==0);
 assert(SameItems({row},{Snapshot(1,33,*restored)}));
 row[3]="32767";restored=Restore(row);assert(restored&&restored->GetCharges()==-1);
 row[5]="9999";assert(!Restore(row));
 row[5]="201";row[2]="9999";assert(!Restore(row));
 Client client;Rows cursor;
 assert(CursorSnapshot(&client,cursor));
 client.inv.cursor.front().SetCustomData("a",std::string("1"));cursor.clear();
 assert(CursorSnapshot(&client,cursor));assert(Restore(cursor.front()));
 client.inv.cursor.front().SetCustomData("b",std::string("2"));cursor.clear();
 assert(client.inv.cursor.front().GetCustomDataString()=="a^1^^b^2^");
 assert(!Restore(Snapshot(1,33,client.inv.cursor.front())));
 assert(!CursorSnapshot(&client,cursor)); // never escrow unreconstructible metadata
 client.inv.cursor.front()=EQ::ItemInstance{};client.inv.cursor.front().id=1002;
 client.inv.cursor.front().charges=32766;cursor.clear();assert(CursorSnapshot(&client,cursor));
 client.inv.cursor.front().charges=32767;cursor.clear();assert(!CursorSnapshot(&client,cursor));
 client.inv.cursor.front().charges=0;cursor.clear();assert(!CursorSnapshot(&client,cursor));

}
'''


POST_FIXTURE=r"""
#include "common/bazaar_escrow.h"
#include <cassert>
#include <string>
using uint32=uint32_t;using uint64=uint64_t;
uint64 clock_value=100;uint64 Now(){return clock_value;}
namespace Chat {constexpr int Yellow=1;}
namespace EQ {namespace invslot {constexpr int slotCursor=33;}}
namespace NightcapLoot {std::string NewDropID(){return "abcd-1234";}}
struct Item {const char *Name="Dagger";};
struct Instance {Item data;int charges=3;bool stackable=true;bool IsStackable()const{return stackable;}int GetCharges()const{return charges;}const Item *GetItem()const{return &data;}};
struct Inventory {Instance item;const Instance *GetItem(int)const{return &item;}};
struct Client {
 Inventory m_inv;NightcapBazaar::Request m_bazaar_post;std::string m_bazaar_confirmation;uint64 m_bazaar_confirmation_deadline=0;
 bool eligible=true,commit=true;unsigned completed=0,messages=0;
 unsigned CharacterID()const{return 23;}
 template<class... A>void Message(int,const char*,A...){++messages;}
 bool CompleteBazaarRequest(const NightcapBazaar::Request &){++completed;return commit;}
 bool PrepareBazaarPost(uint64,bool quiet=false);bool ConfirmBazaarPost(const std::string&);
};
bool CursorSnapshot(Client *client,NightcapBazaar::Rows &rows){if(!client->eligible)return false;rows={{"exact cursor snapshot"}};return true;}
"""
POST_CASES=r"""
int main(){
 {Client c;assert(c.PrepareBazaarPost(1,true));assert(!c.messages&&!c.completed);assert(c.m_bazaar_post.unit_price==1000&&c.m_bazaar_post.quantity==3&&c.m_bazaar_post.character==23);assert(c.m_bazaar_confirmation_deadline==160);
 assert(!c.ConfirmBazaarPost("wrong")&&!c.completed);assert(c.ConfirmBazaarPost("abcd-1234")&&c.completed==1);assert(!c.ConfirmBazaarPost("abcd-1234")&&c.completed==1);}
 {Client c;assert(c.PrepareBazaarPost(1));assert(c.messages==1);clock_value=161;assert(!c.ConfirmBazaarPost("abcd-1234")&&!c.completed);clock_value=100;}
 for(unsigned mode=0;mode<5;++mode){Client c;assert(c.PrepareBazaarPost(1,true));uint64 price=1;
 switch(mode){case 0:price=0;break;case 1:price=4294968;break;case 2:c.eligible=false;break;case 3:c.m_inv.item.charges=0;break;case 4:price=2000000;break;}
 assert(!c.PrepareBazaarPost(price,true));assert(c.m_bazaar_confirmation.empty());assert(!c.ConfirmBazaarPost("abcd-1234")&&!c.completed);}
 {Client c;c.commit=false;assert(c.PrepareBazaarPost(1,true));assert(!c.ConfirmBazaarPost("abcd-1234"));assert(c.completed==1&&c.m_bazaar_confirmation.empty());assert(!c.ConfirmBazaarPost("abcd-1234")&&c.completed==1);}
 {Client c;c.m_inv.item.stackable=false;c.m_inv.item.charges=0;assert(c.PrepareBazaarPost(4294967,true));assert(c.m_bazaar_post.quantity==1);}
}
"""

class NativeGuards(unittest.TestCase):
    def test_native_post_quote_confirmation(self):
        source=(ROOT/'server-mods/code/zone/client_bazaar.cpp').read_text()
        self.compile_run(POST_FIXTURE+'\n'+function(source,'bool Client::PrepareBazaarPost(')+'\n'+function(source,'bool Client::ConfirmBazaarPost(')+POST_CASES)

    def test_current_grip_projection_through_bazaar_restore(self):
        source=(ROOT/'server-mods/code/zone/client_bazaar.cpp').read_text()
        instance=(ROOT/'server-mods/code/common/item_instance.cpp').read_text()
        fixture=RESTORE_FIXTURE.replace('#include <array>', '#include <array>\n#include <cstring>\n#include "common/paladin_weapon_grip.h"')
        fixture=fixture.replace('struct ItemInstance {', '''struct ItemData {unsigned ID=5504,Damage=23;uint8_t Delay=45;int ItemType=1;struct {int Effect=13,Type=3,Level=1,Level2=1;} Click;char ClickName[65]={};int CastTime=0,CastTime_=0,RecastDelay=0,RecastType=0;int Accuracy=0,Mana=0,AStr=0,AWis=0,HeroicStr=0,HeroicWis=0,HealAmt=0,SpellDmg=0;struct {int Level2=50;} Proc;};
struct ItemInstance {
 ItemData owned;const ItemData *m_item=&owned;ItemData *m_scaledItem=nullptr;void RefreshPaladinWeaponGrip();
''')
        fixture=fixture.replace('item->id=id;item->charges=', 'item->id=id;item->owned.ID=id;item->RefreshPaladinWeaponGrip();item->charges=')
        split=function((ROOT/'tools/tests/fixtures/bazaar_custom_data.inc').read_text(), 'std::vector<std::string> Strings::Split(')
        methods='\n'.join(function(instance,x) for x in ['std::string EQ::ItemInstance::GetCustomDataString(', 'void EQ::ItemInstance::SetCustomDataString(', 'void EQ::ItemInstance::SetCustomData(const std::string& identifier, const std::string& value)', 'void EQ::ItemInstance::DeleteCustomData(', 'void EQ::ItemInstance::RefreshPaladinWeaponGrip('])
        restore='\n'.join(function(source,x) for x in ['std::string Hex(', 'std::string Unhex(', 'Row Snapshot(', 'std::unique_ptr<EQ::ItemInstance> Restore('])
        cases=r'''
int main(){
 for(unsigned id:{5504u,205504u,405504u,605504u,11050u,211050u,411050u,611050u,10099u,810099u})for(bool grip:{false,true}){
  const std::string metadata=grip?"nightcap_paladin_grip^1^":"";
  Row row={"1","33",std::to_string(id),"0","123","201","0","0","0","0","0","1",Hex(metadata),"72","73","-7","123456"};
  auto restored=Restore(row);assert(restored);assert(restored->GetID()==id&&restored->GetCharges()==0);
  assert(restored->GetCustomDataString()==metadata&&restored->m_item->ItemType==(grip?0:1));
  const auto &profile=*NightcapPaladinGrip::FindProfile(id);
  assert(restored->m_item->Damage==(grip?profile.one_hand_damage:profile.two_hand_damage));
  assert(restored->m_item->Delay==(grip?profile.one_hand_delay:profile.two_hand_delay));
  assert(SameItems({row},{Snapshot(1,33,*restored)}));
  row[0]="2";auto buyer=Restore(row);assert(buyer&&buyer->m_item->ItemType==(grip?0:1));
  assert(SameItems({row},{Snapshot(2,33,*buyer)}));
  buyer->SetCustomData(NightcapPaladinGrip::Key,std::string("1"));assert(buyer->m_item->ItemType==0);
  buyer->DeleteCustomData(NightcapPaladinGrip::Key);assert(buyer->m_item->ItemType==1&&buyer->GetCustomDataString().empty());
  assert(buyer->m_item->Damage==profile.two_hand_damage&&buyer->m_item->Delay==profile.two_hand_delay);
 }
}
'''
        self.compile_run(fixture+split+methods+restore+cases)

    def test_exact_instance_reconstruction(self):
        source=(ROOT/'server-mods/code/zone/client_bazaar.cpp').read_text()
        code=RESTORE_FIXTURE+'\n'+(ROOT/'tools/tests/fixtures/bazaar_custom_data.inc').read_text(encoding='utf-8')+'\n'+'\n'.join(function(source,x) for x in ['std::string Hex(','std::string Unhex(','Row Snapshot(','std::unique_ptr<EQ::ItemInstance> Restore(','bool CursorSnapshot('])+RESTORE_CASES
        self.compile_run(code)

    def test_real_purchase_guards(self):
        source=(ROOT/'server-mods/code/zone/client_bazaar.cpp').read_text()
        code=FIXTURE+'\n'+function(source,'void Client::RememberBazaarResults(')+'\n'+function(source,'bool Client::HandleBazaarPurchase(')+'\n'+CASES
        self.compile_run(code)

    def compile_run(self,code):
        with tempfile.TemporaryDirectory(prefix='nightcap-bazaar-guards-') as temp:
            out=Path(temp);(out/'test.cpp').write_text(code)
            if os.name=='nt':
                (out/'build.cmd').write_text('@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars64.bat" >nul || exit /b 1\n'
                    f'cl /nologo /EHsc /W4 /std:c++17 /I"{ROOT / "server-mods/code"}" test.cpp /Fe:test.exe >build.log 2>&1\nexit /b %errorlevel%\n')
                result=subprocess.run(['cmd','/d','/c',str(out/'build.cmd')],cwd=out)
                self.assertEqual(result.returncode,0,(out/'build.log').read_text());exe=out/'test.exe'
            else:
                exe=out/'test';subprocess.run(['c++','-std=c++17','-I',str(ROOT/'server-mods/code'),str(out/'test.cpp'),'-o',str(exe)],check=True)
            run=subprocess.run([str(exe)],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)

if __name__=='__main__':unittest.main(verbosity=2)
