# SpellDmg / HealAmt Scaling QA Spike

Date: 2026-09-08
Spec: docs/superpowers/specs/2026-09-08-spelldmg-healamt-scaling-design.md

## Setup
- A caster test character able to cast one fixed direct-damage nuke and one fixed
  direct heal, plus one DoT and one HoT. Note each spell's base value.
- Have Polished / Exalted / Ascended gear available for that character's slots.

## Steps & expected results
1. **Baseline (no tier gear):** cast the nuke and the heal. Output should equal
   the vanilla base (SpellDmg/HealAmt = 0). `#showstats` shows SpellDmg 0.
2. **Partial Ascended set:** equip ~6 Ascended pieces (SpellDmg ~120). Nuke and
   heal should be ~2.2x base (1 + 120/100). Confirm `#showstats` SpellDmg ~120.
3. **Near-full Ascended set:** equip enough that summed SpellDmg exceeds 250.
   `#showstats` SpellDmg should read exactly **250** (cap clamps). Nuke/heal
   should be ~3.5x base and NOT increase past this even with more gear.
4. **DoT / HoT:** cast the DoT and HoT at the near-full set; total damage/healing
   over the full duration should scale by the same percent (split across ticks,
   not front-loaded).
5. **Scope guard:** on a pure-melee character (no casting), confirm melee auto-attack
   and combat-ability damage are unchanged by any of the above.
6. **NPC guard:** confirm an NPC's spell output is unchanged (no client cap path).

## Report
- Measured nuke/heal at each state vs the expected multiplier.
- The `#showstats` SpellDmg/HealAmt at partial vs near-full (cap clamp proof).
- Whether DoT/HoT scaled and stayed split over duration.
- Any melee/NPC output that changed (should be none).
- Whether the resulting solo kill speed feels right, or the cap needs a nudge.
