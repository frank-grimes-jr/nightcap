#pragma once
#include "common/advanced_loot_protocol.h"
#include <map>

namespace NightcapLoot {
struct Preferences {
	uint32_t settings = Enabled | ApplyFilters | AutoShow;
	std::map<uint32_t, Filter> filters;
	Filter Saved(uint32_t item) const {
		const auto found = filters.find(item);
		return found == filters.end() ? Filter::Ask : found->second;
	}
	Filter Effective(uint32_t item) const { return (settings & Enabled) && (settings & ApplyFilters) ? Saved(item) : Filter::Ask; }
};

// Callers publish changed settings only after a successful write. On any
// ambiguous result they invalidate their cache and reload before continuing.
bool LoadPreferences(uint32_t character, Preferences &output);
bool SaveSettings(uint32_t character, uint32_t settings);
bool SaveFilter(uint32_t character, uint32_t item, Filter filter);
}
