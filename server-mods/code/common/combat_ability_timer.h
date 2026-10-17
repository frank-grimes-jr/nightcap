#pragma once

#include "ptimer.h"
#include "skills.h"

namespace EQ { namespace skills {
// These are persistent server timer IDs, not the RoF2 client's two timer slots.
// Preserve non-Monk and older-client grouping; the paired RoF2 proxy separates
// the six basic attacks. Tail Rake is the same skill as Dragon Punch.
inline pTimerType CombatAbilityTimer(SkillType skill, bool held_monk, bool rof2)
{
	if (held_monk && rof2) {
		switch (skill) {
		case SkillDragonPunch:
		case SkillEagleStrike:
		case SkillFlyingKick:
		case SkillKick:
		case SkillRoundKick:
		case SkillTigerClaw:
			return pTimerMonkCombatAbilityStart + skill;
		default:
			break;
		}
	}
	return rof2 && skill == SkillTigerClaw ? pTimerCombatAbility2 : pTimerCombatAbility;
}
} }
