# Backstab hand selection

At level 50 and Backstab skill 200, a 30-damage primary dagger with 7 Backstab damage beat an 8-damage secondary dagger with 18 Backstab damage only on raw weapon damage. Before the fix the server submitted base 42 with the first dagger in primary and 108 after swapping them. The corrected server submitted 108 in both orders and selected the dagger with 18 Backstab damage. The June 12 THJ notes specify using “whichever will produce the more damaging Backstab.” [THJ combat update](https://www.reddit.com/r/TheHeroesJourney/comments/1lamtdc/)

| Physical setup | Earlier submitted base | Corrected submitted base |
|---|---:|---:|
| 7 Backstab primary, 18 secondary | 42 | 108 |
| 18 Backstab primary, 7 secondary | 108 | 108 |
| Two daggers with 18 Backstab | 108 | 108, primary selected |
| Empty primary, 18 Backstab secondary | No strike | 108 |
| 7 Backstab primary, empty secondary | 42 | 42 |
| Slashing primary, 18 Backstab secondary | No strike | 108 |
| 7 Backstab primary with a +12 Backstab augment | 114 | 114 |
| 7 Backstab primary, secondary with zero intrinsic Backstab and +4 Backstab augment, 12 weapon damage and +7 damage augment | 42 | 138 |
| Neither hand holds an eligible piercer | No strike | No strike |

Both receipts contain 57 cases. They record 46 submitted hits on the baseline and 52 on the candidate, including intentional misses and generic skill controls. Each case asserts its expected damage, skill/cast callbacks and proc counts. Inventory and attached-augment pointers are checked across each action. The fixture compiles the original item-instance damage getters and uses synthetic item and augment definitions.

## Scope of the comparison

- **Normal button and class slots.** The physical controls run the complete native `Client::OPCombatAbility`, `Mob::TryBackstab`, `Mob::RogueBackstab`, `Mob::GetBaseSkillDamage` and special-damage submission paths. A Bard with Rogue in slot two and a Bard/Ranger with Rogue in slot three each changed from no strike to 108. A character without Rogue submitted no hit. An ineligible secondary by slot, class, race, level or dual-wield skill left the eligible primary at 42. A two-handed primary suppressed a synthetic stale secondary. Bot primary-only and NPC unarmed controls kept their original results.
- **Position, AA and procs.** An ordinary frontal attempt generated one primary attack fallback. Seized Opportunity permitted one full Backstab. Chaotic kept one minimum-damage strike, with a second full strike only when the frontal-double effect succeeded. Rank IX Triple Backstab, using a controlled successful double check and 45% triple-roll outcome, produced three strikes before and after, totalling 126 and 324 at the fixed damage boundary. Failed double/triple gates produced one/two strikes respectively. A killing first or second strike stopped further attempts. Each physical strike invoked one animation, one cast-on-skill callback and one attempt-proc check. A controlled miss invoked zero success-proc checks. [Existing Triple Backstab native suite](../../../tools/tests/verify_triple_backstab_native.py)
- **Bane, elemental and immunity.** Matching +16 bane made the 7-Backstab primary submit 138. With nonmatching or ignored bane, the candidate chose the 18-Backstab secondary for 108. Complete melee immunity and invulnerability produced no strikes. A magic-only target admitted the magical secondary when the primary was ineligible. The server compared target-adjusted expected elemental damage before consuming RNG. With elemental damage on both weapons, the fixture observed one native draw on the selected weapon. A low draw on an expected-stronger primary could still yield 42. For a magic-immune target, a legacy elemental primary produced 222 on the controlled draw; the corrected server excluded the immune element and submitted 108 from the secondary. The THJ source gives a hand-selection outcome. Expected-value treatment of random elemental damage and primary-on-tie are Nightcap decisions.
- **Zero and explicit damage.** Against a target requiring magical weapons, the only eligible piercing weapon had zero physical base and fully resisted elemental damage. Its resolved zero reached the attack boundary exactly once. The stronger ineligible primary contributed nothing, and no resist draw or success-proc check occurred. The generic caller's zero still requested base calculation. An explicit generic base of 31 stayed 31. The original SPA SkillAttack dispatcher and `DoMeleeSkillAttackDmg` submitted spell base 37 with both equipment orders and with both hands empty.

The harness controls the final `DoAttack` outcome to observe exactly which base, hate, animation and callbacks reach the native hit path. It passes ordinary base damage through, forces a miss where labeled, and returns a controlled 50 for a level-50 Chaotic minimum. The values above describe submitted bases or controlled outcomes. Actual mitigation, criticals, spell casting from a proc, combat-log display and encounter DPS require a running character. The original server's `ResistElementalWeaponDmg`, the candidate’s expected elemental calculation, target bane calculation, native dual-wield predicate and native item/socket damage getters all run in the fixture. Equipment class/race authorization, current skill caps, inventory, target stats, timers and network effects are controlled boundaries.

## Reproduce

From this checkout, pass the pre-change or candidate native source tree. The runner compiles the original method bodies, executes the controls, checks their results and writes the source SHA-256 values with the samples.

```powershell
python docs/combat/thj-backstab/measure.py --source <baseline-checkout>/server-mods/code --output before.json
python docs/combat/thj-backstab/measure.py --source <candidate-checkout>/server-mods/code --output after.json
```

[Baseline measurements](before.json) · [Corrected measurements](after.json) · [Driver and assertions](measure.py) · [Controlled dependencies](backstab_boundary.cpp) · [Player QA](QA.md)
