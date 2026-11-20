#pragma once

#include <cstdint>

namespace NightcapAAAvailability {

// Family 150 combines the native Mastery of the Past class lines. The six
// classes from disabled family 251 never had Spell Casting Expertise access.
// Class masks here use the in-memory/client convention: bit N is class N.
inline bool WaivesPrerequisite(int ability_id, int prerequisite_id, uint32_t held_classes)
{
	constexpr uint32_t independent_classes = (1u << 2) | (1u << 3) | (1u << 4) |
		(1u << 6) | (1u << 10) | (1u << 15);
	return ability_id == 150 && prerequisite_id == 26 && (held_classes & independent_classes);
}

} // namespace NightcapAAAvailability
