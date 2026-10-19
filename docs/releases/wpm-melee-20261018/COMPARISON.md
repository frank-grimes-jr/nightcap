# Native WPM and pet comparison

All26 scenarios executed and the recorded mechanics assertions passed. These are
isolated native diagnostics, not final balance or client acceptance.

| Case | Outcome | Seconds | Effective DPS | AA spent | Final HP |
|---|---|---:|---:|---:|---:|
| wpm-shield-zero | npc_death | 46.5 | 691.6 | 0 | 9246 |
| wpm-dual-zero | npc_death | 54.4 | 591.6 | 0 | 8895 |
| wpm-twohand-zero | npc_death | 78.4 | 411.7 | 0 | 8408 |
| wpm-shield-max | npc_death | 11 | 2911.2 | 2074 | 12682 |
| wpm-dual-max | npc_death | 13 | 2465.1 | 2074 | 12330 |
| wpm-twohand-max | npc_death | 15.1 | 2122.3 | 2074 | 11352 |
| wpm-shield-undead-max | npc_death | 7.15 | 4478.7 | 2074 | 12852 |
| pet-bare-zero | timeout | 180 | 91.3 | 0 | 6249 |
| pet-equipped-zero | boss_death | 93.4 | 346.3 | 0 | 6764 |
| pet-bare-max | boss_death | 173.4 | 188.3 | 2085 | 8851 |
| pet-equipped-max | boss_death | 71.3 | 452.4 | 2085 | 7696 |
| wpm-shield-heroic-off | npc_death | 12.15 | 2637.5 | 2074 | 12572 |
| wpm-shield-max-seed-2718 | npc_death | 8.25 | 3881.6 | 2074 | 12140 |
| pet-equipped-max-seed-2718 | boss_death | 56.8 | 567 | 2085 | 8914 |
| wpm-classic50-zero | timeout | 180 | 126.6 | 0 | 5611 |
| wpm-classic50-max | npc_death | 18.2 | 1762 | 2074 | 9012 |
| caster65-zero | npc_death | 79.9 | 403.1 | 0 | 5759 |
| caster65-max | npc_death | 46.95 | 685 | 2163 | 6723 |
| pet-pop65-bare-max | boss_death | 62.15 | 518.6 | 2085 | 9136 |
| pet-pop65-equipped-max | boss_death | 17.45 | 1836.4 | 2085 | 7641 |

## Verified mechanics

- 26 input/output hashes and diagnostic binary match recorded execution
- Canonical AA costs, including zero-cost baseline ranks, preserved; every supplied budget fully accounted
- All six WPM class orders have identical recorded combat capability state
- Shield removal/restoration clears/restores Holy Shield, Diaku and Marr healing
- Shield Specialist100%, six Way of Steel contributions and nonrecursive focus controls
- Native WPM encounters exercise all six skill timers and earned Rage60s activation
- Fists of Fury, haste fragment, Diaku, Healing Fragment, Holy rune, Blessing and Healing Light observed
- Native Holy rune absorption and successful Mend pulse/cooldown recorded
- All three equipped pet classes retain15/8/8 items and own stats plus bounded half-owner inheritance
- Across equipped pet encounters all three classes emit innate weapon, healing augment and rune augment effects
- Companion Fury IV purchased through native gates with actual RoF2 mask

## Limits

- Native diagnostic clock/packet adapters; no actual RoF2 render or user gameplay acceptance
- Captured Nagafen55 single-target encounter; no pack, raid or long-duration balance certification
- Class permutations are stat/shield-swap probes; combat uses Warrior-first WPM
- Seed1729 plus two seed2718 repeats do not establish statistical superiority
- Explicit gear and maximum trained skills; max stages spend2074 WPM/2085 pet AA points
- Damage sums depth-zero HP loss capped at zero terminal HP; includes replacement of NPC regeneration
- Healing ledger is HealDamage only, excludes regeneration/Mend; spell IDs may be65535 at native call sites
- Pet runes and healing proved through native effects/state; player ledger totals do not describe pet sustain
- Bare/equipped pet comparisons retain fixed Classic support gems, with separate PoP summon cases
- No production content, characters, runtime, signed-client or wiki changes
