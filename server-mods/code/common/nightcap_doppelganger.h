#pragma once

namespace NightcapDoppelganger {
enum class Role { Hot, Heal, Rune, Buff, ResistDebuff, Debuff, Dot, Damage, Unsupported };

inline bool Wants(Role role, float hp)
{
	if (role == Role::Heal) return hp < 50.0f;
	if (role == Role::Hot) return hp >= 50.0f && hp <= 75.0f;
	return role != Role::Unsupported;
}

inline bool Interrupt(Role role, float hp)
{
	return (role == Role::Heal && hp > 75.0f) || (role == Role::Hot && hp < 40.0f);
}

inline int Priority(Role role, int level)
{
	return static_cast<int>(role) * 1000 - level;
}

// The clone is a combat assistant, not a second inventory/transport controller.
// Unknown, recursive trigger, summon, charm and resource-conversion effects are
// excluded explicitly; expanding this list requires target/resource tests.
inline bool CombatEffect(int effect)
{
	switch (effect) {
	case 0: case 1: case 2: case 3: case 4: case 5: case 6: case 7:
	case 8: case 9: case 10: case 11: case 15: case 20: case 21:
	case 23: case 46: case 47: case 48: case 49: case 50: case 55:
	case 59: case 69: case 79: case 97: case 98: case 99: case 100:
	case 111: case 119: case 148: case 149: case 254:
		return true;
	default:
		return false;
	}
}
}
