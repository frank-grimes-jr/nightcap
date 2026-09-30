#include "zone/advanced_loot_preferences.h"
#include "zone/zonedb.h"

extern ZoneDatabase database;

namespace NightcapLoot {
bool LoadPreferences(uint32_t character, Preferences &output)
{
	if (!character) { return false; }
	Preferences loaded;
	auto settings = database.QueryDatabase(fmt::format(
		"SELECT settings FROM character_advloot_settings WHERE character_id={}", character), false);
	if (!settings.Success() || settings.RowCount() > 1) { return false; }
	if (settings.RowCount()) {
		auto row = settings.begin();
		uint32_t value = 0;
		if (!row[0] || !Number(row[0], value) || (value & ~AllSettings)) { return false; }
		loaded.settings = value;
	}
	auto filters = database.QueryDatabase(fmt::format(
		"SELECT item_id,filter FROM character_advloot_filters WHERE character_id={} ORDER BY item_id", character), false);
	if (!filters.Success() || filters.RowCount() > MaxResults) { return false; }
	for (auto row : filters) {
		uint32_t item = 0, filter = 0;
		if (!row[0] || !row[1] || !Number(row[0], item) || !item || !Number(row[1], filter) || filter > 4 ||
			!loaded.filters.emplace(item, static_cast<Filter>(filter)).second) { return false; }
	}
	output = std::move(loaded);
	return true;
}

bool SaveSettings(uint32_t character, uint32_t settings)
{
	if (!character || (settings & ~AllSettings)) { return false; }
	return database.QueryDatabase(fmt::format(
		"INSERT INTO character_advloot_settings (character_id,settings) VALUES ({},{}) "
		"ON DUPLICATE KEY UPDATE settings=VALUES(settings)", character, settings), false).Success();
}

bool SaveFilter(uint32_t character, uint32_t item, Filter filter)
{
	if (!character || !item || static_cast<uint32_t>(filter) > 4 || !database.GetItem(item)) { return false; }
	// Saving Ask removes the automatic choice. New-only view includes these items.
	if (filter == Filter::Ask) {
		return database.QueryDatabase(fmt::format(
			"DELETE FROM character_advloot_filters WHERE character_id={} AND item_id={}", character, item), false).Success();
	}
	return database.QueryDatabase(fmt::format(
		"INSERT INTO character_advloot_filters (character_id,item_id,filter) VALUES ({},{},{}) "
		"ON DUPLICATE KEY UPDATE filter=VALUES(filter)", character, item, static_cast<uint32_t>(filter)), false).Success();
}
}
