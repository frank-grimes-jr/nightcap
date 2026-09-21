"""Compile native market reads and tunnel chat against a bounded C++ fixture."""
from pathlib import Path
import subprocess
import tempfile
import unittest

from test_gameplay_policies import function


ROOT = Path(__file__).resolve().parents[2]
ZONE = ROOT / 'server-mods/code/zone'


FIXTURE = r'''
#include <algorithm>
#include <array>
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <map>
#include <string>
#include <utility>
#include <vector>
using uint32 = uint32_t;
using uint64 = uint64_t;
namespace fmt {
 template<class T> std::string one(const T& value) { return std::to_string(value); }
 inline std::string one(const std::string& value) { return value; }
 inline std::string one(const char* value) { return value; }
 template<class... Args> std::string format(std::string pattern,const Args&... args) {
  std::vector<std::string> values={one(args)...};
  for(const auto& value:values) {
   auto pos=pattern.find("{}"); assert(pos!=std::string::npos);
   pattern.replace(pos,2,value);
  }
  return pattern;
 }
}
namespace Strings { uint32 ToUnsignedInt(const char* text) { return static_cast<uint32>(std::strtoul(text,nullptr,10)); } }
#define RuleI(category,name) 4
#define RuleR(category,name) 2.5
namespace NightcapMarket {
 struct Offer {
  uint64 epoch=0; uint32 npc_id=0,zone_id=0,item_id=0,price_cp=0;
  std::string kind;
 };
 bool Ready();
 std::vector<Offer> ReadOffers(uint32,uint32,int);
 bool ReadOffer(uint32,uint32,int,Offer&,uint32=0);
}
struct Row {
 std::array<std::string,4> fields;
 const char* operator[](int i) const { return fields[i].c_str(); }
 operator const char*() const { return fields[0].c_str(); }
};
struct QueryResult {
 bool ok=true;
 std::vector<Row> rows;
 bool Success() const { return ok; }
 size_t RowCount() const { return rows.size(); }
 auto begin() const { return rows.begin(); }
 auto end() const { return rows.end(); }
};
struct MarketRow {
 uint32 npc=0,zone=0,item=0,price=0;
 uint64 epoch=1;
 std::string kind="sell";
 bool active=true;
};
struct ItemData { uint32 ID=0; };
struct ZoneDatabase {
 std::vector<MarketRow> offers;
 std::map<uint32,ItemData> items;
 bool fail_query=false;
 std::string last_sql;
 QueryResult QueryDatabase(const std::string& sql,bool) {
  last_sql=sql;
  if(sql.find("information_schema.TABLES")!=std::string::npos) return {true,{{{{"7"}}}}};
  if(sql.find("information_schema.TRIGGERS")!=std::string::npos) return {true,{{{{"0"}}}}};
  if(fail_query) return {false,{}};
  assert(sql.find("o.remaining=1")!=std::string::npos);
  assert(sql.find("ORDER BY o.item_id LIMIT 3")!=std::string::npos);
  assert(sql.find("JOIN nightcap_market_actors")!=std::string::npos);
  QueryResult result;
  for(const auto& offer:offers) {
   if(!offer.active) continue;
   if(sql.find("o.npc_id="+std::to_string(offer.npc))==std::string::npos) continue;
   if(sql.find("o.zone_id="+std::to_string(offer.zone))==std::string::npos) continue;
   result.rows.push_back({{{std::to_string(offer.epoch),std::to_string(offer.item),
    std::to_string(offer.price),offer.kind}}});
  }
  std::sort(result.rows.begin(),result.rows.end(),[](const Row& a,const Row& b) {
   return std::stoul(a.fields[1])<std::stoul(b.fields[1]);
  });
  if(result.rows.size()>3) result.rows.resize(3);
  return result;
 }
 const ItemData* GetItem(uint32 id) const {
  auto found=items.find(id); return found==items.end()?nullptr:&found->second;
 }
} database;
namespace EQ { namespace saylink { enum { SayLinkItemData=1 }; }
 struct SayLinkEngine {
  uint32 item=0;
  void SetLinkType(int) {}
  void SetItemData(const ItemData* value) { item=value->ID; }
  std::string GenerateLink() const { return "[item"+std::to_string(item)+"]"; }
 };
}
struct Zone {
 uint32 id=22,instance=0;
 uint32 GetZoneID() const { return id; }
 uint32 GetInstanceID() const { return instance; }
};
Zone active_zone; Zone* zone=&active_zone;
struct Mob {
 uint32 entity=5,npc=999500;
 std::string name="Rellan_Ridgewalker";
 bool is_npc=true;
 bool IsNPC() const { return is_npc; }
 uint32 GetNPCTypeID() const { return npc; }
 const char* GetCleanName() const { return name.c_str(); }
};
struct EntityList {
 std::map<uint32,Mob> mobs;
 Mob* GetMob(uint32 id) {
  auto found=mobs.find(id); return found==mobs.end()?nullptr:&found->second;
 }
} entity_list;
enum { ChatChannel_Auction=1,ChatChannel_OOC=2 };
int MarketEra() { return 0; }
struct Client {
 struct Sent { std::string name,text; int channel=0; };
 std::vector<Sent> sent;
 void ChannelMessageSend(const char* from,const char*,int channel,int,int,const char* pattern,const char* message) {
  assert(std::string(pattern)=="%s"); sent.push_back({from,message,channel});
 }
 void MarketAnnouncement(uint32,uint32);
 void TunnelChatter(uint32,const std::string&);
};

// ACTUAL_TUNNEL_CHAT
namespace NightcapMarket {
// ACTUAL_READY
// ACTUAL_READ_OFFERS
// ACTUAL_READ_OFFER
}
// ACTUAL_MARKET_ANNOUNCEMENT
// ACTUAL_TUNNEL_CHATTER

int main() {
 using NightcapMarket::Offer;
 database.offers={{999500,22,1001,10000,1,"sell",true},
                  {999500,22,1002,20000,1,"sell",true}};
 database.items={{1001,{1001}},{1002,{1002}}};
 auto both=NightcapMarket::ReadOffers(999500,22,0);
 assert(both.size()==2 && both[0].item_id==1001 && both[1].item_id==1002);
 Offer selected;
 assert(!NightcapMarket::ReadOffer(999500,22,0,selected));
 assert(NightcapMarket::ReadOffer(999500,22,0,selected,1001) && selected.item_id==1001);
 assert(NightcapMarket::ReadOffer(999500,22,0,selected,1002) && selected.item_id==1002);
 assert(!NightcapMarket::ReadOffer(999500,22,0,selected,9999));
 database.offers[0].active=false;
 assert(NightcapMarket::ReadOffers(999500,22,0).size()==1);
 assert(!NightcapMarket::ReadOffer(999500,22,0,selected,1001));
 assert(NightcapMarket::ReadOffer(999500,22,0,selected) && selected.item_id==1002);
 database.offers[1].active=false;
 assert(NightcapMarket::ReadOffers(999500,22,0).empty());
 assert(!NightcapMarket::ReadOffer(999500,22,0,selected,1002));
 database.offers[0].active=database.offers[1].active=true;
 database.fail_query=true;
 assert(NightcapMarket::ReadOffers(999500,22,0).empty());
 assert(!NightcapMarket::ReadOffer(999500,22,0,selected,1001));
 database.fail_query=false;
 database.offers.push_back({999500,22,1003,30000,1,"sell",true});
 assert(NightcapMarket::ReadOffers(999500,22,0).empty());
 assert(!NightcapMarket::ReadOffer(999500,22,0,selected,1001));
 database.offers.pop_back();
 assert(NightcapMarket::ReadOffers(999500,22,-1).empty());
 assert(NightcapMarket::ReadOffers(999501,22,0).empty());

 entity_list.mobs.emplace(5,Mob{});
 Client client;
 client.MarketAnnouncement(5,0);
 assert(client.sent.size()==1 && client.sent[0].channel==ChatChannel_Auction);
 assert(client.sent[0].name=="Rellan");
 assert(client.sent[0].text.find("[item1001]")!=std::string::npos);
 assert(client.sent[0].text.find("[item1002]")!=std::string::npos);
 assert(client.sent[0].text.find(" // ")!=std::string::npos);
 client.MarketAnnouncement(5,1);
 assert(client.sent.back().text.find(" -- ")!=std::string::npos);
 client.MarketAnnouncement(5,2);
 assert(client.sent.back().text.find(", ")!=std::string::npos);
 client.TunnelChatter(5,"Anyone headed to Guk?");
 assert(client.sent.back().channel==ChatChannel_OOC);
 assert(client.sent.back().name=="Rellan");
 assert(client.sent.back().text=="Anyone headed to Guk?");
 auto count=client.sent.size();
 active_zone.instance=1;
 client.MarketAnnouncement(5,0); client.TunnelChatter(5,"ignored");
 assert(client.sent.size()==count);
 active_zone.instance=0; active_zone.id=2;
 client.MarketAnnouncement(5,0); client.TunnelChatter(5,"ignored");
 assert(client.sent.size()==count);
 active_zone.id=22;
 entity_list.mobs.at(5).npc=123;
 client.MarketAnnouncement(5,0); client.TunnelChatter(5,"ignored");
 assert(client.sent.size()==count);
 entity_list.mobs.at(5).npc=999500;
 entity_list.mobs.at(5).is_npc=false;
 client.MarketAnnouncement(5,0); client.TunnelChatter(5,"ignored");
 assert(client.sent.size()==count);
 entity_list.mobs.at(5).is_npc=true;
 client.TunnelChatter(5,std::string(301,'x'));
 assert(client.sent.size()==count);
}
'''


class TunnelMarketNative(unittest.TestCase):
    def test_offer_reads_and_native_channels(self):
        market = (ZONE / 'living_economy.cpp').read_text()
        client = (ZONE / 'client_living_economy.cpp').read_text()
        source = FIXTURE
        for marker, body in (
            ('// ACTUAL_READY', function(market, 'bool Ready()')),
            ('// ACTUAL_READ_OFFERS', function(market, 'std::vector<Offer> ReadOffers(')),
            ('// ACTUAL_READ_OFFER', function(market, 'bool ReadOffer(')),
            ('// ACTUAL_MARKET_ANNOUNCEMENT', function(client, 'void Client::MarketAnnouncement(')),
            ('// ACTUAL_TUNNEL_CHATTER', function(client, 'void Client::TunnelChatter(')),
        ):
            source = source.replace(marker, body)
        source = source.replace('// ACTUAL_TUNNEL_CHAT',
            (ROOT / 'server-mods/code/common/tunnel_chat.h').read_text())
        with tempfile.TemporaryDirectory(prefix='nightcap-tunnel-market-') as tmp:
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
