"""Compile actual hunger, stamina, setter and consume paths with packet fixtures.

Run: python tools/tests/test_food_drink.py (CXX or g++ required).
This tests server packet values; RoF2 warning rendering requires in-game QA.
"""
import argparse
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source-dir', type=Path, default=ROOT / 'server-mods/code/zone')
SOURCE = parser.parse_args().source_dir


def function(source, signature):
    start = source.index(signature)
    opening = source.index('{', start)
    depth = 0
    for end in range(opening, len(source)):
        depth += (source[end] == '{') - (source[end] == '}')
        if depth == 0:
            return source[start:end + 1]
    raise AssertionError(signature)


client = (SOURCE / 'client.cpp').read_text()
header = (SOURCE / 'client.h').read_text()
packet = (SOURCE / 'client_packet.cpp').read_text()
process = (SOURCE / 'client_process.cpp').read_text()
predicates = '\n'.join(function(header, 'bool ' + name + '() const')
                       for name in ('Hungry', 'Thirsty', 'IsStarved'))
native = '\n'.join(function(source, signature) for source, signature in (
    (client, 'void Client::SetHunger('),
    (client, 'void Client::SetThirst('),
    (client, 'void Client::SetConsumption('),
    (client, 'void Client::Consume('),
    (process, 'void Client::DoStaminaHungerUpdate('),
    (packet, 'void Client::Handle_OP_Consume('),
))
harness = r'''
#include <algorithm>
#include <cstdint>
#include <iostream>
#include <vector>
using int32=int32_t; using int16=int16_t; using uint8=uint8_t;
bool EnableFoodRequirement=true, EnableHungerPenalties=true;
int FoodLossPerUpdate=32;
#define RuleB(category,name) name
#define RuleI(category,name) name
#define LogFood(...) ((void)0)
#define LogError(...) ((void)0)
#define safe_delete(p) delete p
enum { OP_Stamina, EATING_MESSAGE, DRINKING_MESSAGE };
struct Stamina_Struct { int food=0, water=0; };
struct Consume_Struct { int slot=23; uint32_t auto_consumed=0xffffffff; uint8 type=1; };
struct EQApplicationPacket {
    size_t size; unsigned char* pBuffer;
    EQApplicationPacket(int,size_t n):size(n),pBuffer(new unsigned char[n]{}){}
    ~EQApplicationPacket(){delete[] pBuffer;}
};
namespace Zones { const int BAZAAR=151; }
struct Zone { int id=22; int GetZoneID(){return id;} } zone_value;
Zone* zone=&zone_value;
namespace EQ {
template<class T> T Clamp(T v,T lo,T hi){return std::max(lo,std::min(v,hi));}
template<class T> T ClampLower(T v,T lo){return std::max(v,lo);}
namespace item { enum {ItemTypeFood=14,ItemTypeDrink=15}; }
struct ItemData { int CastTime_=10; const char* Name="Ration"; };
struct ItemInstance { ItemData item; const ItemData* GetItem(){return &item;} };
}
struct Inventory {
    EQ::ItemInstance item; bool present=true;
    EQ::ItemInstance* GetItem(int){return present ? &item : nullptr;}
};
struct EntityList { int messages=0; template<class... T> void MessageCloseString(T...){++messages;} } entity_list;
struct Client {
    struct Profile { int hunger_level=0,thirst_level=0; } m_pp;
    struct Bonuses { bool hunger=false; } spellbonuses;
    bool gm=false; int horse=0,deleted=0; Inventory inventory;
    std::vector<Stamina_Struct> packets;
    bool GetGM() const {return gm;}
    int GetHorseId(){return horse;}
    const char* GetName(){return "Test";}
    Inventory& GetInv(){return inventory;}
    void DeleteItemInInventory(int,int n){deleted+=n;}
    void QueuePacket(EQApplicationPacket* p){packets.push_back(*reinterpret_cast<Stamina_Struct*>(p->pBuffer));}
    void FastQueuePacket(EQApplicationPacket** p){QueuePacket(*p);delete *p;*p=nullptr;}
    void SetHunger(int32); void SetThirst(int32); void SetConsumption(int32,int32);
    void Consume(const EQ::ItemData*,uint8,int16,bool);
    void DoStaminaHungerUpdate(); void Handle_OP_Consume(const EQApplicationPacket*);
''' + predicates + '\n};\n' + native + r'''
int main(){
    int checks=0,failures=0;
    auto check=[&](bool okay,const char* label){++checks;if(!okay){++failures;std::cerr<<"FAIL "<<label<<'\n';}};
    auto full=[&](Client& c,const char* label){
        check(c.m_pp.hunger_level==6000 && c.m_pp.thirst_level==6000,label);
        check(!c.packets.empty() && c.packets.back().food==6000 && c.packets.back().water==6000,label);
    };
    for(bool requirement:{false,true}) for(bool penalties:{false,true})
    for(int level:{-1,0,1,3000,6000,50000}){
        EnableFoodRequirement=requirement;EnableHungerPenalties=penalties;
        Client c;c.m_pp.hunger_level=level;c.m_pp.thirst_level=level;
        check(!c.Hungry() && !c.Thirsty() && !c.IsStarved(),"no hunger or starvation with any legacy rules");
        c.SetHunger(0);full(c,"hunger setter repairs both meters");
        c.m_pp.hunger_level=level;c.m_pp.thirst_level=level;c.SetThirst(-1);full(c,"thirst setter repairs both meters");
        c.SetConsumption(0,-1);full(c,"quest consumption cannot drain meters");
    }
    for(int id:{22,Zones::BAZAAR}) for(bool gm:{false,true}) for(int horse:{0,1}){
        Client c;zone->id=id;c.gm=gm;c.horse=horse;
        c.DoStaminaHungerUpdate();full(c,"stamina repairs empty profile in all zones/mount states");
        for(int n=0;n<1000;++n)c.DoStaminaHungerUpdate();
        full(c,"long sessions remain full");
    }
    for(uint8 type:{1,2,99}) for(uint32_t automatic:{0u,0xffffffffu}) for(bool present:{false,true}){
        Client c;c.inventory.present=present;
        EQApplicationPacket p(0,sizeof(Consume_Struct));
        auto pcs=reinterpret_cast<Consume_Struct*>(p.pBuffer);pcs->type=type;pcs->auto_consumed=automatic;pcs->slot=23;
        c.Handle_OP_Consume(&p);
        full(c,"client consume request repairs meters");
        check(c.deleted==0,"consume request preserves inventory");
    }
    for(uint8 type:{EQ::item::ItemTypeFood,EQ::item::ItemTypeDrink}) for(bool automatic:{false,true}){
        Client c;c.Consume(&c.inventory.item.item,type,23,automatic);
        full(c,"direct consume stays full");check(!c.deleted,"direct consume preserves inventory");
    }
    Client c;EQApplicationPacket malformed(0,1);c.Handle_OP_Consume(&malformed);
    check(c.packets.empty() && !c.deleted,"malformed packet rejected");
    check(entity_list.messages==0,"no eating/drinking broadcasts");
    std::cout<<checks-failures<<'/'<<checks<<" food/drink checks passed\n";
    return failures ? 1 : 0;
}
'''

with tempfile.TemporaryDirectory(prefix='nightcap-food-drink-') as directory:
    cpp = Path(directory) / 'test.cpp'
    binary = Path(directory) / ('test.exe' if os.name == 'nt' else 'test')
    cpp.write_text(harness)
    subprocess.run([os.environ.get('CXX', 'g++'), '-std=c++11', str(cpp), '-o', str(binary)], check=True)
    subprocess.run([str(binary)], check=True)

# Guard initialization order: the client must never receive the stale saved values.
load = packet.index('database.LoadCharacterData(cid, &m_pp, &m_epp);')
profile = packet.index('new EQApplicationPacket(OP_PlayerProfile', load)
initialization = packet[load:profile]
assert re.search(r'm_pp.hunger_level\s*=\s*6000;', initialization)
assert re.search(r'm_pp.thirst_level\s*=\s*6000;', initialization)
print('Login profile initializes both meters before OP_PlayerProfile')
