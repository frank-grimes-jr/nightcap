# Unique Classic dungeon rewards — October 22 candidate

The owner requested unique rewards appropriate to dungeon difficulty, all MAGIC,
with especially distinctive, lore-driven planar rewards. This extends the accepted
21-zone expansion in `../classic-expansion-20261022/`; it supersedes that candidate's
temporary shared saber/signet/satchel fallback and zone-only binary pairing.
No gameplay deployment, main promotion, wiki publication or owner acceptance is implied.

## Design and acceptance

- Keep the original 330 IDs, stats, names, rolls, stored drops and earned receipts.
  Exactly 220 existing definitions change only MAGIC from 0 to 1.
- Append 42 authored designs / 84 Polished and Ascended variants at 960330–960413.
  All 21 dungeon finals now select their own three exclusive designs; completion
  rewards, Grind and raid roll probabilities remain unchanged.
- Cap new numeric power at the existing slot/band/quality template. Move resistance
  budget and choose relevant stat pairs without increasing their totals. Existing
  bands20/30/40/50 represent the dungeon progression; planes remain band50 and add
  a level46 requirement. This is a conservative baseline, not balance acceptance.
- Make planes distinct through nine authored relics and three equipped utility
  clicks. Existing See Invisible80, Invisibility42 and Levitate261 are captured and
  guarded. All have a 10-second cast, level46 requirement, unlimited charges and
  shared quality-family cooldowns of300/600/900 seconds in groups91/92/93.
  Cast/reuse values are base values; native focus reductions, targeting, reagent,
  invisibility-break and no-levitation rules remain.
  Sky itself disallows levitation; the Astrolabe is a reward for use elsewhere and
  consumes one Bat Wing. Keys and island progression remain required.
- Lore-driven means authored narrative and thematic mechanics. It does not set
  the LORE uniqueness flag or remove Nightcap's free-trade policy.

The complete reviewable catalog is [REWARDS.md](REWARDS.md). Lore sources are linked
there; individual relic stories are explicitly original Nightcap fiction.

## Implementation and evidence

`tools/classic_dungeon_rewards.py` owns authored design identities; `dungeon_catalog.py`
appends them after the frozen330-item retune. `legacy_items()` and `existing_items()`
retain historical migration inputs. `common/dungeon_policy.h` extends the reserved
range and final-boss mapping. `dungeon_contract.py` additionally checks inspect lore
and all new click fields in the actual ItemData cache.

`tools/classic_reward_migration.py` consumes the complete production public preimages
in `preimages.json`. The SQL requires disabled acquisition, expansion-installed tasks,
correct storage, all330 complete item preimages, unchanged utility spells, unused
new identities and unused cooldown groups. It checks ordinary item references,
dungeon entitlements/loot, serialized checkpoints/corpses, native timers and persisted
item-recast timestamps. It changes only220 MAGIC values and inserts84 definitions
in one transaction. It does not write inventory, existing rewards or checkpoints.

Build, isolated SQL and actual cache verification passed. All414 native rows and
888 deliberate MAGIC/lore/click mutations were checked. The77-test broader run
passed74 with two optional DB skips and one reproduced pre-existing generator
drift (preexisting-test-drift.json). Wiki21 Python/13 Node checks and458 pages pass;
nine POSIX-only publisher checks are skipped on Windows.

Verification evidence is recorded in `verification.json`, `rehearsal.json`,
`build-manifest.json`, `cache-verification.json` and `review.md` with their measured scope.
The isolated rehearsal uses synthetic earned state and tests orphan references,
preimage/spell drift, mid-transaction failure and repeat installation rejection.
Production captures are read-only; absence in a dated capture never replaces a
deployment-time guard.

## Pairing and rollout boundary

1. Review current source/release drift and obtain the applicable promotion and
   deployment authorization. Take a fresh backup and capture current binaries,
   item/cache hashes, feature state and exact public preimages. Do not reuse a
   stale local database/cache as production authority.
2. Disable acquisition and quiesce game writers during full-runtime maintenance;
   production's supervisor restarts the runtime when any native child exits.
3. Install the additive Classic dungeon migration first, then
   `server-mods/sql/20261022_classic_dungeon_rewards.sql`. Recheck every current
   schema/content contract. Guard failure stops activation; investigate drift.
4. Pair matching world, zone and shared_memory with the expanded dungeon policy,
   the 11 plane quest scripts and Lua module from the expansion. Regenerate target
   item caches with matching shared_memory. ItemData/rule ABI is unchanged, but
   `common/shareddb.cpp` consumes the expanded reward range for zero resale.
   Existing spell IDs require no new client assets; preserve the current signed
   client release and its paired spell files. Do not downgrade current releases.
5. Verify all414 cached rows, MAGIC, full click fields, zero resale and runtime
   checks before re-enabling. Run [QA.md](QA.md); record deployment separately from
   player and balance acceptance. Local wiki edits remain unpublished.

Rollback before player access may restore the exact captured binaries/cache and
revert only this migration under reviewed preimage checks. After access, disable
new acquisition and retain a compatible21-zone/414-item runtime and all definitions,
earned items, pending drops, receipts and cooldowns. Never roll back player snapshots
or remove definitions already held by players. No destructive rollback is automated.

## Work plan

Authored catalog and deterministic budget/mapping tests → full-preimage migration
and actual MariaDB fault rehearsal → matching native build and actual cache inspection
→ independent review → candidate wiki/knowledge maintenance. The principal risk is
mixed old binaries/cache/catalog; fail-closed guards and paired artifacts address it.
Final in-game difficulty, effects, item appearance and progression remain owner QA.

Historical October16 installation/packaging/verification helpers and the pre-reward
expansion rehearsal are frozen evidence, not current release commands. Use the
combined `rehearse_classic_rewards.py` and `rehearse_classic_reward_cache.py`; the
old330-row item-reference audit describes its original range only.
