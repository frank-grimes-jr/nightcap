#pragma once
#include <algorithm>
#include <cstdint>

namespace NightcapPetScaling {
// The inheritance ceiling is independent of the pet's own equipment ceiling.
constexpr int InheritedOutput(int owner_stat)
{
	return std::min(std::max(owner_stat, 0) / 2, 375);
}

enum class CasterBonus { SpellChance, SpellDamage, DotChance, DotDamage, HealChance, HotChance };

constexpr int AAReuse(int ability, int ordinal, int native_seconds)
{
	return ability == 241 && ordinal == 1 ? 60 : ability == 60 && ordinal >= 1 && ordinal <= 6 ? 600 : native_seconds;
}

constexpr bool PermanentRabidBear(int spell)
{
	return spell == 2750 || spell == 8216 || spell == 11279 || spell == 12644 || spell == 13795 ||
		spell == 16668 || spell == 23599 || spell == 27493 || spell == 30709;
}
}
