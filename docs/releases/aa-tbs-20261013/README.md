# Buried Sea AA candidate — October 13, 2026

> Superseded after owner QA: this historical candidate’s level gates were rejected. See [level-1 correction](../aa-tbs-level1-20261013/README.md).

The owner-authorized policy is **live on OVH for QA**, from the feature/dev/test
candidate. It started at 11:09:24 UTC October 13. Native build, independent review
and deployment checks passed. Gameplay acceptance and promotion to main remain
pending. Reconnect with the current launcher client to test.

## Behavior

The AA window, purchases, quest/GM grants, active hotkeys and passive usable ranks
share an independent AA policy. Ordinary ranks stop at The Buried Sea (13), with
the six named exceptions below. The world remains Classic, level 50. The full
catalog, native class masks, AA prices, XP rates and stored purchases remain intact.

| Group | Trial unlocks / maximum |
|---|---|
| Natural Durability, Combat Stability/Agility, Mental Clarity, Innate Regeneration | Ranks 1/2/3 at levels 1/20/30 |
| Healing Adept/Gift, spell mastery/fury, Natural Healing, Combat Fury | Ranks 1/2/3 at 10/20/30 |
| Most other ordinary TBS families | Ranks 1/2/3 at 30/40/50, subject to prerequisites |
| Innate Run Speed | Ranks 1/2/3 at 1/10/20 |
| Pet Discipline / Advanced Pet Discipline | Rank 1 at 10 / ranks 1/2 at 20/30 |
| Animation Empathy | Ranks 1/2/3 at 1/10/20 |
| Eyes Wide Open 938 | All eight free ranks at level 1 |
| Diminutive Companion 543 | Rank 1 at 10 |
| Enchanter Pet Discipline 3202 | Rank 1 at 20, requiring Animation Empathy 3 |
| Companion's Durability 3512 / Agility 3818 | Ranks 1/2/3 at 30/40/50 |
| Sturdy Companion 1403 | Rank 1 at 50; raw pet AC, not percent mitigation |
| Slay Undead | Rank 1 at 50 |
| Ancient Attunement / Expeditious Dispatch | Existing one-rank travel access at 1 |

Headshot, Finishing Blow, Anatomy, large burns/crit multipliers, Flurry/Rapid Strikes,
Mortal Coil, Tenacity, resource refills and charged glyphs are deferred. Later
twincast, burst, proc and sustain families receive no exceptions. The exact
authority is [policy JSON](../../../config/aa-policy.json); dependencies can raise
an unlock level or remove an unreachable rank, never extend the pool.

All grant-only veteran families become dormant too, including Lesson, recovery,
combat boosts and merchant/banker summons. The audit captured five ownership
rows for each of fourteen veteran families. No grant-only unknown/system powers
are implicitly exempted. This does not delete those records or refund points.

Higher purchased ranks are **dormant**: the server retains their earned counts,
charges and spent-point accounting, uses only the eligible prefix, and prevents
paying again for an already owned rank. Level gains/losses immediately reproject
usable ranks and refresh the window. Login, class refresh and AA reload use the
same eligibility checks. Missing prerequisite definitions reject purchases.

Existing temporary spell buffs expire normally. Pet avoidance/AC consult current
owner bonuses; pet HP is fixed when summoned. Resummon to test a changed Durability
rank. The deployment restart restores pets with current caps and clamps saved HP.
No forced summon, heal, buff reset or pet deletion occurs on leveling. An inherited
Mastery of the Past/class-release prerequisite behavior is outside this change.

## Size and evidence

There are 390 allowed families / 941 ranks globally at level 50, before native
class/race/status restrictions. The sampled triples start with **nine families**
at level 1 and approximately 15–16 at levels 10–20. For example WAR/CLR/WIZ reaches
152 families / 389 ranks / 1,692 points at 50; MAG/NEC/SHM reaches 143 / 348 / 1,506.
These are catalog ceilings, not measured combat strength or required spending.
[All 16 classes and six unions by level](coverage.json) distinguish visible
families from prerequisite-closed purchase pools.

Verification: five policy tests, 5,646 native rank/level cases plus class masks,
identity mismatch, actual purchase/save/ownership/projection methods and complete
clear/table/points/stats refresh checks. A regression reproduced the missing-
prerequisite purchase on the first candidate, then passed after the fix. Three
read-only preflight tests and ten rollout/recovery cases pass. The first native
harness build hit signedness warnings in test doubles; the final harness compiles
under its documented flags. Full zone compilation/link and runtime library checks
pass. These checks do not simulate a full player session or prove encounter balance.

The final v3 build uses retained production source from the October 13 full
skill-progression correction. That release arrived while the initial AA candidate
was building; the older AA binary was never activated. Main b203fba was integrated
and all 126 corrected zone object hashes were verified. Only aa.cpp and exp.cpp
are recompiled; client.h adds a nonvirtual method and no layout changes. Other
link inputs match recorded hashes, and the final manifest records every linked
object. The two changed units compile without a stale precompiled header. Trainer
purchases, skill progression, offhand fixes and signed client 2026101301 are retained.

Native zone SHA256: `0737959ab3ebce1b31ad687cdb41e7d69bc7c3a30620e884e543051859bde143`.
See [build](build-manifest.json), [native tests](native-tests.json),
[original audit](../../audits/aa-tbs-20261013/README.md), and
[decision](../../adr/0046-aa-tbs-policy.md).

## Exact in-game QA

1. Reconnect using the current signed client (2026101301); no new client patch is
   required. On an existing low-level character, open every AA tab and confirm the
   compact list, owned usable prefix and unchanged unspent/spent totals. Try old
   Headshot/burn/veteran hotkeys: dormant abilities must not activate or consume
   points/charges. Camp and log back in; then zone East Commonlands to North Ro.
2. On a **disposable** WAR/CLR/WIZ or PAL/WAR/MNK test character, use GM `#level`
   for 1 → 10 → 20 → 30 → 40 → 50 → 10. At 1 buy Natural Durability rank 1;
   rank 2 must be absent. At 20 it unlocks, at 30 rank 3 unlocks, and rank 4
   stays absent at 50. Returning to 10 uses rank 1 and keeps the higher earned
   ranks; returning to 30 restores rank 3 without a second charge. Reopen the
   window without zoning at each step and inspect HP/defense changes.
3. Verify native class restrictions using a single-class Warrior and an Enchanter
   union. A Warrior must not buy Enchanter Pet Discipline. On the Enchanter union,
   buy Animation Empathy 1/2/3 at 1/10/20, then Pet Discipline at 20; test follow,
   back off and hold on every owned pet slot. On MAG/NEC/SHM, test shrink at 10,
   Durability/Agility at 30/40/50 and Sturdy at 50. Resummon for HP comparisons.
4. On disposable controls, compare no AAs, 25/100/200/500 points and the full legal
   pool at 10/20/30/40/50. If the pool exhausts early, record actual spend. Keep
   obtainable gear, buffs and pets fixed. Test East Commonlands orc pulls, then
   appropriate Crushbone, Unrest and Lower Guk camps, including two/three adds.
   At 50 test Nagafen (npc_types 32040, soldungb) and Vox (73057, permafrost),
   confirming the current target before starting. Record kill time, low HP,
   mana use, cooldowns, recovery, pet deaths, deaths/timeouts and repeated kills.
5. Confirm meaningful preparation and gear upgrades still matter, fights require
   decisions, sustain does not erase downtime, and the early list is readable.
   Owner acceptance covers the enjoyment and combined-class balance judgement.

## Deploy and recover

Activated image: `sha256:5555000c74665f13eb3c99facc657b2e38c3983eff745a9ffe65a5439440f025`.
All twelve zone processes match, with zero runtime restarts and zero detected
native/quest/database errors. Closed-state fingerprints preserved 47 player and
11 custom tables. Rules, complete AA catalog, quests/plugins, public client files
and DB/web/tunnel services remained unchanged. The prior image is the October 13
skill correction, `sha256:67b3114b9142ba19a0ead71948a053eb482818638564c408b1ebab1503f0336b`.

Fresh preflight validated **239 ownership rows / 1,193 earned ranks**: 45 rows
fully usable, 28 partially usable and 166 dormant under the new policy. All rows
were retained. Saved charges were zero in this capture; synthetic native checks
also verified nonzero charge retention. Backup gzip integrity passed (63.4 MB
compressed). See [activation](server-receipt.json), [health](final-health.json),
[ownership preflight](production-preflight.json),
[backup/image receipt](rollout-preflight.json) and
[stopped fingerprints](stopped-fingerprints.json).

`deployment/rollout.py` uses the established production runtime helper under
deployment/GM locks. Preflight verifies current native hashes, exact AA catalog,
anonymous ownership validity, supporting services and a fresh gzip-tested SQL
backup. Activation closes access, gracefully stops the whole game, captures player
and custom table fingerprints, overlays only zone, and checks all twelve running
zones plus data/rules/content/catalog before reopening. No SQL is restored.
Recovery tests cover failed health, data/custom/catalog drift, service drift,
lost gateway acknowledgment and GM maintenance conflicts.

If activation fails before access, the operator restores the prior immutable
image and retains all data. Persistent data/catalog drift holds access closed.
For a later QA rollback, take a fresh backup and stopped-state fingerprints,
reselect the prior image from preflight.json, and perform the same verification
against **current** player data before reopening. Never replay old SQL or old
player-state snapshots after gameplay. If another native release has intervened,
reconcile its changes before reverting this policy.

Future policy changes edit `era.json`/`config/aa-policy.json`, capture/review the
catalog, regenerate the header and rebuild/deploy zone. `apply-era.ps1 -Check`
only checks source generation, not running binary identity. A generic AA/rules
reload cannot replace compiled policy. The protected RoF2 reference is unchanged.

Retained build evidence fingerprints all 126 zone objects and 15 recorded library
inputs. Its inherited suffix filter excludes directly named versioned libperl;
the unchanged image supplies that runtime dependency and dependency checks passed.
This is not a claim that every system library file was separately fingerprinted.
