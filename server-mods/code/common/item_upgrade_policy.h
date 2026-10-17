#pragma once
#include "zone_hunt_catalog.h"
#include <cstdint>
#include <string>

namespace NightcapUpgrade {
constexpr uint32_t NpcID = 999820;
constexpr uint32_t ContainerID = 900620;
constexpr uint64_t Revision = 2026101201;
constexpr unsigned ContainerSlots = 4;

inline uint32_t LegacyTarget(uint32_t id)
{
	return (id > 0 && id < 600000 && id % 200000 != 0) ? id + 200000 : 0;
}

inline uint32_t ZoneTarget(uint32_t id)
{
	return NightcapHunt::NextTier(id);
}

inline unsigned ZoneCopies(uint32_t id)
{
	return ZoneTarget(id) && (id - 940000) % 4 != 0 ? 4 : 3;
}

inline unsigned BoxCopies(uint32_t id)
{
	if (LegacyTarget(id)) { return id < 200000 ? 3 : 4; }
	return ZoneTarget(id) ? ZoneCopies(id) : 0;
}

inline bool NamesMatch(const std::string &input, const std::string &output, uint32_t id)
{
	if (!LegacyTarget(id)) { return false; }
	const std::string from = id < 200000 ? "" : id < 400000 ? " (Polished)" : " (Exalted)";
	const std::string to = id < 200000 ? " (Polished)" : id < 400000 ? " (Exalted)" : " (Ascended)";
	return input.size() > from.size() && input.compare(input.size() - from.size(), from.size(), from) == 0 &&
		output == input.substr(0, input.size() - from.size()) + to;
}
}
