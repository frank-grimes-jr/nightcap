# Backstab hand selection

The June 12 THJ note describes using either equipped hand, whichever produces the stronger Backstab. The reviewed Nightcap baseline checked the primary hand at the skill gate, again for target eligibility, and again to compute damage. All three matter: changing only the entry check could allow a stab with damage derived from the wrong item. [THJ combat update](https://www.reddit.com/r/TheHeroesJourney/comments/1lamtdc/).

## Confirmed cases

In a level-50 fixture with Backstab skill 200, the two piercers had ordinary weapon damage 30 and 8, but Backstab damage 7 and 18, respectively. The predecessor submitted base 42 or 108 depending on which was in primary. The correction submitted 108 in either order, and 108 with only the eligible secondary. A Triple Backstab control submitted three hits of 108. These are skill base values with controlled damage boundaries; criticals, mitigation and the encounter can change the final hit. [Before](before.json) · [After](after.json).

An eligible offhand requires the character to be able to dual wield in its current setup. The comparison includes augments, the weapon-damage fallback when the host has no Backstab stat, applicable bane, and the target's expected elemental resistance. The chosen weapon rolls its actual elemental damage once per strike; the comparison consumes no combat random draws. A magic-immune target can still take eligible physical Backstab damage. A held Rogue can dispatch the normal skill through the combat-ability input with the same skill and reuse checks. Explicit spell-supplied Backstab damage keeps its separate calculation.

## In-game QA

1. Use a level-50 character with Rogue and Dual Wield trained. Record weapon IDs, weapon damage, Backstab damage, augments, skill and AA ranks. Keep all other gear and buffs fixed. Use two equippable one-hand piercers with visibly different Backstab damage.
2. Position behind the same stationary NPC in a private instance. Use Backstab with the stronger piercer in primary and then with it in secondary. Compare repeated ordinary landed Backstabs, keeping misses, criticals, assassinations, additional strikes and item procs in separate counts. Both arrangements should select the stronger eligible piercer. The two items remain in their original slots.
3. Retest with an eligible secondary piercer and a nonpiercing primary, then with only a primary piercer, then with no eligible piercer. The first two combinations should backstab. The last should show the normal weapon-required result. For a tie, primary takes precedence.
4. Try weapons whose ordinary damage rating favors the opposite hand from their Backstab damage. Repeat with an augment and a target for which only one piercer passes a magic or bane restriction. Verify the eligible item wins and an immune target still takes no damage.
5. With identical legal AA ranks, repeat frontal and rear attempts, including Chaotic Stab or Triple Backstab if owned. Compare reuse, attack counts and proc counts. Weapon selection grants no additional strikes. Record in-game behavior and balance separately from automated native tests.
