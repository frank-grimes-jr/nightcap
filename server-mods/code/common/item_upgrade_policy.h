#pragma once
#include "zone_hunt_catalog.h"
#include <cstdint>
#include <string>

namespace NightcapUpgrade {
constexpr uint32_t NpcID = 999820;
constexpr uint32_t ContainerID = 900620;
constexpr uint64_t Revision = 2026101201;
constexpr unsigned Copies = 4;

inline uint32_t LegacyTarget(uint32_t id)
{
	return ((id > 200000 && id < 400000) || (id > 400000 && id < 600000)) ? id + 200000 : 0;
}

inline uint32_t ZoneTarget(uint32_t id)
{
	return id >= 940000 && ((id - 940000) % 4 == 1 || (id - 940000) % 4 == 2)
		? NightcapHunt::NextTier(id) : 0;
}

inline unsigned ZoneCopies(uint32_t id)
{
	return ZoneTarget(id) ? Copies : 3;
}

inline bool NamesMatch(const std::string &input, const std::string &output, bool exalted)
{
	const std::string from = exalted ? " (Exalted)" : " (Polished)";
	const std::string to = exalted ? " (Ascended)" : " (Exalted)";
	return input.size() > from.size() && input.compare(input.size() - from.size(), from.size(), from) == 0 &&
		output == input.substr(0, input.size() - from.size()) + to;
}
}
