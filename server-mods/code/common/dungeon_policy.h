#pragma once
#include "common/dungeon_catalog.h"
#include <array>
#include <cstdint>
#include <limits>

namespace NightcapDungeon {
constexpr uint64_t Revision = 2026101601;
constexpr uint32_t Duration = 43200;
constexpr unsigned MaxMembers = 6;
constexpr uint32_t ItemBegin = 960000;
constexpr uint32_t SharedDesigns = 24;
constexpr uint32_t SharedItems = SharedDesigns * 4 * 3;
constexpr uint32_t ItemEnd = ItemBegin + SharedItems + DungeonCount * 3 * 2;
enum class Mode : uint8_t { Grind = 0, Raid = 1 };
enum class Quality : uint8_t { Normal = 0, Polished = 1, Ascended = 2 };
inline bool IsReward(uint32_t id) { return id >= ItemBegin && id < ItemEnd; }
// The Hate entrance service lives in the public Commonlands hub. A retained
// private entrance copy still supports the same run's status and reward menu.
inline const Dungeon *KeeperDungeon(uint32_t host, uint32_t instance, uint32_t keeper) {
	if (host==22 && instance==0 && keeper==998812) { return FindDungeon(76); }
	if (host==21 && instance==0 && keeper==998820) { return FindDungeon(760); }
	if (host==21 && instance==0 && keeper==998860) { return FindDungeon(113); }
	const auto d=FindDungeon(host);
	return d && d->keeper==keeper ? d : nullptr;
}
inline Quality RollQuality(Mode mode, unsigned roll) {
	return mode == Mode::Grind ? Quality::Normal : roll < 9000 ? Quality::Polished : Quality::Ascended;
}
inline unsigned BossCount(unsigned roll) { return roll < 8000 ? 1 : roll < 9800 ? 2 : 3; }
inline uint32_t SharedItem(unsigned band, unsigned design, Quality quality) {
	return band < 4 && design < SharedDesigns && unsigned(quality)<3 ? ItemBegin + (band * SharedDesigns + design) * 3 + unsigned(quality) : 0;
}
inline uint32_t BossItem(unsigned dungeon, unsigned design, Quality quality) {
	return dungeon < DungeonCount && design < 3 && unsigned(quality)>=1 && unsigned(quality)<=2 ?
		ItemBegin + SharedItems + (dungeon * 3 + design) * 2 + unsigned(quality) - 1 : 0;
}
// Append exclusive families; the original seven identities remain unchanged.
inline uint32_t FinalBossItem(unsigned dungeon, unsigned band, unsigned design, Quality quality) {
	if (dungeon>=DungeonCount || band>=4 || design>=3 || unsigned(quality)<1 || unsigned(quality)>2) { return 0; }
	return BossItem(dungeon,design,quality);
}
inline int64_t Scale(int64_t value, unsigned percent) {
	if (value <= 0) { return value; }
	if (!percent) { return 0; }
	const auto limit = std::numeric_limits<int64_t>::max();
	const auto whole=value/100;
	const auto fraction=(uint64_t(value%100)*percent)/100;
	if (whole>limit/percent || uint64_t(whole*percent)>uint64_t(limit)-fraction) { return limit; }
	return whole*percent+fraction;
}
// Persisted seed; domains separate personal designs, quality and corpse rolls.
// This is deterministic random selection, never an authorization token.
inline uint64_t Mix(uint64_t value) {
	value += 0x9e3779b97f4a7c15ULL;
	value = (value ^ (value >> 30)) * 0xbf58476d1ce4e5b9ULL;
	value = (value ^ (value >> 27)) * 0x94d049bb133111ebULL;
	return value ^ (value >> 31);
}
inline unsigned Roll(uint64_t seed, uint32_t character, unsigned domain, unsigned bound) {
	if (!bound) { return 0; }
	uint64_t value=Mix(seed ^ (uint64_t(character) << 16) ^ domain);
	const uint64_t threshold=(uint64_t(0)-bound)%bound;
	while (value<threshold) { value=Mix(value); }
	return unsigned(value%bound);
}
inline std::array<unsigned, 3> BossOrder(uint64_t seed) {
	std::array<unsigned, 3> result{0, 1, 2};
	for (unsigned i = 2; i > 0; --i) {
		const auto j = Roll(seed, 0, 100 + i, i + 1);
		const auto old = result[i]; result[i] = result[j]; result[j] = old;
	}
	return result;
}
}
