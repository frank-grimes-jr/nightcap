#pragma once

#include "nightcap_sympathetic_eras.h"
#include <cstdint>

class Mob;

namespace NightcapSympathetic {
constexpr uint16_t StrikeBuff = 44379, HealingBuff = 44380;
constexpr int StrikeAmount = 48, HealingAmount = 48;
constexpr int ShareDivisor = 20;

// This result is passed only down the original single-target delivery. A
// nested proc, recourse, reflect, tick or twin starts its own ordinary path.
enum class Effect : uint8_t { None, Strike, Healing, WornHeal };
struct Cast {
	Effect effect = Effect::None;
	Mob *recipient = nullptr;
	uint16_t recipient_id = 0;
	bool landed = false;
	int64_t largest_hp = 0;
	bool *bolt_worn_heal = nullptr;
	bool worn_heal = false;

	// Only the immediately invoked native entry point may accept this receipt.
	// Take() clears it before any callbacks. Nested calls and later ticks have
	// no ambient original-cast state; callers explicitly forward each hop.
	inline static thread_local Cast *next = nullptr;
	static Cast *Take() { auto *cast = next; next = nullptr; return cast; }
	template<class Fn>
	static bool Deliver(Cast *cast, Fn fn) {
		struct Restore { Cast *saved; ~Restore() { next = saved; } } restore{next};
		next = cast;
		return fn();
	}

	void Record(Line line, int64_t amount) {
		if (amount > 0 && (line == Line::Strike ? effect == Effect::Strike :
			(effect == Effect::Healing || effect == Effect::WornHeal))) {
			landed = true;
			if (amount > largest_hp) { largest_hp = amount; }
		}
	}
	// Divide before narrowing. One cast uses its largest slot, never the sum.
	int Bonus() const {
		const int maximum = effect == Effect::Strike ? StrikeAmount : HealingAmount;
		const auto portion = largest_hp / ShareDivisor;
		return portion < maximum ? static_cast<int>(portion) : maximum;
	}

};

// Native group/raid loops invoke SpellOnTarget once per real recipient.
// Observe only a worn child with the matching caster and spell. Nested
// SpellFinished/SpellOnTarget calls pause this group, including same-ID procs.
class WornGroup {
public:
	WornGroup(Cast *cast = nullptr, const Mob *caster = nullptr, uint16_t spell = 0) :
		result(cast), owner(caster), spell_id(spell), previous(active) { active = this; }
	~WornGroup() { active = previous; }
	WornGroup(const WornGroup &) = delete;
	WornGroup &operator=(const WornGroup &) = delete;

	static Cast *For(const Mob *caster, uint16_t spell) {
		return active && active->owner == caster && active->spell_id == spell ? active->result : nullptr;
	}
private:
	Cast *result;
	const Mob *owner;
	uint16_t spell_id;
	const WornGroup *previous;
	inline static thread_local const WornGroup *active = nullptr;
};

// Spell and weapon projectiles share tProjatk. The weapon-only fields
// are never read by archery/throwing while the discriminator is Conjuration.
// Each allocation overwrites its own payload, including untracked spells.
template<class Projectile>
void StoreBolt(Projectile &p, Effect effect, uint32_t spawn_time)
{
	p.ammo_slot = static_cast<int>(effect);
	p.ranged_id = spawn_time;
	p.disable_procs = false; // spell payload: a worn heal already landed at launch
}

template<class Projectile>
Effect BoltEffect(const Projectile &p, uint32_t spawn_time)
{
	if (p.ranged_id != spawn_time) { return Effect::None; }
	const auto effect = static_cast<Effect>(p.ammo_slot);
	if (effect == Effect::Strike || (effect == Effect::Healing && !p.disable_procs)) { return effect; }
	return Effect::None;
}
}
