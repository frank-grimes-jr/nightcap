# Boss spell resolution evidence

Date: 2026-09-12. Offline tooling on feature/balance-calculator; no live tuning.

The revised snapshot fixes two coverage gaps that would materially weaken the
enemy model: Phinigel uses list 1346 with Wizard parent 2, and Vox inherits spells
above the initial 1,200-ID cutoff. References now come from the selected NPC rows,
immediate parents, item effect fields, and recursive recourses. The snapshot also
contains legal Human creation combinations and point allocations.

Snapshot: `classic-20260912-v2.json.gz`, SHA-256
`e4b06f462a32b5463a608efae7ddde4d303b2422c863aecedc3427da06c08dae`.
There are 1,373 spells, five lists, and 172 entries before level/content filtering.
The original snapshot remains unchanged for previously recorded controls.

## Findings

The source-filtered profiles contain two Nagafen spells, 18 Vox spells, and 12
Phinigel spells. `npc-spell-profiles.json` records IDs, provenance, entry overrides,
timing, and formula values. Examples for level-55 Vox before final focus/scaling:

| Spell | Formula heal | Mana | Cast | Entry recast |
|---|---:|---:|---:|---:|
| Complete Heal | 7,500 | 400 | 10 s | 10 s |
| Divine Light | 1,380 | 355 | 3.75 s | 6 s |
| Remedy | 483 | 167 | 1.75 s | 6 s |

Vox also inherits defensive buffs, Yaulp IV, and Annul Magic. Her priority-zero
breath and Dragon Roar are attempted before ordinary self-healing. Ordinary
self-heals use the integer HP percentage threshold, default 50. Detrimental AI
has both the overall attempt chance and category-specific gates. A full-mana NPC
may cast an otherwise unaffordable spell at zero cost, including zero-mana NPCs.

`npc_casting.py` implements this selection subset for a single target in range
and line of sight. Its caller must supply scan order, cooldowns, and statuses.
It does not establish actual equal-priority `std::sort` order or a complete AI
state machine. Ally healing, stacking conflicts, per-target readiness timers,
initial uptime, failed casts, prebuffs, and movement need explicit integration.
Unsupported engaged categories fail rather than silently disappearing.

The stored Sound of Force stun slot has base 8,000 and maximum 55. The extracted
formula returns 55; that maximum also participates in the stun level check.
Do not replace the result with an assumed eight-second stun. Trace the complete
application path and verify the observed duration before using it in balance QA.

## Verification and limits

`spell-resolution-oracle.json` records actual source and extracted-function hashes.
The native duration/effect oracle matches 12,224 cases. Ordinary resist outcomes
match all 201 equiprobable rolls for each of 1,500 inputs: 301,500 rolls, zero
mismatches. Formula IDs 202, 208, 210, and 211 remain explicitly skipped by the
scalar oracle; stacking metadata is retained separately in the content report.
The full Python suite passes 94 tests, including regression fixtures for omitted
boss dependencies, later-ID heals, entry recasts, and parent suppression.

The resist proof uses resolved modifiers and excludes fear CHA, focus/AA checks,
softcaps, physical/PvP paths, and root/charm breaks. Formula values do not include
final focus, crit, class, item, or NPC scaling. Buff tick lifetime and fear expiry
also require the actual application/tick path. Nothing here certifies a full BiS
character, full boss simulation, or a change to the 250 spell/healing caps.
