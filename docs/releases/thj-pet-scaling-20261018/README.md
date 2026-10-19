# THJ pet and shared scaling candidate — October 18, 2026

Status: built candidate; not deployed or accepted in game. See
[Implementation and handoff](IMPLEMENTATION.md) for completed behavior, exact
evidence, deliberate limits and remaining release gates.
Base: origin/main a8e0a91. The paired build uses fingerprinted retained production
sources in an isolated tree; repository overlays are not a complete build tree.

The owner authorized the researched pet implementation plan, coordination with
Warrior/Paladin/Monk (WPM), and a permanent, independently removable Rabid Bear
benefit and illusion. Research evidence is in the originating chat's
`outputs/nightcap-minion-master-audit-and-plan.txt` and WPM audit.

## Contract and implementation order

1. Persistent equipment: fifteen equipped items for Mage pets, eight for other
   class pets, chosen from normal wearable locations. Preserve the existing eight
   locations and their database IDs. Add weapons, jewelry and the second wrist.
   Native worn-slot eligibility and duplicate-location limits remain. Two-handed
   weapons occupy one budget entry and exclude the secondary hand; the freed
   budget can equip another armor or jewelry location. Preserve every instance
   field and augment, transaction preimages and commit-uncertainty quarantine.
   Present all locations through a paged, versioned client snapshot.
2. Feed owned permanent pets' actual weapon instances to proc execution. Make
   independent innate/augment attempts explicit for those pets. Preserve ordinary
   hostile NPC behavior. Keep native template melee damage/delay until historical
   evidence establishes a replacement; conflicting anecdotes are not a formula.
3. Shared player SD/HA ceiling 750, preserving earned Hunt headroom. Pet inheritance
   is live: min(max(owner effective item stat, 0) / 2, 375), added once to the pet's
   own item contribution. Keep inherited and own-equipment caps distinct. Apply
   consistent DD, DoT, heal and proc getters; pet-specific focus and caster AA
   transfer must not empower hostile or charmed NPCs. Use the same player formula
   for WPM healing/procs and caster controls.
4. Friendly-pet healing and whole-roster buff delivery; curated AA depth and reuse;
   coexisting pet buff lines; independently measured Bard runes and Enchanter
   Doppelganger support. Preserve native ownership and purchased progression.
5. Essential item/proc effects and earned level-65/PoP progression. Any missing
   historical numeric target remains identified as calibration, not THJ parity.
6. Rabid Bear: split the illusion from the gameplay benefit, make both permanent
   and removable, preserve independent dismissal across zoning, retain cooldowns.

## Proof and release boundary

Execute native policy and transaction tests, real temporary-table rehearsals,
client parser/control tests, full native compilation and an independent review.
Validate all three pet variants, class orders, WPM and a caster control, including
death, resummoning, zoning, suspension, class changes and recovery. Native-client
visual/combat acceptance is separate from compilation and unit tests.

Pair schema, server, spell data, generated item cache and signed pet client UI.
Any rule-catalog change requires matching world and zone. Production activation
uses a reviewed maintenance deployment and preservation checks. Reverting to the
eight-slot binary requires reclaiming equipment in newly supported locations;
never discard player items or restore an old character snapshot.

Exact completed and outstanding checks are recorded in IMPLEMENTATION.md and evidence/.
