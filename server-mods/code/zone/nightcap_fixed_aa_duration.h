#pragma once

#include <chrono>
#include <cstdint>

namespace NightcapFixedAA {
constexpr int Milliseconds(uint32_t spell)
{
	return spell == 21773 ? 12000 : spell == 30736 ? 24000 : 0;
}

inline int64_t Now()
{
	using namespace std::chrono;
	return duration_cast<milliseconds>(system_clock::now().time_since_epoch()).count();
}

constexpr int Ticks(int remaining_ms) { return (remaining_ms + 5999) / 6000; }

// Both reviewed self buffs contain only SPA 200. Their distance removal
// coordinates are unused and persist as three signed integers in character_buffs.
// x/y hold Unix minutes and milliseconds in that minute, or 0/remaining while paused.
// z tags both the spell and the representation. These fields never go on the wire.
template<typename Buff> bool Marked(const Buff& buff)
{
	return Milliseconds(buff.spellid) &&
		(buff.caston_z == static_cast<int>(buff.spellid) || buff.caston_z == -static_cast<int>(buff.spellid));
}

template<typename Buff> void Store(Buff& buff, int64_t now, int remaining, bool suspended)
{
	const int64_t deadline = now + remaining;
	buff.caston_x = suspended ? 0 : static_cast<int32_t>(deadline / 60000);
	buff.caston_y = suspended ? remaining : static_cast<int32_t>(deadline % 60000);
	buff.caston_z = suspended ? -static_cast<int>(buff.spellid) : static_cast<int>(buff.spellid);
}

template<typename Buff> void Start(Buff& buff, int64_t now, bool suspended)
{
	const int duration = Milliseconds(buff.spellid);
	Store(buff, now, duration, suspended);
	buff.ticsremaining = Ticks(duration);
}

// Old unmarked rows and corrupt or expired deadlines cannot establish time remaining.
template<typename Buff> int Remaining(Buff& buff, int64_t now, bool suspended)
{
	if (!Marked(buff)) { return 0; }
	const bool paused = buff.caston_z < 0;
	if ((paused && buff.caston_x != 0) || buff.caston_x < 0 || buff.caston_y < 0 || buff.caston_y >= 60000) {
		return 0;
	}
	const int64_t remaining = paused ? buff.caston_y : int64_t(buff.caston_x) * 60000 + buff.caston_y - now;
	if (remaining <= 0 || remaining > Milliseconds(buff.spellid)) { return 0; }
	if (paused != suspended) { Store(buff, now, static_cast<int>(remaining), suspended); }
	return static_cast<int>(remaining);
}
}
