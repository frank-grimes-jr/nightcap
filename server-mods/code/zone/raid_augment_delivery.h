#pragma once

#include "zone/raid_augment.h"

namespace NightcapRaidAug {
// Projectiles and ground-targeted rain apply damage on a later zone frame.
enum class Delivery : uint8_t { Triggered, Direct, Gem };

// The queue stores a separate heroic-cast flag in the same byte. Direct raid
// eligibility includes clicks, so it cannot identify a player spell by itself.
constexpr Delivery WithHeroicCast(Delivery delivery, bool eligible)
{
	return static_cast<Delivery>(static_cast<uint8_t>(delivery) | (eligible ? 0x80 : 0));
}
constexpr bool HasHeroicCast(Delivery delivery)
{
	return (static_cast<uint8_t>(delivery) & 0x80) != 0;
}

inline Delivery CaptureDelivery(const Mob *caster, uint32_t spell)
{
	const auto *origin = CastOrigin::current;
	if (!origin || origin->caster != caster || origin->spell != spell || origin->triggered) {
		return Delivery::Triggered;
	}
	return origin->gem ? Delivery::Gem : Delivery::Direct;
}

inline CastOrigin OnDelivery(const Mob *caster, uint32_t spell, Delivery delivery)
{
	delivery = static_cast<Delivery>(static_cast<uint8_t>(delivery) & 0x7f);
	return CastOrigin(caster, spell, delivery == Delivery::Gem, delivery == Delivery::Triggered);
}
}
