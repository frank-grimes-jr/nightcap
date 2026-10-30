#pragma once
#include "bazaar_escrow.h"

namespace NightcapItemXP {
// Snapshot format is the existing complete native inventory row. GUIDs are
// regenerated at login, so compare every persisted instance field except GUID;
// leave the saved GUID and other instance fields untouched. The caller may
// change default color with the tier while retaining explicit player dye.
inline std::string UpdateSQL(NightcapBazaar::Row before, NightcapBazaar::Row after)
{
	using namespace NightcapBazaar;
	if (before.size() != Columns().size() || after.size() != before.size()) { return {}; }
	// Loot packet helpers emit lowercase hex; Bazaar's row validator uses
	// uppercase. Normalize hex spelling only, never the underlying metadata.
	for (auto *row : {&before, &after}) {
		for (auto &digit : (*row)[12]) { if (digit >= 'a' && digit <= 'f') { digit -= 'a' - 'A'; } }
	}
	try {
		const auto character = Number(before[0]);
		if (!character || character > UINT32_MAX || !ValidItem(before, static_cast<uint32_t>(character)) ||
			!ValidItem(after, static_cast<uint32_t>(character))) { return {}; }
		for (size_t i = 0; i < before.size(); ++i) {
			if (i != 2 && i != 4 && i != 12 && before[i] != after[i]) { return {}; }
		}
		if (before[2] == after[2] && before[12] == after[12]) { return {}; }
		std::string sql = "UPDATE inventory SET item_id=" + after[2] + ",color=" + after[4] + ",custom_data=X'" + after[12] + "' WHERE ";
		for (size_t i = 0; i < before.size() - 1; ++i) {
			if (i) { sql += " AND "; }
			sql += i == 12 ? "BINARY COALESCE(custom_data,'')=X'" + before[i] + "'"
				: '`' + Columns()[i] + "`=" + before[i];
		}
		return sql;
	} catch (...) { return {}; }
}
}
