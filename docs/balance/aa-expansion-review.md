# AA availability and expansion progression review

Date: 2026-09-12. Design work in response to the owner's request to consider
removing overpowered AAs and unlocking more with expansion releases. This is a
review direction, not an approved removal list or a deployed policy.

## Current evidence

`era.json` currently declares Classic, level 50, and `aa_open: true`.
`tools/apply-era.ps1` translates that into
`Expansion:UseCurrentExpansionAAOnly=false`. The existing all-purchasable
WAR/CLR/WIZ control spends 13,738 points. It is a stress ceiling; it should not
automatically define the intended Classic endgame.
With the verified preparation policy, its six sampled boss kills take 11.40–16.95
seconds. That motivates reviewing the ceiling, but identifying an exclusion still
requires matched tests of specific abilities/ranks and their interactions.

The frozen native catalog retains expansion metadata. WAR/CLR/WIZ has 26 rank
rows tagged expansion 0, 200 tagged 3, and many hundreds tagged later expansions.
Some early rows have unknown names. Counts describe catalog rows, not a vetted
playable pool. A strict switch to native expansion gating would also remove
basic AA families currently contributing to solo viability.

| Ability family | Native first expansion tag | Review direction |
| --- | ---: | --- |
| Natural Durability, Combat Stability, Combat Agility | 3 | Consider limited early ranks as deliberate Classic exceptions |
| Spell Casting Mastery, Mental Clarity, Healing Adept/Gift | 3 | Measure early sustain ranks alongside offense and pet builds |
| Celestial Regeneration | 3 | Resolve the level-50 target rejection before counting its benefit |
| Divine Arbitration | 4 | Group utility; do not treat its solo no-effect result as evidence of excessive power |
| Warlord's Tenacity, Frenzied Devastation | 7 | Test delayed access and rank caps before permanent exclusion |
| Improved Twincast | 17 | High-priority review of early availability and interaction with other burst bonuses |

Metadata comes from `native-aa-catalog.json`; expansion tags alone are not a
Nightcap release schedule. Later ranks within a family can have different tags.

## Proposed policy shape

Create a declarative, reviewed rank-level availability policy associated with
`era.json`. For each ability/rank, record its first Nightcap release, prerequisites,
maximum accessible rank in each release, and any exclusion reason. Preserve useful
solo preparation and resource-management choices while limiting combinations that
erase encounter mechanics. Expansion releases can add ranks as well as abilities.

Separate three decisions: retain early, defer to a later release, or exclude because
its interaction remains unsuitable. A strong AA is not automatically an exclusion;
its cost, cooldown, activation window, stacking and impact across builds matter.
An unknown display name is not proof that an AA is overpowered.

Use the calculator to compare each proposed era pool at 0/100/200/500 spent-point
budgets and its legal purchase closure. If a pool exhausts before a budget, report
the actual spend and unavailable next purchase explicitly. Do not fabricate more
ranks to reach 500 or silently use the unrestricted all-AA ceiling.

Before enforcing a policy, validate prerequisite closure and inspect existing
characters' purchases. Document how inaccessible owned ranks, refunds and client
display are handled. Test purchase and activation enforcement together. Keep the
global spell damage/healing caps and NPC HP unchanged while measuring an AA pool,
then tune the remaining gaps using matched gear and preparation.

## Next evidence required

Measure a curated Classic candidate pool for melee, caster/healer and pet/DoT builds;
identify the families responsible for extreme burst or sustain with matched
removal/rank-cap comparisons. Review later release unlocks against their encounter
and gear ceilings. Native metadata is a starting point, not the final balance rule.

No AA has been disabled, no purchase has been removed and no era rule has changed
as part of this review.

The first 54 native rank-pool/family-removal comparisons are now recorded in
`native-aa-pools.md`. A 114-point combat core preserves danger but has some very
long Vox fights; removing both selected burst families from the unrestricted
ceiling still leaves six easy-looking wins with at least 82.1% sampled HP. Broader
rank curation remains necessary. These candidates are not a release whitelist.
