#pragma once

#include "common/classes.h"
#include "common/repositories/skill_caps_repository.h"
#include "common/skills.h"
#include "common/types.h"

#include <functional>
#include <vector>

class SkillCaps {
public:
	struct HeldSkillEligibility {
		uint16 current_cap = 0;
		uint8 unlock_level = 0;
	};

	inline void ClearSkillCaps() { m_skill_caps.clear(); }
	SkillCapsRepository::SkillCaps GetSkillCap(uint8 class_id, EQ::skills::SkillType skill_id, uint8 level);
	uint8 GetSkillTrainLevel(uint8 class_id, EQ::skills::SkillType skill_id, uint8 level);
	static uint8 FindFirstTrainableLevel(uint8 max_level, const std::function<bool(uint8)> &has_skill_cap);
	static HeldSkillEligibility ResolveHeldSkillEligibility(
		const std::vector<uint8> &held_classes,
		const std::function<uint16(uint8)> &current_cap_for_class,
		const std::function<uint8(uint8)> &unlock_level_for_class
	);
	void LoadSkillCaps();
	void ReloadSkillCaps();
	static int32_t GetSkillCapMaxLevel(uint8 class_id, EQ::skills::SkillType skill_id);

	SkillCaps *SetContentDatabase(Database *db);

	static SkillCaps* Instance()
	{
		static SkillCaps instance;
		return &instance;
	}
private:
	Database                                    *m_content_database{};
	std::map<uint64, SkillCapsRepository::SkillCaps> m_skill_caps = {};
};
