#ifndef EQEMU_AA_PROGRESSION_H
#define EQEMU_AA_PROGRESSION_H

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <limits>

namespace AAProgression {

// Keep all allocation math wide and validate before narrowing client input.
inline uint64_t LevelShare(uint64_t award, uint32_t allocation)
{
	const auto percent = 100 - std::min(allocation, uint32_t(100));
	return (award / 100) * percent + (award % 100) * percent / 100;
}

// Fixed stored units preserve existing AA progress through level changes.
// Scale awards by actual level boundaries, including awards crossing levels.
template <typename Threshold>
uint64_t Award(uint64_t full_xp, uint64_t level_xp, uint64_t current_xp,
	uint16_t level, uint16_t max_level, uint32_t allocation, uint32_t passive,
	uint32_t points_per_level, uint32_t units_per_point, Threshold threshold)
{
	if (!full_xp || !level || level > 126 || !points_per_level || !units_per_point) {
		return 0;
	}
	allocation = std::min(allocation, uint32_t(100));
	passive = std::min(passive, uint32_t(100));
	max_level = std::max(level, std::min(max_level, uint16_t(126)));
	const uint32_t weight = allocation * 100 + passive * (100 - allocation);
	const long double units = static_cast<long double>(points_per_level) * units_per_point * weight / 10000.0L;
	const long double limit = std::numeric_limits<uint32_t>::max();
	long double result = 0;

	while (full_xp) {
		const uint64_t start = threshold(level);
		const uint64_t end = threshold(level + 1);
		if (start == 0xFFFFFFFF || end == 0xFFFFFFFF || end <= start) {
			return 0;
		}
		const uint64_t span = end - start;
		// At cap (or with no normal XP), use the same level span indefinitely.
		if (!level_xp || level >= max_level) {
			result += units * full_xp / span;
			break;
		}
		current_xp = std::max(current_xp, start);
		if (current_xp >= end) {
			++level;
			continue;
		}
		const uint64_t segment = std::min(level_xp, end - current_xp);
		const long double scale = units * full_xp / level_xp;
		// Endpoint differences preserve tiny passive awards within a level.
		result += std::floor(scale * (current_xp - start + segment) / span)
			- std::floor(scale * (current_xp - start) / span);
		if (result >= limit || segment == level_xp) {
			break;
		}
		// Use the same full-XP/level-XP ratio across the remaining boundaries.
		// Carry the rational proportion in the coefficient instead of rounding XP.
		long double remaining = static_cast<long double>(level_xp - segment);
		++level;
		while (remaining > 0) {
			const uint64_t next_start = threshold(level);
			const uint64_t next_end = threshold(level + 1);
			if (next_start == 0xFFFFFFFF || next_end == 0xFFFFFFFF || next_end <= next_start) {
				return 0;
			}
			const uint64_t next_span = next_end - next_start;
			if (level >= max_level) {
				result += scale * remaining / next_span;
				remaining = 0;
			} else {
				const auto part = std::min(remaining, static_cast<long double>(next_span));
				result += std::floor(scale * part / next_span);
				remaining -= part;
				++level;
			}
			if (result >= limit) {
				break;
			}
		}
		break;
	}
	return static_cast<uint64_t>(std::min(limit, std::max(0.0L, std::floor(result))));
}

}
#endif
