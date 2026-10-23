#pragma once
#include <cstdint>
#include <initializer_list>
namespace NightcapVigil {
constexpr uint32_t Zone = 760, Task = 9800, Keeper = 998820, Helmet = 990500;
constexpr uint32_t Augment = 961000;
enum class Event : unsigned { Enter, Vicar, Record1, Record2, Record3, Vigil,
	Halvyr, Knight1, Knight2, Knight3, Vaelen, Shadow, Chapel };
constexpr unsigned Bit(Event event) { return 1u << unsigned(event); }
constexpr unsigned Required(Event event) {
	switch (event) {
	case Event::Enter: return 0;
	case Event::Vicar: return Bit(Event::Enter);
	case Event::Record1: case Event::Record2: case Event::Record3: return Bit(Event::Vicar);
	case Event::Vigil: return Bit(Event::Record1)|Bit(Event::Record2)|Bit(Event::Record3);
	case Event::Halvyr: return Bit(Event::Vigil);
	case Event::Knight1: case Event::Knight2: case Event::Knight3: return Bit(Event::Halvyr);
	case Event::Vaelen: return Bit(Event::Knight1)|Bit(Event::Knight2)|Bit(Event::Knight3);
	case Event::Shadow: return Bit(Event::Vaelen);
	case Event::Chapel: return Bit(Event::Shadow);
	}
	return UINT32_MAX;
}
inline bool Advance(unsigned &mask, Event event) {
	const auto needed=Required(event);
	if (needed==UINT32_MAX || (mask&needed)!=needed || (mask&Bit(event))) { return false; }
	mask|=Bit(event); return true;
}
inline bool Ready(unsigned mask) { return mask == (1u<<13)-1; }
// Native class masks use 1 << class number (Paladin=3), unlike item masks.
inline bool Eligible(unsigned level, unsigned classes) { return level>=50 && (classes&(1u<<3)); }
inline bool Credit(bool enrolled, bool alive, float distance_squared) {
	return enrolled && alive && distance_squared<=200.0f*200.0f;
}
inline bool Combat(uint32_t npc) { return npc>=998821 && npc<=998826; }
inline bool Service(uint32_t npc) { return npc==Keeper || (npc>=998827 && npc<=998834); }
inline uint32_t MiniReward(uint32_t npc) { return npc>=998821 && npc<=998823 ? 961010+(npc-998821) : 0; }
}
