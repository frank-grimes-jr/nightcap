# 0057: Give Throw Stone a flat Spell Damage contribution

Date: 2026-10-09. Status: accepted for main/server promotion by the owner;
gameplay acceptance pending.

The owner requested that Throw Stone use Spell Damage. Spell 5225 already reaches
the direct-damage handler with base damage 1. The pinned October 4 client spell
file allows item modifiers, while the October 7 local database backup has flat
percentage scaling enabled with a 250 item-stat cap. That combination yields only
3 damage at the cap, and ordinary level/timing restrictions can further prevent
scaling. Neither snapshot is a fresh production query.

Use `base damage + max(0, effective Spell Damage)` for ordinary player, bot and
mercenary casts of this spell. This is the stated working interpretation of the
request; the owner subsequently authorized main/server promotion of the completed
change. Preserve
the already-applied stat cap, existing spell-critical multiplier and downstream
defenses. Respect `no_heal_damage_item_mod`; do not apply the usual percentage
bonus a second time. NPC casts and the separate reflection path remain unchanged.

Alternatives: raising the base and retaining percentage scaling changes ungeared
damage and spell data; changing global scaling affects every spell and heal.
The narrow exception leaves Throw Stone at 1 with no Spell Damage, requires only
a zone rebuild, and avoids either broader change. At 250 Spell Damage the ordinary
hit is 251, approximately 25.1 raw DPS at its existing 10-second reuse, before
criticals, defenses and other modifiers. This is calibration, not encounter proof.

Reassess the coefficient only against representative legal multiclass builds and
progression stages. [Verification and exact QA](../releases/throw-stone-20261009.md).
