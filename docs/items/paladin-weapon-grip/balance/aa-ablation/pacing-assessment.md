# Epic reward pacing assessment — October 27, 2026

Recommendation, not an implemented reward-policy change: award Ascended Fiery
Defender at completion of its original epic quest, remove the additional material/
currency gate for that reward, and judge it against its acquisition effort and
credible later replacements. Do not use Ghoulbane as the ceiling for Ascended
SoulFire or the epic. If this policy is adopted for all class epics, audit their
individual clicks/procs and existing-owner transition separately.

The current checked-in Epic Forgemaster requires the completed class epic,
8 Essence of Ascension and100,000 platinum. That is an additional material/currency
gate after the epic quest. Under the owner's intended fast progression, delaying
the useful version can consume its intended period of relevance. This is a design
inference from the gate and intended pace; no player acquisition-duration telemetry
was collected. No quest, forge, inventory or live definition has been changed.

## Concrete progression checks

Selected public item definitions and static drop associations were captured
read-only from production on2026-10-27 at23:53:56UTC. Full reference is
`public-replacement-reference.json`. Static spawn associations are incomplete for
scripted spawns and quest rewards; existence is not proof of immediate access.

| Weapon | Current definition | Proposed test definition |
|---|---:|---:|
| Ascended SoulFire |46/45 2HS|26/30 1HS or46/45 2HS|
| Ascended Fiery Avenger |66/44 2HS|30/30 1HS or66/44 2HS|
| Ascended Fiery Defender |47/40 2HS|36/30 1HS or72/40 2HS|

Direct delivery of the existing Ascended Defender alone does not fix the current
raw-ratio regression from Ascended Avenger:47/40 is21.7% below66/44. Existing armor,
HP, mana and proc differences still matter, but this is a meaningful progression
gap rather than a small comparator-ranking concern. The proposed72/40 increases
the raw ratio20% over66/44 and also changes support/proc fields as documented in
the original assessment. Those values remain candidates, not release-approved.

Later definitions leave replacement opportunities without requiring the epic to
be weak at acquisition:

| Later item | Definition | Same-grip ratio above proposed Ascended Defender |
|---|---:|---:|
| Ascended Sword of Ssraeshza |104/42 2HS, required level60|37.6%|
| Ascended Great Sword of Pestilence |80/42 2HS, recommended level60|5.8%|
| Ascended Scimitar of Shissar Slaying |30/19 1HS, recommended level60|31.6%|

Pestilence and the Scimitar have captured Vex Thal static loot associations. The
Sword of Ssraeshza's item definition was captured; this bounded static-spawn query
did not establish its acquisition route. Compare recommended-level items at full
effect. Ratios above are not native DPS predictions and omit delay bonuses,
procs, damage caps, skill, AAs, support stats and shield effects.

Normal later-item definitions do not automatically replace the proposed Ascended
epic by ratio. Captured default ordinary loot tier rules are20% Polished,5% Exalted
and1% Ascended per eligible item; not every Luclin drop is Ascended. Deterministic
quest rewards, trading, tier forging and the actual time spent farming determine
replacement speed. Do not claim that the epic will necessarily be obsolete soon
after entering Luclin. Useful clicks/procs or defense can extend an item's life.

## What warrants tuning

Prioritize a satisfying reward on acquisition, a clear quest-chain improvement,
and sufficiently attractive later upgrades. A small advantage over an earlier
weapon does not warrant repeated min/maxing. Large reusable damage/proc/AA effects
and differences that erase later upgrades do warrant tests. The ongoing Wu/Way of
Steel removal experiment addresses this larger scaling concern; it is not a reason
to make epic weapons deliberately weak.

Broad bands are better supported than an exact target lifespan today. Measure
epic completion to replacement before claiming a number of hours or expansions
of use. This assessment does not authorize removing the existing forge, converting
owned epics, refunding materials, modifying every class epic or publishing new
player guidance. The earlier separate-upgrade implementation remains unchanged.
