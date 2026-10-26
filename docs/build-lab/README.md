# Nightcap Build Lab — first release

The owner requested an interactive counterpart to the THJ spreadsheets for build
benefits, DPS and rotation testing. The first release is a browser-local diagnostic
workbench in the wiki, using the existing handbook shell. No gameplay changes,
database writes or server execution are part of this feature.

## Accepted scope

- Two independently editable, saved builds; three distinct classes; Classic 50.
- Effective SD/HA (750 caps), heroic INT/WIS, HP/mana, regen and resolved passive
  melee/pet damage inputs. These are assumptions, not inferred character stats.
- A small source-pinned spell library with original class eligibility; direct,
  ordinary DoT and direct-heal formulas. Full equipment/AA/pet derivation is outside
  this model. Catalog item A/B comparison reports raw stat deltas, not legal BiS.
- Editable resolved actions let advanced testers supply measured abilities with
  cast/recovery/reuse, resource cost, damage/ticks/healing and shared timer groups.
- Deterministic 100 ms scheduling, 6 s global ticks, mana reserve, healing priority,
  continuous resolved incoming/background damage, fixed-duration target dummy.
- A/B DPS, first-10-second burst, damage breakdown, effective healing, mana trace,
  survival and cooldown timeline; no damage or ticks beyond the simulation end.
- Exhaustive priority permutations of up to six selected damage actions, keeping
  healing priority fixed. Best found order under these inputs, not global optimality.
- Versioned local save/import/export and input validation. No account or telemetry.

## Authority and proof

Source starts at main c6c2100 plus the published interactive handbook b6fe8e2.
Formula authority: server-mods/code/zone/effects.cpp and
server-mods/code/common/nightcap_spell_scaling.h. The October18 native result
archive supplies landed Frost Bolt, Light Healing and Heat Blood controls at
SD/HA 0,39,170 and heroic scaling. The older content snapshot supplies only the
explicitly projected spell rows; docs/pok/hub-stock-audit.json supplies original
class levels instead of widened spell columns. Fixture dates remain visible.

The scheduler is a separate diagnostic model, not the native combat engine.
Resists are explicit expected landed fractions, not an NPC resistance formula;
continuous incoming damage is not boss AI. No fizzle, interrupt, movement, hate,
focus/crit/AA resolution, full buff stacking or pet AI is implied. Resolved actions
must already include those effects. No hypothetical AA purchase changes damage.

## Implementation and verification

1. Private projection builder and public fixtures; pure JS model and arithmetic,
   mana, tick, timer, death, horizon, optimizer and validation regression tests.
2. Wiki app generation, scoped CSS and browser controls; article/home/navigation
   integration, safe browser storage and A/B workflows.
3. Build/link/security checks, real responsive browser QA, source review,
   CHANGES/status/wiki-impact evidence and installed skill maintenance.

Deployment and native player acceptance are separate from model verification.
Publication uses the existing immutable wiki updater only after all checks pass.
