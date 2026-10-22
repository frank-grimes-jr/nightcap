// Inspect bytes produced by the actual candidate shared_memory executable.
#ifdef NDEBUG
#error "Cache verification requires assertions enabled"
#endif
#include "common/dungeon_contract.h"
#include "common/dungeon_policy.h"
#include "common/fixed_memory_hash_set.h"
#include <cassert>
#include <fstream>
#include <iostream>
#include <vector>

int main(int argc, char **argv) {
	assert(argc == 2);
	std::ifstream file(argv[1],std::ios::binary);
	assert(file);
	std::vector<unsigned char> bytes((std::istreambuf_iterator<char>(file)),{});
	assert(bytes.size()>16);
	EQ::FixedMemoryHashSet<EQ::ItemData> cache(bytes.data()+4,bytes.size()-4);
	unsigned count=0,clicks=0,negative=0;
	for (uint32_t id=NightcapDungeon::ItemBegin; id<NightcapDungeon::ItemEnd; ++id) {
		assert(cache.exists(id));
		const auto &item=cache[id];
		if (!NightcapDungeon::CacheMatches(item)) { std::cerr<<"Cache mismatch: "<<id<<"\n"; return 1; }
		assert(item.Magic && item.Price==0 && item.FixedSellPrice==0 && item.FreeTrade);
		assert(item.NoDrop && item.NoRent && !item.Attuneable && !item.LoreGroup);
		++count;
		auto bad=item; bad.Magic=false; assert(!NightcapDungeon::CacheMatches(bad)); ++negative;
		bad=item;bad.Lore[0]='!';assert(!NightcapDungeon::CacheMatches(bad));++negative;
		if (item.Click.Effect>0) {
			++clicks;
#define CHECK_DRIFT(member) bad=item; ++bad.member; assert(!NightcapDungeon::CacheMatches(bad)); ++negative;
			CHECK_DRIFT(Click.Effect); CHECK_DRIFT(Click.Type); CHECK_DRIFT(Click.Level); CHECK_DRIFT(Click.Level2);
			CHECK_DRIFT(CastTime); CHECK_DRIFT(CastTime_); CHECK_DRIFT(MaxCharges);
			CHECK_DRIFT(RecastDelay); CHECK_DRIFT(RecastType);
#undef CHECK_DRIFT
			bad=item;bad.ClickName[0]='!';assert(!NightcapDungeon::CacheMatches(bad));++negative;
		}
	}
	assert(count==414 && clicks==6 && negative==888);
	std::cout<<"{\"items\":"<<count<<",\"clicks\":"<<clicks<<",\"drift_rejections\":"<<negative<<",\"item_bytes\":"<<sizeof(EQ::ItemData)<<"}\n";
}
