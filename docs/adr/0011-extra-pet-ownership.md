# ADR 0011: Keep registered multiclass pets owned during native processing

> Current status (2026-09-15): implemented server/AA/PoK candidates are deployed for live QA; main gameplay acceptance remains pending. See [current status](../status.md). The dated evidence below retains its original scope and is not a current deployment checklist.


Date: 2026-09-12. Status: candidate verified in the isolated diagnostic; not deployed.

## Problem

`spell_effects.cpp` registers secondary/tertiary class summons in the client's
extra-pet map, then restores its primary pet ID. `Mob::GetOwner` and
`GetOwnerOrSelf` recognized only that primary ID. Their failure path clears the
owner and depops ordinary pets. In native MAG/NEC/SHM controls, Invoke Death (443)
and Frenzied Spirit (166) disappeared after summoning, leaving stale map entries.
This occurred with either summon order and all tested AA budgets. It made a
three-pet balance calculation invalid before any numerical tuning.

## Decision

Both native owner lookups accept the primary pet ID or an explicitly registered
extra pet of a client owner. They still require a real owner entity. An owner ID
alone does not confer membership. Unregistered pets retain the original
detach/depop behavior; swarm fallback and non-client primary ownership are unchanged.
The correction is shared in a local helper in `mob.cpp`, with no new public API.

Merely restoring `ownerid` after each lookup would retain stale pets and repeatedly
trigger depop. Disabling owner checks globally would weaken ordinary pet semantics.
The explicit registry already represents the intended multiclass ownership contract.

## Evidence and limits

The 13 original controls reproduced 10 roster failures. The candidate passes all
13 plus negative checks for both owner lookup methods after removing a pet from
the registry. Eight caster/monk encounter reports remain byte identical. See
`../balance/native-pet-ownership.md` for inputs, measurements and reproduction.

This does not settle spell ownership after global class-level widening, extra-pet
commands, zoning/persistence, charm/swarm/bot parity, pet equipment or pet fights.
The existing extra-command broadcaster calls `Attack` directly; its range, hate,
movement and cooldown behavior still needs native controls. No combat result is
inferred from these stationary preparation checks. Full fresh-source compilation
and manual in-game QA remain required before promotion.

## In-game QA before promotion

1. In the test build, use a non-GM level-50 MAG/NEC/SHM character with sufficient
   mana and Malachite (10015) / Bone Chips (13073). In Solusek B, clear a safe area
   near the recorded diagnostic position (-861, -1395, 104.88).
2. Cast Greater Conjuration: Water (633), Invoke Death (443), and Frenzied Spirit
   (166) through ordinary spell gems. All three should remain visible and owned
   after at least 12 seconds. Repeat with Necromancer or Shaman summoned first.
3. Cast Burnout III (107) on the water pet. Check its buff and haste, while both
   extra pets remain. Repeat the recorded 0/100/200/500 AA allocations, holding
   gear fixed; compare pet HP to the diagnostic, including actual spent points.
4. On an unfocused zero-AA character, omit Malachite: the water summon must fail.
   Supply it and retry: one reagent is consumed. Repeating a primary summon must
   not create a second primary pet. Test replacement of each extra-class pet.
5. Exercise dismissal, death, zoning/relogging and resummoning, plus ordinary
   single-class pets, charm, swarm and bot paths. Verify ownership cleanup and
   lack of orphan pets. Extra-pet command checks remain a separate prerequisite;
   a surviving pet alone is not sufficient approval for a boss balance baseline.

Do not promote to main without the owner's in-game sign-off.
