#pragma once

#include <cstdint>
#include <string>

namespace NightcapQuestItems {
// Only ordinary quality variants satisfy a request for the Normal item.
// Explicit qualities, epic progression, hunt and dungeon catalogs retain exact IDs.
template<class Item>
bool Matches(const Item *handed, const Item *required)
{
	if (!handed || !required) { return false; }
	if (handed->ID == required->ID) { return true; }
	if (required->ID == 0 || required->ID >= 200000 || handed->ID <= required->ID) { return false; }
	const auto offset = handed->ID - required->ID;
	const char *suffix = offset == 200000 ? " (Polished)" :
		offset == 400000 ? " (Exalted)" : offset == 600000 ? " (Ascended)" : nullptr;
	return suffix && std::string(required->Name).size() > 0 &&
		std::string(handed->Name) == std::string(required->Name) + suffix;
}
}
