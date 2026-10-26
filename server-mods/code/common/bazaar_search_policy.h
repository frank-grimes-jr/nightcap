#pragma once
#include <cstdint>
#include <string>

namespace NightcapBazaar {
// SQL projection of NightcapEquipment::ApplyRacePolicy, evaluated before the
// native result LIMIT. The DB/native equivalence regression owns this boundary.
inline std::string RacePredicate(uint32_t bit)
{
	return " AND ((items.races & " + std::to_string(bit) + ") = " + std::to_string(bit) +
		" OR (items.itemclass=0 AND (items.classes & 65535)<>0 AND (items.races & 65535)<>0 "
		"AND ((items.slots & 8388607)<>0 OR items.augtype<>0)))";
}
}
