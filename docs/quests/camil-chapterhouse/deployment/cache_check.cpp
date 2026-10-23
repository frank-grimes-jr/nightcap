#ifdef NDEBUG
#error "Cache verification requires assertions"
#endif
#include "common/dungeon_contract.h"
#include "common/fixed_memory_hash_set.h"
#include <cassert>
#include <fstream>
#include <iostream>
#include <vector>
int main(int argc,char**argv) {
	assert(argc==2);std::ifstream f(argv[1],std::ios::binary);assert(f);
	std::vector<unsigned char> bytes((std::istreambuf_iterator<char>(f)),{});assert(bytes.size()>16);
	EQ::FixedMemoryHashSet<EQ::ItemData> cache(bytes.data()+4,bytes.size()-4);
	unsigned count=0,negative=0;
	auto check=[&](unsigned id) {
		assert(cache.exists(id));auto item=cache[id];assert(NightcapDungeon::CacheMatches(item));++count;
		auto bad=item;bad.Magic=!bad.Magic;assert(!NightcapDungeon::CacheMatches(bad));++negative;
		bad=item;bad.HP++;assert(!NightcapDungeon::CacheMatches(bad));++negative;
	};
	for(unsigned id=960000;id<960420;++id)check(id);
	for(unsigned id=961000;id<961004;++id)check(id);
	for(unsigned id=961010;id<961013;++id)check(id);
	assert(count==427 && negative==854);
	std::cout<<"{\"items\":"<<count<<",\"drift_rejections\":"<<negative<<",\"item_bytes\":"<<sizeof(EQ::ItemData)<<"}\n";
}
