# WPM melee completion

Status: implemented and automatically verified; paired with the undeployed pet candidate.
The134-test suite, native AA checks and26 native scenarios pass. See README.md
and COMPARISON.md for evidence and remaining client/gameplay acceptance.
The original `nightcap-wpm-source-audit.txt` is the scope baseline. No production
activation or gameplay acceptance is implied by this document.

## Contract and order

1. `zone/attack.cpp`, `mob.h`, `special_attacks.cpp`: resolve combat capabilities
   from held classes without changing identity. All six W/P/M permutations must
   agree on AC, mitigation, critical eligibility, double attacks, Monk damage
   tables, rear dodge and special-attack counts. Single-class and NPC controls
   preserve native behavior. Remove the duplicate initial automated Monk strike.
   Player innate/augment attempts become independent, like permanent pets.
2. Generated, guarded AA content plus `config/aa-policy.json`: Shield Specialist
   five ranks at20/40/60/80/100%; Way of Steel two ranks for six Monk specials,
   damage100/200 and Fists of Fury attempts at native proc modifiers30/60.
   Use a distinct Paladin Holy Shield family rather than repurposing Warrior914.
   Open Healing Light3, Blessing of Life3, Rage of Rallos1 (60s reuse), Flurry12,
   Rapid Strikes10 and Veteran's Wrath6. Resolve obsolete Combat Fury309 edges
   through earned active Combat Fury30, never duplicate crit bonuses or grant AAs.
   All permitted ranks remain purchasable at level1. Preserve earned ranks,
   costs, class eligibility and saved cooldown deadlines.
3. `tools/wpm_content.py` and paired client assets: add sympathetic healing to
   Hopebringer/Cloak, shield sustain and haste, Diaku combat augments and a new
   Bloodfrenzy power-source equivalent. Do not move an already-owned weapon to a
   different slot. Preserve ratios, existing sockets and pet content. Every new
   definition needs an earned acquisition route and guarded occupied-ID checks.
   PoP gear retains original progression gates; coordinate with staged65/PoP.
4. Heroic STR: implement an explicit, separately switchable player autoattack
   percentage curve, retaining native flat minimum damage and shield AC. Use the
   documented1%/point through100, then linearly declining marginal gain0.0055 per
   point down to1/3%. This precise Nightcap interpretation is calibration, not a
   claim to reproduce approximate THJ examples. Do not inherit this multiplier
   into pets or multiply spell, rune, Bash or Monk-special damage.
5. Rebuild paired native binaries and client data. Run real-method regressions,
   AA purchase/prerequisite/ownership cases, disposable-DB activation/recovery,
   and reproducible native encounters for WPM and pet/caster controls. Compare
   1H/shield, dual wield,2H, living/undead, level/AA/gear stages and all class
   orders; record DPS, sustain, rune absorption, proc/HHE activity and resource
   use. Tests must distinguish full native encounters from isolated arithmetic.
6. Review final code independently, update CHANGES/status, all-wiki impact and
   installed skill references/fingerprints. Publish exact gameplay QA and paired
   rollback requirements. Production promotion retains repository manual-QA gate.

## Deliberate decisions

The later THJ Monk prose explicitly restricts Way of Steel to kicks/strikes;
the older AA dump also contained weapon-skill bonuses. Use the prose contract,
covering Kick, Round Kick, Tiger Claw, Eagle Strike, Dragon Punch and Flying Kick.
Keep native Fists of Fury -338 Hundred Hands and400ms floor rather than claiming
the unverified50% player recollection. Holy Shield requires an equipped shield
for its proc and proc-chance benefits. Native runes refresh/replace; they do not
accumulate. Sympathetic focuses roll individually, then native code chooses one
successful focus at random; the VI/VII level bands are deliberately disjoint.
Zero-mana proc heals cannot trigger this healing focus recursively.

The largest risks are stacked damage/sustain, stale or duplicate AA effects,
proc recursion, shield-swap invalidation and data/cache/client disagreement.
The pet candidate's equipment persistence, owner inheritance and Rabid Bear
split/permanence are part of the regression boundary, not work to redo.
