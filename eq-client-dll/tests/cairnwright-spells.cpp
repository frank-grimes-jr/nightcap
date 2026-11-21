#include "../src/spell_access.h"
#include "../src/ui_state.h"
#include <cassert>

int main()
{
	constexpr uint8_t stock_levels[16] = {1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,255};
	for (int id = 0; id <= 255; ++id) {
		const auto level = Cairnwright::EffectLevel(200, static_cast<uint8_t>(id), stock_levels);
		if (id % 17) { assert(level == stock_levels[(id % 17) - 1]); }
		else { assert(!level && !(level >= -4)); }
	}
	for (auto id : {Cairnwright::StrikeCairn, Cairnwright::SoundTheSeam, Cairnwright::SeamFracture}) {
		const auto level = Cairnwright::EffectLevel(id, 17, stock_levels);
		assert(Cairnwright::EffectLevel(id, 16, stock_levels) == level);
		assert(level == 1 && level >= 6 - 5 && !(level >= 7 - 5));
	}
	nightcap::UIState ui;
	assert(ui.Consume("[NCUI1]S|1|42|11|0|12|17|0|0|Mason"));
	assert(ui.Classes() == "CRW/---/---");
	assert(ui.ClassMask() == 65536);
	for (auto id : {Cairnwright::StrikeCairn, Cairnwright::SoundTheSeam}) {
		assert(NightcapSpellClasses::Level(id, 17) == 1);
		assert(NightcapSpellClasses::Mask(id) == 65536);
		assert(nightcap::HeldSpellLevel(id, ui.ClassMask()) == 1);
		for (unsigned c = 1; c <= 16; ++c) {
			assert(NightcapSpellClasses::Level(id, c) == 255);
		}
	}
	assert(!ui.Consume("[NCUI1]S|2|42|11|0|12|18|0|0|Mason"));
	assert(ui.Consume("[NCUI1]S|2|42|11|0|12|1|17|0|Mason"));
	assert(ui.Classes() == "WAR/CRW/---");
	assert(ui.Consume("[NCUI1]S|3|42|11|0|12|1|2|17|Mason"));
	assert(ui.Classes() == "WAR/CLR/CRW");
	assert(ui.Consume("[NCUI1]S|4|42|11|0|12|1|2|0|Mason"));
	assert(nightcap::HeldSpellLevel(Cairnwright::StrikeCairn, ui.ClassMask()) == 255);
	assert(nightcap::HeldSpellLevel(44383, ~uint32_t{0}) == 255);
	assert(NightcapSpellClasses::Level(200, 17) == 255);
	return 0;
}
