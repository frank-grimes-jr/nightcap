#pragma once

#include "zone/raid_augment.h"

namespace NightcapRaidAug {
// Projectiles and ground-targeted rain apply damage on a later zone frame.
enum class Delivery : uint8_t { Triggered, Direct, Gem };

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
	return CastOrigin(caster, spell, delivery == Delivery::Gem, delivery == Delivery::Triggered);
}
}
