# Regular combat zone augments — October 29 candidate

Status: implementation and focused native/database tests; **not deployed or
player-accepted**. The user requested all regular combat mobs in each zone,
including Grind/Raid, plus Hate B, at the existing 0.5% augment rate.

## Contract

The 48 currently enabled Classic Hunt zones retain their own augment families.
Every ordinary spawned combat NPC can roll that zone's augment, including named
NPCs and private Grind/Raid spawns. There is no augment minimum NPC level,
name/script whitelist, or Kithicor nighttime/undead restriction. A real spawn ID,
player combat class 1–16, nonmerchant role, targetable body and absence of
invulnerability/aggro/harm protection identify regular combat NPCs. Services,
merchants, invisible controllers, pets/mercenaries/swarm pets, temporary actors
without a native spawn, and restored corpses are excluded. Ownership is captured
before death scripts/charm cleanup. Living NPCs restored with their native spawn
remain eligible; restored corpses never reroll.

Both public zones and Grind/Raid use zone version 0; nonzero instance IDs are
allowed. Nonzero *versions* and non-Classic eras retain the existing exclusion.
The global Hunt enable/revision gate and per-zone enable gate still apply.

Each qualifying death draws exactly one uniform integer in [0,9999]; values
0–49 succeed. Quality remains Base/Polished/Exalted/Ascension 60/30/8/2. One death
cannot reroll through another call. Item power, required equip levels, sockets,
forge costs, legacy quality multipliers and merchant resale are unchanged.
Wearable Hunt rewards keep the exact original approved spawn/NPC list, minimum
NPC level, and night gates, and retain their separate 0.5% roll.

Hate B uses its already-installed **Blackspire Prism**, IDs940592–940595. Its
existing gear family remains nondroppable because its equipment source list is
empty. The scoped SQL changes only zone186's enabled flag from0 to1; it adds no
item definitions or equipment sources. Seven other access-check zones remain
disabled. Other curated expedition augment systems are unchanged.

Broader eligibility increases acquisition per total zone clear despite the
unchanged per-kill rate. Low-level mobs can award high-required-level augments;
equip requirements still gate their use. Owner balance QA remains required.

## Evidence and implementation

- `server-mods/code/zone/zone_hunt.cpp`: independently select augment/equipment
  eligibility; permit an enabled augment zone with zero equipment sources.
- `common/zone_hunt_policy.h`: ordinary combat and augment predicates; legacy
  equipment predicate retained.
- `tools/tests/test_zone_hunt_native.py`: compile the actual Load/Award functions,
  caps and death integration; fixtures exhaust 10,000 chance values and cover
  public/instance identities, named/private low-level spawns, each exclusion,
  quality boundaries, duplicate calls, disabled/failed loads and Hate B.
- `tools/zone_augment_combat.py`: canonical guarded enable/disable SQL generator.
- `tools/tests/test_zone_augment_migration.py`: real disposable MariaDB schemas,
  enable/rollback, replay, missing/drifted state/items/config/sources and exact
  preservation of all seeded unrelated content, inventory and forge receipts.

October29 read-only production audit found Hunt revision2026100901 enabled,
448 definitions,48 enabled zones/6056 source pairs, and all source pairs still
matching current spawn/NPC data. Hate B was disabled with zero sources. Runtime
logs showed successful Hunt loading for Permafrost, Sol B and original Hate.
This was configuration evidence, not proof of natural drops. Live zone hash at
that observation:9e1a8148976ad6eb5431d3afa3b7efd630e6c9009de0aadb45444b7d797171ad.

## Release and recovery

Normal branch policy applies: feature → dev → test; main/production requires
owner sign-off. Tests do not constitute a full production build or live QA.
Before authorized activation, reconcile the latest deployed native source, build
the changed zone against it, take a fresh backup and verify exact target preimages.
Stop the whole supervised game cleanly, run `enable-hateplaneb.sql`, install the
paired zone and restart through the supported supervisor. Never kill one worker.
No rules catalog, ItemData ABI, cache definition or client asset changes are
introduced; retain the matching current world/loader/cache/client. Quest/rule
reload alone cannot change this compiled death path.

Hate layout candidate `ac9d9629` in the separate hateplaneb checkout maps managed
186 Hunt config and sources to76. **Do not merge that Load mapping unchanged:**
augment configuration must use the actual zone186 and Blackspire family. Resolve
any deliberately retained original-Hate wearable source mapping separately.
This candidate does not activate the new layout, travel or client archives.

`disable-hateplaneb.sql` safely restores only186's flag after exact guards. It
retains every definition, earned item, corpse and receipt. Reverting the augment
eligibility code restores the old restrictive policy in the other zones; after
any unrelated native changes, make a compatible forward patch instead of
downgrading their binary. The global Hunt flag remains the emergency pause for
both families. Never restore player snapshots. If a guarded procedure fails,
inspect its preimage error and the retained procedure before cleanup/retry;
never force its guard to pass.

Wiki impact: all authored articles, generated zone/item pages, catalog values,
Features, home summaries, commands and release labels are reviewed in
`wiki-review.json`. Candidate notes are distinct from current live acquisition;
publication is pending. Exact acceptance steps: [QA.md](QA.md).
