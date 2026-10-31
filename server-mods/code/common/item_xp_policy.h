#pragma once
#include <algorithm>
#include <cstdint>

namespace NightcapItemXP {
constexpr uint64_t Unit = 1000000;
constexpr uint64_t MaxProgress = 480 * Unit;
constexpr const char *Key = "nightcap_item_xp";

// Candidate calibration: 80/160/240 comparable-kill equivalents. At 60–120
// equivalents/hour the complete path takes 4–8 hours. This is a tuning target,
// not a claim of measured live combat throughput.
inline uint64_t Cost(uint8_t tier)
{
	constexpr uint64_t costs[] = {80 * Unit, 160 * Unit, 240 * Unit};
	return tier < 3 ? costs[tier] : 0;
}

// Full modified combat XP, before AA allocation or character-level clamping.
// Reference kill = level^2 * 75 * 3.5 * 0.65 = level^2 * 1365 / 8.
// 0.65 is the dated normal-XP baseline, not the active AA multiplier. Actual
// zone/rate bonuses remain part of earned XP; never multiply them twice.
inline uint64_t Award(uint64_t experience, uint8_t level)
{
	if (!level) { return 0; }
	const uint64_t denominator = uint64_t{1365} * level * level;
	constexpr uint64_t scale = 8 * Unit;
	const uint64_t whole = experience / denominator;
	if (whole >= MaxProgress / scale) { return MaxProgress; }
	// The remainder product is bounded by 1365*255^2*8,000,000 < 2^64.
	return std::min(MaxProgress, whole * scale + (experience % denominator) * scale / denominator);
}

struct Progress {
	bool valid = false;
	uint8_t tier = 0;
	uint64_t progress = 0;
};

inline Progress Advance(uint8_t tier, uint64_t progress, uint64_t award)
{
	if (tier > 3 || (tier == 3 ? progress != 0 : progress >= Cost(tier))) { return {}; }
	if (tier == 3) { return {true, 3, 0}; }
	uint64_t remaining = progress + std::min(award, MaxProgress);
	while (tier < 3 && remaining >= Cost(tier)) {
		remaining -= Cost(tier);
		++tier;
	}
	return {true, tier, tier == 3 ? 0 : remaining};
}
}
