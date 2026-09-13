# 0020: Retain 250 caps after matched native sensitivity tests

Date: 2026-09-13. Status: baseline decision; overall balance remains unfinished.

## Decision

Retain the current spell-damage and healing caps of 250 while investigating the
pet build's encounter-specific survival gap. Do not adopt 300 damage, 300 healing
or both as a global solution on the current evidence. Higher caps remain available
when a broader balance case supports them; 250 is not a permanent ceiling.

## Evidence

Run 54 matched fights for each alternative, holding source-constrained gear,
zero/launch-maximum/later-maximum purchases, preparation, NPC data and three seeds
fixed. All 162 reports pass native combat, equipment, AA and effective-cap checks.
Only the intended cap readouts change in the initial build state.

The launch pet build moves from 0/3 Nagafen wins at 250/250 to 1/3 with healing 300,
0/3 with damage 300 and 2/3 with both. Damage 300 also produces a 57.5-second Vox
kill in a deeper-AA caster sample, while pet kills still take roughly ten minutes.
All 18 melee-build reports are identical under damage 300 after removing the
expected static spell-damage readout difference. Healing alone does not consistently
resolve the observed gaps. Three seeds are samples, not estimated win probabilities.

## Consequences

The global damage lever disproportionately strengthens the caster controller and
does not address the launch pet build's Nagafen failure by itself. Raising both
caps improves some pet outcomes, but does not establish a broadly balanced endpoint.
Changing healing affects resource and threat decisions as well as per-cast output;
different event timing consumes the seeded RNG differently. Do not infer that an
individual worse sample means stronger healing universally harms the build.

Keep the same baseline for the next pet preparation/AA and encounter-mechanics
comparison. Complete the expansion AA offering and owned-rank lifecycle separately.
No live configuration change or promotion is justified by this checkpoint.
