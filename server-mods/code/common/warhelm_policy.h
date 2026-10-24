#pragma once
#include <cstdint>
#include <initializer_list>
namespace NightcapAshen {
constexpr uint32_t Zone = 113, Task = 9801, Keeper = 998860, Helmet = 990510;
constexpr uint32_t Augment = 961020;
enum class Event : unsigned { Enter, Herald, Standard1, Standard2, Standard3, Binding,
	Marshal, Knight1, Knight2, Knight3, General, Echo, Altar };
constexpr unsigned Bit(Event event) { return 1u << unsigned(event); }
constexpr unsigned Required(Event event) {
	switch (event) {
	case Event::Enter: return 0;
	case Event::Herald: return Bit(Event::Enter);
	case Event::Standard1: case Event::Standard2: case Event::Standard3: return Bit(Event::Herald);
	case Event::Binding: return Bit(Event::Standard1)|Bit(Event::Standard2)|Bit(Event::Standard3);
	case Event::Marshal: return Bit(Event::Binding);
	case Event::Knight1: case Event::Knight2: case Event::Knight3: return Bit(Event::Marshal);
	case Event::General: return Bit(Event::Knight1)|Bit(Event::Knight2)|Bit(Event::Knight3);
	case Event::Echo: return Bit(Event::General);
	case Event::Altar: return Bit(Event::Echo);
	}
	return UINT32_MAX;
}
inline bool Advance(unsigned &mask, Event event) {
	const auto needed=Required(event);
	if (needed==UINT32_MAX || (mask&needed)!=needed || (mask&Bit(event))) { return false; }
	mask|=Bit(event); return true;
}
inline bool Ready(unsigned mask) { return mask == (1u<<13)-1; }
// Native class masks use 1 << class number (Shadow Knight=5), unlike item masks.
inline bool Eligible(unsigned level, unsigned classes) { return level>=50 && (classes&(1u<<5)); }
inline bool Credit(bool enrolled, bool alive, float distance_squared) {
	return enrolled && alive && distance_squared<=200.0f*200.0f;
}
inline bool Combat(uint32_t npc) { return npc>=998861 && npc<=998866; }
inline bool Transient(uint32_t npc) { return npc==998875 || npc==998876; }
inline bool Service(uint32_t npc) { return npc==Keeper || (npc>=998867 && npc<=998874); }
inline uint32_t MiniReward(uint32_t npc) { return npc>=998861 && npc<=998863 ? 961030+(npc-998861) : 0; }
}
