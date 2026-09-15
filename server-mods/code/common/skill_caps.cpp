#include "skill_caps.h"

#include "common/timer.h"

// cache the skill cap max level in the database
std::map<uint8_t, int32_t> skill_max_level = {};

uint8 skill_cap_max_level = (
	RuleI(Character, SkillCapMaxLevel) > 0 ?
		RuleI(Character, SkillCapMaxLevel) :
		RuleI(Character, MaxLevel)
);

SkillCaps *SkillCaps::SetContentDatabase(Database *db)
{
	m_content_database = db;

	return this;
}

int32_t SkillCaps::GetSkillCapMaxLevel(uint8 class_id, EQ::skills::SkillType skill_id)
{
	// pull the max value defined in the database if it exists
	auto it = skill_max_level.find((class_id * 1000000) + skill_id);
	if (it != skill_max_level.end()) {
		return it->second;
	}

	return skill_cap_max_level;
}

SkillCapsRepository::SkillCaps SkillCaps::GetSkillCap(uint8 class_id, EQ::skills::SkillType skill_id, uint8 level)
{
	if (!IsPlayerClass(class_id) || static_cast<uint32>(skill_id) > EQ::skills::HIGHEST_SKILL + 1) {
		return SkillCapsRepository::NewEntity();
	}

	const uint8 max_level = GetSkillCapMaxLevel(class_id, skill_id);
	if (level > max_level) {
		level = max_level;
	}

	const uint64_t key = (class_id * 1000000) + (level * 1000) + static_cast<uint32>(skill_id);
	auto           pos = m_skill_caps.find(key);
	if (pos != m_skill_caps.end()) {
		return pos->second;
	}

	return SkillCapsRepository::NewEntity();
}

uint8 SkillCaps::GetSkillTrainLevel(uint8 class_id, EQ::skills::SkillType skill_id, uint8 level)
{
	if (
		!IsPlayerClass(class_id) ||
		class_id > Class::PLAYER_CLASS_COUNT ||
		static_cast<uint32>(skill_id) > (EQ::skills::HIGHEST_SKILL + 1)
		) {
		return 0;
	}

	const uint8 max_level = level < skill_cap_max_level ? level : skill_cap_max_level;
	return FindFirstTrainableLevel(max_level, [this, class_id, skill_id](uint8 current_level) {
		const uint64_t key = (
			(class_id * 1000000) +
			(current_level * 1000) +
			static_cast<uint32>(skill_id)
		);
		return m_skill_caps.find(key) != m_skill_caps.end();
	});
}

uint8 SkillCaps::FindFirstTrainableLevel(uint8 max_level, const std::function<bool(uint8)> &has_skill_cap)
{
	for (uint16 current_level = 1; current_level <= max_level; ++current_level) {
		if (has_skill_cap(static_cast<uint8>(current_level))) {
			return static_cast<uint8>(current_level);
		}
	}

	return 0;
}

SkillCaps::HeldSkillEligibility SkillCaps::ResolveHeldSkillEligibility(
	const std::vector<uint8> &held_classes,
	const std::function<uint16(uint8)> &current_cap_for_class,
	const std::function<uint8(uint8)> &unlock_level_for_class
)
{
	HeldSkillEligibility result;
	bool seen[Class::PLAYER_CLASS_COUNT + 1] = {};

	for (const uint8 class_id : held_classes) {
		if (!IsPlayerClass(class_id) || class_id > Class::PLAYER_CLASS_COUNT || seen[class_id]) {
			continue;
		}
		seen[class_id] = true;

		const uint16 current_cap = current_cap_for_class(class_id);
		if (current_cap > result.current_cap) {
			result.current_cap = current_cap;
		}

		const uint8 unlock_level = unlock_level_for_class(class_id);
		if (
			unlock_level > 0 &&
			(result.unlock_level == 0 || unlock_level < result.unlock_level)
		) {
			result.unlock_level = unlock_level;
		}
	}

	return result;
}

bool SkillCaps::CanUseTrainer(
	uint8 trainer_class,
	const std::vector<uint8> &held_classes,
	bool allow_cross_class
)
{
	if (!IsPlayerClass(trainer_class) || trainer_class > Class::PLAYER_CLASS_COUNT) {
		return false;
	}

	if (allow_cross_class) {
		return true;
	}

	for (const uint8 class_id : held_classes) {
		if (class_id == trainer_class) {
			return true;
		}
	}

	return false;
}

void SkillCaps::LoadSkillCaps()
{
	const auto &l = SkillCapsRepository::All(*m_content_database);

	m_skill_caps.clear();

	for (const auto &e: l) {
		if (
			e.level < 1 ||
			!IsPlayerClass(e.class_id) ||
			static_cast<EQ::skills::SkillType>(e.skill_id) >= EQ::skills::SkillCount
			) {
			continue;
		}

		const uint64_t key = (e.class_id * 1000000) + (e.level * 1000) + e.skill_id;
		m_skill_caps[key] = e;

		const int max_level_key = (e.class_id * 1000000) + e.skill_id;
		auto      it            = skill_max_level.find(max_level_key);
		if (it != skill_max_level.end()) {
			// Key found, update the value if the new level is higher
			if (e.level > it->second) {
				it->second = e.level;
			}
			// we never want to exceed the defined rule skill cap max level
			if (it->second > skill_cap_max_level) {
				it->second = skill_cap_max_level;
			}
		}
		else {
			// Key not found, insert the new key-value pair
			skill_max_level[max_level_key] = e.level;
		}
	}

	LogInfo(
		"Loaded [{}] Skill Cap Entr{}",
		l.size(),
		l.size() != 1 ? "ies" : "y"
	);
}

void SkillCaps::ReloadSkillCaps()
{
	ClearSkillCaps();
	LoadSkillCaps();
}
