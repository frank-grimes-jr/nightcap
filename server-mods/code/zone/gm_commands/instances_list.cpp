#include "zone/client.h"
#include "common/zone_store.h"

// Player-facing list of the character's open instances with remaining time (#7).
// The GM #instance command manages instances; this one only displays.
void command_instances_list(Client *c, const Seperator *sep)
{
	auto results = database.QueryDatabase(
		fmt::format(
			"SELECT il.id, il.zone, il.version, il.start_time, il.duration, il.never_expires "
			"FROM instance_list il "
			"JOIN instance_list_player ilp ON ilp.id = il.id "
			"WHERE ilp.charid = {} "
			"ORDER BY il.start_time",
			c->CharacterID()
		)
	);

	if (!results.Success() || results.RowCount() == 0) {
		c->Message(Chat::White, "You have no open instances.");
		return;
	}

	c->Message(Chat::White, "Your open instances:");

	const auto now = static_cast<uint32>(time(nullptr));
	for (auto row : results) {
		const auto instance_id = Strings::ToUnsignedInt(row[0]);
		const auto zone_id     = Strings::ToUnsignedInt(row[1]);
		const auto start_time  = Strings::ToUnsignedInt(row[3]);
		const auto duration    = Strings::ToUnsignedInt(row[4]);
		const bool never_expires = Strings::ToInt(row[5]) != 0;

		std::string remaining = "never expires";
		if (!never_expires) {
			const auto expires = start_time + duration;
			if (expires <= now) {
				remaining = "expired";
			} else {
				const auto seconds = expires - now;
				remaining = fmt::format(
					"{}h {}m remaining",
					seconds / 3600,
					(seconds % 3600) / 60
				);
			}
		}

		c->Message(
			Chat::White,
			fmt::format(
				"  {} (instance {}) - {}",
				ZoneLongName(zone_id, true),
				instance_id,
				remaining
			).c_str()
		);
	}
}
