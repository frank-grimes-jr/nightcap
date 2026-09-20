# Three class pets and shared controls

## Accepted intent

Allow up to three persistent summoned class pets, one for each held class that
can summon a pet. Duplicate summons from the same class cannot create another
active pet. The ordinary pet window commands all owned class pets together;
attack, back off, follow, guard, sit/stand, taunt and supported advanced commands
retain native safety and AA/type restrictions. Each class pet uses its existing
eight-slot armor loadout without item duplication or cross-class assignment.

After pet completion, assess moving the starting hub to the East Commonlands
tunnel near Shady Swashbuckler. Produce a concrete grounded arrangement with
spaced spell/tome merchants and clickable travel portals before changing the
starting zone. The user's wording is to consider this move; do not silently
migrate characters or delete the current hub during the assessment.

## Current failures

- Live spells_new class columns are widened by multiclass selection. The current
  summoner infers ownership from those columns, assigning Mage summons to other
  classes and preventing a valid three-pet roster.
- The primary-pet ID is coupled to character class 1. Pet commands other than
  attack early-return when that pet is missing, despite surviving class pets.
- Extra-pet movement uses a separate incomplete switch: sit lacks appearance and
  interrupt handling; advanced buttons are not broadcast.
- Armor identifies the primary pet by character class rather than summon class.

## Implementation and proof

1. Generate immutable pet spell ownership from the preserved original RoF2 file
   (SHA256 bae7ba7d897962f67581e3e731b94f4a31898d160c30c2edb74912b21aa11880).
   Tests cover class permutations, shared spells, level gates, unavailable classes
   and unclassified item/AA summons. Do not alter widened spell access globally.
2. Use a per-class registry for all permanent summons and a separate native pet
   window representative. Enforce ownership, live NPC status and class identity;
   handle representative death/dismissal and class release safely. Keep charms
   and temporary swarm pets on their native paths.
3. Apply one native command implementation to the validated roster. Resolve
   toggle intent once for the roster; retain each pet's fear, animation/AA,
   target, range and line-of-sight checks. Armor uses the same class lookup.
4. Extend the isolated native runtime to execute real summons and command packets,
   inspect per-pet state, and test duplicates, all six class orders, representative
   loss, malformed/stale references and separate armor loads. Build zone/world,
   run focused regression checks and independent review before deployment.
5. Document exact owner in-game QA and preserve existing inventory transactions.

The previous silent-client release is complete and not changed by this work.
Pet persistence across zoning/relogging must be evaluated explicitly; losing all
but the representative at each zone boundary is not a completed three-pet UX.
