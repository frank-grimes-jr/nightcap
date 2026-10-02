"""Exercise production LootAll and physical consent with dependency fakes."""
import argparse, hashlib, json, subprocess, tempfile
from pathlib import Path
from test_advanced_loot_access import function

FIXTURE = r"""
#include <algorithm>
#include <cassert>
#include <cstdarg>
#include <cstdint>
#include <cstdio>
#include <functional>
#include <iostream>
#include <map>
#include <memory>
#include <string>
#include <vector>
using uint32=uint32_t;using uint16=uint16_t;using uint64=uint64_t;using int16=int16_t;
// LOOT_HEADER
enum class Filter { Ask, Always, Never };
enum class Action { Take, TakeNoTrade };
enum class TransferResult { Delivered, Declined, Uncertain };
constexpr uint32 ShowNewOnly=32,MaxResults=256;
uint32 Capability(Action a){return 1u<<static_cast<unsigned>(a);}
namespace Chat {constexpr int Yellow=1,Red=2;}
namespace EQ {namespace item {constexpr int ItemClassBag=1;} namespace invbag {constexpr int SLOT_COUNT=10;}
struct InventoryProfile {static bool SupportsContainers(int16 s){return s>=22&&s<=29;} static int16 CalcSlotId(int16 s,int){return static_cast<int16>(251+(s-22)*10);}};}
struct Item {uint32 ID=1;int ItemClass=0;std::string Name="Item";};
struct Database {std::map<uint32,Item> items;const Item* GetItem(uint32 id){auto i=items.find(id);return i==items.end()?nullptr:&i->second;}} database;
namespace Strings {std::string ToLower(std::string s){std::transform(s.begin(),s.end(),s.begin(),[](char c){return static_cast<char>(tolower(c));});return s;}}
struct Client {std::string message;void Message(int,const char *f,...){char b[512];va_list v;va_start(v,f);vsnprintf(b,sizeof(b),f,v);va_end(v);message=b;}};
struct Corpse {bool alive=true;std::vector<LootItem*> items;const auto& GetLootItems(){return items;}};
struct Drop {LootItem* item=nullptr;uint32 token=0;bool visible=true,allowed=true,consent=false;TransferResult result=TransferResult::Delivered;};
struct CorpseEntry {Corpse* corpse=nullptr;std::map<std::string,std::shared_ptr<Drop>> drops;};
struct PendingLoot {std::shared_ptr<CorpseEntry> entry;std::shared_ptr<Drop> drop;std::vector<LootItem> items;};
struct Preferences {uint32 settings=0;std::map<uint32,Filter> filters;Filter Saved(uint32 id){return filters.count(id)?filters[id]:Filter::Ask;}};
struct Session {Client* client=nullptr;Preferences preferences;struct {uint32 revision=1;} snapshot;std::string search;
std::vector<PendingLoot> pending_no_trade;uint32 pending_revision=0;uint64 pending_until=0;
void ClearConfirmation(){pending_no_trade.clear();pending_revision=0;pending_until=0;}};
std::map<Corpse*,std::shared_ptr<CorpseEntry>> corpses;
uint64 clock_ms=100;uint64 Now(){return clock_ms;}
bool Present(const CorpseEntry&e,const Drop&d){return e.corpse->alive&&std::find(e.corpse->items.begin(),e.corpse->items.end(),d.item)!=e.corpse->items.end();}
bool Visible(Session&,const CorpseEntry&e,const Drop&d){return Present(e,d)&&d.visible;}
bool CanTake(Session&,const CorpseEntry&e,const Drop&d){return Present(e,d)&&d.allowed;}
bool RequiresConsent(Corpse*c,LootItem*i){for(auto&[k,d]:corpses.at(c)->drops)if(d->item==i)return d->consent;return false;}
struct Row {uint32 capabilities;};
Row MakeRow(Session&s,const CorpseEntry&e,const Drop&d){return {CanTake(s,e,d)?Capability(d.consent?Action::TakeNoTrade:Action::Take):0};}
std::vector<uint32> awarded;std::function<void(uint32)> callback;
TransferResult Take(Session&,const std::shared_ptr<CorpseEntry>&e,const std::shared_ptr<Drop>&d,bool consent,bool){
assert(!d->consent||consent);if(d->result==TransferResult::Delivered){awarded.push_back(d->token);auto&v=e->corpse->items;v.erase(std::find(v.begin(),v.end(),d->item));}
if(callback)callback(d->token);return d->result;}
void Discover(){}void RefreshAll(){}void Publish(Session&s,bool){if(s.pending_revision)s.ClearConfirmation();++s.snapshot.revision;}
// ACTUAL_FUNCTIONS
struct Fixture {
Client client;Corpse corpse;Session s;std::shared_ptr<CorpseEntry> e=std::make_shared<CorpseEntry>();std::vector<std::unique_ptr<LootItem>> items;
Fixture(){corpses.clear();awarded.clear();callback={};clock_ms=100;s.client=&client;e->corpse=&corpse;corpses[&corpse]=e;database.items.clear();}
std::shared_ptr<Drop> add(uint32 token,bool consent=false){auto i=std::make_unique<LootItem>();i->item_id=token;i->charges=1;i->advanced_loot_id=std::to_string(token);auto d=std::make_shared<Drop>();d->item=i.get();d->token=token;d->consent=consent;database.items[token]={token,0,"Item"};e->drops[i->advanced_loot_id]=d;corpse.items.push_back(i.get());items.push_back(std::move(i));return d;}
};
int main(){
{Fixture f;for(uint32 i=1;i<=12;++i)f.add(i);f.add(13)->visible=false;f.add(14)->allowed=false;LootAll(f.s,false);assert(awarded.size()==12&&f.client.message.find("1 unavailable")!=std::string::npos);}
{Fixture f;f.add(1)->result=TransferResult::Declined;LootAll(f.s,false);assert(awarded.empty()&&f.client.message.find("Looted 0")!=std::string::npos);}
{Fixture f;f.add(1)->result=TransferResult::Uncertain;f.add(2);LootAll(f.s,false);assert(awarded.empty()&&f.s.pending_no_trade.empty()&&f.client.message.find("Reconnect")!=std::string::npos);}
{Fixture f;f.add(1);f.add(2,true);LootAll(f.s,false);assert(awarded==std::vector<uint32>{1}&&f.s.pending_revision==f.s.snapshot.revision);f.add(3,true);LootAll(f.s,true);assert((awarded==std::vector<uint32>{1,2}));LootAll(f.s,true);assert(awarded.size()==2);}
for(int kind=0;kind<6;++kind){Fixture f;auto d=f.add(1,true);LootAll(f.s,false);switch(kind){case 0:d->item->charges=2;break;case 1:d->item->aug_6=123;break;case 2:f.corpse.alive=false;break;case 3:clock_ms+=30000;break;case 4:++f.s.snapshot.revision;break;case 5:d->allowed=false;break;}LootAll(f.s,true);assert(awarded.empty()&&f.s.pending_no_trade.empty());}
{Fixture f;auto bag=f.add(1,true);database.items[1].ItemClass=EQ::item::ItemClassBag;bag->item->equip_slot=22;auto child=f.add(2);child->item->equip_slot=251;child->visible=false;LootAll(f.s,false);assert(f.s.pending_no_trade[0].items.size()==2);child->item->custom_data="changed";LootAll(f.s,true);assert(awarded.empty());}
{Fixture f;f.add(1,true);auto second=f.add(2,true);LootAll(f.s,false);callback=[&](uint32 t){if(t==1)second->item->charges=7;};LootAll(f.s,true);assert(awarded==std::vector<uint32>{1});}
{Fixture f;for(uint32 i=1;i<=MaxResults+1;++i)f.add(i,true);LootAll(f.s,false);assert(f.s.pending_no_trade.size()==MaxResults);LootAll(f.s,true);assert(awarded.size()==MaxResults&&awarded.back()==MaxResults);}
{Fixture f;f.add(1,true);LootAll(f.s,false);Publish(f.s,true);LootAll(f.s,true);assert(awarded.empty());}
std::cout<<"PASS: actual LootAll batching, outcomes, physical/bag consent, expiry, revision, new drops and callback mutation guards\n";
}
"""

def run(root, output):
    source=root/'server-mods/code/zone/advanced_loot.cpp'
    header=root/'server-mods/code/common/loot.h'
    selected='\n'.join(function(source.read_text(),s) for s in ('std::vector<LootItem> PhysicalItems(', 'bool SamePending(', 'void LootAll('))
    cpp=FIXTURE.replace('// ACTUAL_FUNCTIONS',selected).replace('// LOOT_HEADER',header.read_text().replace('#pragma once','').replace('#include "common/types.h"',''))
    with tempfile.TemporaryDirectory(prefix='nightcap-advloot-bulk-') as temporary:
        p=Path(temporary);(p/'test.cpp').write_text(cpp)
        (p/'build.cmd').write_text('@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat" >nul || exit /b 1\ncl /nologo /EHsc /W4 /WX /std:c++17 test.cpp /Fe:test.exe >build.log 2>&1\nexit /b %errorlevel%\n')
        result=subprocess.run(['cmd','/d','/c',str(p/'build.cmd')],cwd=p)
        if result.returncode:raise RuntimeError((p/'build.log').read_text())
        result=subprocess.run([str(p/'test.exe')],capture_output=True,text=True)
        if result.returncode:raise RuntimeError(result.stdout+result.stderr)
        output.write_text(json.dumps({'status':'passed','scope':'actual bulk functions with dependency fakes, not native gameplay','sources':{str(x.relative_to(root)):hashlib.sha256(x.read_bytes()).hexdigest() for x in (source,header)},'result':result.stdout.strip()},indent=2)+'\n')
        print(result.stdout.strip())
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();run(a.root.resolve(),a.output.resolve())
