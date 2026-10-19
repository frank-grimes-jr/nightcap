# Combined native item/spell and WPM/pet comparison

All 47 scenarios executed and the recorded mechanics assertions passed. These are
isolated native diagnostics, not final balance or client acceptance.

The same-item controls show a material redistribution: WPM shield DPS rises
from2911.2 to4510.3, the fixed caster controller falls from685 to225.4, and
equipped Classic pets fall from452.4 to289.9. The maximum-AA WPM fixture
kills captured Nagafen in7.1 seconds. This is a required burst/sustain QA
gate, not a balance approval. Low-base spells and ordinary ticks gain;
compare cheaper spell ranks and DoT rotations before generalizing the caster result.

| Case | Outcome | Seconds | Effective DPS | AA spent | Final HP |
|---|---|---:|---:|---:|---:|
| wpm-shield-zero | npc_death | 45.15 | 712.3 | 0 | 9323 |
| wpm-dual-zero | npc_death | 51.7 | 622.5 | 0 | 9795 |
| wpm-twohand-zero | npc_death | 93 | 347.8 | 0 | 9494 |
| wpm-shield-max | npc_death | 7.1 | 4510.3 | 2074 | 12845 |
| wpm-dual-max | npc_death | 7.75 | 4132 | 2074 | 12460 |
| wpm-twohand-max | npc_death | 11.1 | 2885 | 2074 | 11788 |
| wpm-shield-undead-max | npc_death | 5.15 | 6213.6 | 2074 | 12845 |
| pet-bare-zero | timeout | 180 | 91.4 | 0 | 6380 |
| pet-equipped-zero | boss_death | 154.6 | 210.7 | 0 | 8287 |
| pet-bare-max | boss_death | 178.95 | 182.5 | 2085 | 8615 |
| pet-equipped-max | boss_death | 111.8 | 289.9 | 2085 | 8026 |
| wpm-shield-heroic-off | npc_death | 8.05 | 3978 | 2074 | 12845 |
| wpm-shield-max-seed-2718 | npc_death | 6.15 | 5207 | 2074 | 12216 |
| pet-equipped-max-seed-2718 | boss_death | 82.7 | 390.6 | 2085 | 7666 |
| wpm-classic50-zero | timeout | 180 | 127.9 | 0 | 5235 |
| wpm-classic50-max | npc_death | 12.2 | 2626.7 | 2074 | 8738 |
| caster65-zero | timeout | 180 | 104.4 | 0 | 4141 |
| caster65-max | npc_death | 144.3 | 225.4 | 2163 | 7253 |
| pet-pop65-bare-max | boss_death | 92.55 | 349.5 | 2085 | 7499 |
| pet-pop65-equipped-max | boss_death | 58.5 | 550.5 | 2085 | 8590 |
| wpm-shield-max-legacy-spells | npc_death | 11 | 2911.2 | 2074 | 12675 |
| pet-equipped-max-legacy-spells | boss_death | 71.3 | 452.4 | 2085 | 7696 |
| caster65-max-legacy-spells | npc_death | 46.95 | 685 | 2163 | 6723 |

## Comparison with the completed pet/WPM candidate

These paired inputs include both item and formula changes. Percentage deltas are
diagnostic outcomes for these controllers and seeds, not statistical balance estimates.

| Case | Previous DPS | Combined DPS | Change |
|---|---:|---:|---:|
| wpm-shield-zero | 691.6 | 712.3 | +3% |
| wpm-dual-zero | 591.6 | 622.5 | +5.2% |
| wpm-twohand-zero | 411.7 | 347.8 | -15.5% |
| wpm-shield-max | 2911.2 | 4510.3 | +54.9% |
| wpm-dual-max | 2465.1 | 4132.0 | +67.6% |
| wpm-twohand-max | 2122.3 | 2885.0 | +35.9% |
| wpm-shield-undead-max | 4478.7 | 6213.6 | +38.7% |
| pet-bare-zero | 91.3 | 91.4 | +0.1% |
| pet-equipped-zero | 346.3 | 210.7 | -39.2% |
| pet-bare-max | 188.3 | 182.5 | -3.1% |
| pet-equipped-max | 452.4 | 289.9 | -35.9% |
| wpm-shield-heroic-off | 2637.5 | 3978.0 | +50.8% |
| wpm-shield-max-seed-2718 | 3881.6 | 5207.0 | +34.1% |
| pet-equipped-max-seed-2718 | 567.0 | 390.6 | -31.1% |
| wpm-classic50-zero | 126.6 | 127.9 | +1% |
| wpm-classic50-max | 1762.0 | 2626.7 | +49.1% |
| caster65-zero | 403.1 | 104.4 | -74.1% |
| caster65-max | 685.0 | 225.4 | -67.1% |
| pet-pop65-bare-max | 518.6 | 349.5 | -32.6% |
| pet-pop65-equipped-max | 1836.4 | 550.5 | -70% |

## Same-item spell-rule controls

| Case | Rules enabled DPS | Rules disabled DPS | Enabled final HP | Disabled final HP |
|---|---:|---:|---:|---:|
| caster65-max | 225.4 | 685.0 | 7253 | 6723 |
| pet-equipped-max | 289.9 | 452.4 | 8026 | 7696 |
| wpm-shield-max | 4510.3 | 2911.2 | 12845 | 12675 |

## Starter, dungeon and observed-item spell probes

Each spell has 200 samples. Direct damage means include resists; DoT means are
landed initial-duration ticks. Healing is an effect value before missing-HP limits.
The JSON retains landed-only means, ranges and effective heroic stats.

| Case | SD / HA | Heroic INT / WIS | Frost Bolt mean | Light Healing mean | Heat Blood tick mean |
|---|---:|---:|---:|---:|---:|
| parity-l10-starter-normal | 0 / 0 | 0 / 0 | 0.0 | 65.0 | 28.0 |
| parity-l10-starter-ascended | 39 / 39 | 0 / 0 | 0.0 | 90.0 | 47.0 |
| parity-l20-starter-normal | 0 / 0 | 0 / 0 | 0.0 | 65.0 | 38.0 |
| parity-l20-starter-ascended | 39 / 39 | 0 / 0 | 0.0 | 90.0 | 57.0 |
| parity-l20-dungeon-normal | 170 / 170 | 0 / 0 | 0.0 | 175.0 | 123.0 |
| parity-l30-starter-normal | 0 / 0 | 0 / 0 | 0.0 | 65.0 | 43.0 |
| parity-l30-starter-ascended | 39 / 39 | 0 / 0 | 0.0 | 90.0 | 62.0 |
| parity-l30-dungeon-normal | 170 / 170 | 0 / 0 | 0.0 | 175.0 | 128.0 |
| parity-l40-starter-normal | 0 / 0 | 0 / 0 | 2.305 | 65.0 | 43.0 |
| parity-l40-starter-ascended | 39 / 39 | 0 / 0 | 22.39 | 90.0 | 62.0 |
| parity-l40-dungeon-normal | 170 / 170 | 0 / 0 | 89.855 | 175.0 | 128.0 |
| parity-l50-starter-normal | 0 / 0 | 0 / 0 | 9.7 | 65.0 | 43.0 |
| parity-l50-starter-ascended | 39 / 39 | 0 / 0 | 42.07 | 90.0 | 62.0 |
| parity-l50-dungeon-normal | 170 / 170 | 0 / 0 | 150.8 | 175.0 | 128.0 |
| parity-l50-observed-ascended | 532 / 460 | 138 / 119 | 547.035 | 407.0 | 309.0 |
| parity-l50-observed-legacy-spells | 532 / 460 | 138 / 119 | 63.995 | 364.0 | 81.0 |
| parity-l65-observed-ascended | 692 / 600 | 171 / 152 | 817.635 | 524.0 | 395.525 |
| parity-l65-observed-legacy-spells | 692 / 600 | 171 / 152 | 108.165 | 455.0 | 98.525 |

## Verified mechanics

- 47 input/output hashes and diagnostic binary match recorded execution
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
- Eighteen spell probes contain 10800 samples; level50/65 rule controls retain identical gear and effective stats

## Limits

- Native diagnostic clock/packet adapters; no actual RoF2 render or user gameplay acceptance
- Captured Nagafen55 single-target encounter; no pack, raid or long-duration balance certification
- Class permutations are stat/shield-swap probes; combat uses Warrior-first WPM
- Seed1729 plus two seed2718 repeats do not establish statistical superiority
- Explicit gear and maximum trained skills; max stages spend2074 WPM/2085 pet/2163 caster AA points
- Damage sums depth-zero HP loss capped at zero terminal HP; includes replacement of NPC regeneration
- Healing ledger is HealDamage only, excludes regeneration/Mend; spell IDs may be65535 at native call sites
- Pet runes and healing proved through native effects/state; player ledger totals do not describe pet sustain
- Bare/equipped pet comparisons retain fixed Classic support gems, with separate PoP summon cases
- Eighteen caster probes sample direct values/resists and landed initial-duration DoT ticks; no full casting/buff lifecycle
- Historical WPM deltas include item and formula changes; same-item rule controls isolate the two new spell switches together
- Probe loadouts are explicit diagnostic equipment, not proof of legal-era acquisition or optimal builds
- Low-level Frost Bolt probes target level55 Nagafen and can fully resist; these do not establish level-appropriate leveling balance
- Fixed encounter spell controllers were not reoptimized for additive SD; lower-cost ranks and DoT rotations need owner comparison
- No production content, characters, runtime, signed-client or wiki changes
