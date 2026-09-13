# 0015: Separate gear-source assumptions from AA power

Date: 2026-09-13. Status: diagnostic comparison; no release tuning decision.

## Context

The dragon baseline combines legal AA-pool candidates with gear whose strongest
accessories come from a level-72 Classic spawn. Source presence does not establish
solo attainability. Removing all high-level sources would conflate that dependency
with a broad, unsupported content restriction.

## Decision

Remove only Behemoth 56182 as a source, retaining items with another captured
source. Re-optimize the same gear objective and augment assignment per role, then
hold AA allocation, controller, preparation and seeds fixed. Measure a separate
Monk 36%-haste cloak substitution because additive gear scores do not prove the
best combat loadout. Independently regenerate inputs and verify native equipment.

A failing low-HP pet case also requires optional native death-callback evidence.
Use the first callback to decide a terminal result and nonpositive callback HP to
prove it. Keep late same-pulse healing visible in the raw trace, and preserve strict
legacy verification when callback evidence is absent.

## Consequences

The study can attribute a power difference to this specific gear dependency.
It cannot certify other source encounters, all acquisition routes, optimal class
strategy, or a complete AA release offering. Those remain explicit work before
final tuning. The terminal adapter still omits real corpse/persistence transitions,
so in-game death behavior requires QA. No live content or binary changes follow
from this diagnostic decision.
