// Compare all pre-existing native cache records, then validate the additive campaign.
#ifdef NDEBUG
#error assertions must be enabled
#endif
#include "common/item_data.h"
#include "common/spdat.h"
#include "common/last_lantern_catalog.h"
#include "common/fixed_memory_hash_set.h"
#include <cassert>
#include <cstring>
#include <fstream>
#include <iostream>
#include <vector>
std::vector<unsigned char> read(const char*p){std::ifstream f(p,std::ios::binary|std::ios::ate);assert(f);auto n=f.tellg();assert(n>0);std::vector<unsigned char> bytes(static_cast<size_t>(n));f.seekg(0);f.read(reinterpret_cast<char*>(bytes.data()),bytes.size());assert(f);return bytes;}
int main(int argc,char**argv){
 assert(argc==5);auto a=read(argv[1]),b=read(argv[2]);assert(a.size()>16&&b.size()>16);
 EQ::FixedMemoryHashSet<EQ::ItemData> old(a.data()+4,a.size()-4),now(b.data()+4,b.size()-4);
 unsigned kept=0,added=0;
 for(unsigned id=0;id<=std::max(old.max_key(),now.max_key());++id){
  if(old.exists(id)){assert(now.exists(id));if(std::memcmp(&old[id],&now[id],sizeof(EQ::ItemData))){std::cerr<<"Changed existing item "<<id;return 1;}++kept;}
  else if(now.exists(id)){assert(NightcapLantern::IsCampaignItem(id));++added;}
 }
 assert(added==129&&now.size()==old.size()+129);
 for(unsigned id=964000;id<=964127;++id){assert(now.exists(id)&&NightcapLantern::CacheMatches(now[id]));}
 assert(now.exists(900501));auto &charm=now[900501];assert(!charm.NoDrop&&charm.NoTransfer&&charm.NoPet&&!charm.FreeTrade&&!charm.Price&&!charm.FixedSellPrice);
 auto x=read(argv[3]),y=read(argv[4]);assert(x.size()>8&&y.size()>=x.size());
 const auto old_count=*reinterpret_cast<const uint32_t*>(x.data()+4),new_count=*reinterpret_cast<const uint32_t*>(y.data()+4);
 assert(old_count<=new_count&&x.size()==12+old_count*sizeof(SPDat_Spell_Struct)&&y.size()==12+new_count*sizeof(SPDat_Spell_Struct));
 auto before=reinterpret_cast<const SPDat_Spell_Struct*>(x.data()+8),after=reinterpret_cast<const SPDat_Spell_Struct*>(y.data()+8);
 unsigned spell_kept=0;
 for(unsigned id=0;id<old_count;++id){if(id>=42800&&id<=42805)continue;assert(std::memcmp(&before[id],&after[id],sizeof(SPDat_Spell_Struct))==0);++spell_kept;}
 for(unsigned id=42800;id<=42805;++id){assert(id<new_count&&after[id].id==id);}
 std::cout<<"{\"status\":\"PASS\",\"preserved_items\":"<<kept<<",\"added_items\":"<<added<<",\"armor_afterimages\":128,\"preserved_spell_record_bytes\":"<<spell_kept*sizeof(SPDat_Spell_Struct)<<",\"item_bytes\":"<<sizeof(EQ::ItemData)<<"}\n";
}
