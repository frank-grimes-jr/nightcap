#include "../src/advanced_loot_icons.h"
#include <cassert>
#include <iostream>
using nightcap::AdvancedLootIcons;
static unsigned char cache_bytes[0x20]{};
static int animation, calls;
static bool available = true;
static void *__cdecl Cache(int type) { assert(type == 0); return available ? cache_bytes : nullptr; }
static void *__fastcall Get(void *self, void *, int icon) { assert(self == cache_bytes && icon >= 500 && icon <= 600); ++calls; return &animation; }
int main() {
	static_assert(sizeof(void *) == 4, "RoF2 is x86");
	alignas(4) unsigned char button[0x258]{};
	*reinterpret_cast<int *>(cache_bytes+0x18) = 500;
	*reinterpret_cast<int *>(cache_bytes+0x1c) = 600;
	AdvancedLootIcons::cache = &Cache;
	AdvancedLootIcons::get = reinterpret_cast<AdvancedLootIcons::Get>(&Get);
	auto check = [&](void *expected) { for (unsigned i=0x240; i<=0x254; i+=4) { assert(*reinterpret_cast<void **>(button+i) == expected); } };
	assert(AdvancedLootIcons::Set(button, 500)); check(&animation);
	assert(AdvancedLootIcons::Set(button, 600)); check(&animation);
	for (auto icon : {0u,499u,601u,0xffffffffu}) { assert(!AdvancedLootIcons::Set(button,icon)); check(nullptr); }
	assert(calls == 2);
	available = false; assert(!AdvancedLootIcons::Set(button,500)); check(nullptr);
	assert(!AdvancedLootIcons::Set(nullptr,500));
	std::cout << "PASS: stock icon cache ABI, bounds, six decal states and stale-image clearing\n";
}
