#pragma once

#include <cstdint>

class Mob;

namespace NightcapHeroicCast {
// The next engine call takes this flag before any hooks, focus checks or child spells.
struct Cast {
	inline static thread_local bool next = false;
	static bool Take() {
		const bool value = next;
		next = false;
		return value;
	}
	template<class Fn> static auto Deliver(bool eligible, Fn fn) {
		struct Restore { bool saved; ~Restore() { next = saved; } } restore{next};
		next = eligible;
		return fn();
	}
};

// A group, AE or beam can have several original recipients. Each SpellOnTarget
// suspends the list before running hooks, including same-ID procs and reflects.
class Targets {
public:
	Targets(const Mob *caster = nullptr, uint32_t spell = 0, bool eligible = false) :
		owner(eligible ? caster : nullptr), spell_id(spell), previous(active) { active = this; }
	~Targets() { active = previous; }
	Targets(const Targets&) = delete;
	Targets& operator=(const Targets&) = delete;
	void Finish() { owner = nullptr; }
	static bool For(const Mob *caster, uint32_t spell) {
		return caster && active && active->owner == caster && active->spell_id == spell;
	}
private:
	const Mob *owner;
	uint32_t spell_id;
	const Targets *previous;
	inline static thread_local const Targets *active = nullptr;
};
}
