# Automatic title unlocks and matching suffixes

**Built and tested; live activation pending.** This follow-up removes the need
to open Titles or run `#titles` to finish earning any of the 77 achievements.

Login/zoning, a level change, committed personal Keeper clears (including High
Keep rescue), and successful final campaign task persistence schedule an automatic
check. Checks run at the next valid client processing boundary. Saved level and
skills fence mastery/level awards; an enclosing transaction defers the check.
Transient storage failures retry after 30 seconds without replaying kill counters.
Existing qualifying kills and capped-skill changes retain immediate awards.
Each newly inserted award sends the native new-title notification and a chat
message. Unique persisted awards suppress duplicate notices. As before, a lost
write acknowledgment can prevent a notice despite a committed award; this is
not an exactly-once chat-delivery guarantee.

Each of the 76 prefixes also has a matching `the …` suffix. **Flamebreaker** and
**the Flamebreaker** use one existing stable achievement ID and award, so current
owners gain the suffix without a second grind. **the Last Lantern** keeps its
existing suffix. There are 77 achievements, 76 prefix choices and 77 suffix
choices. Both forms fit the native 31-byte limit. No current worn title changes,
new power, reward, title IDs, schema migration, command or client download.

## Evidence and source authority

Five focused groups compile the actual adapter/policy and check notification,
paired fields, durable level, transaction rollback, retry/no-per-frame-SQL and
milestone hook placement. Real isolated MariaDB checks verify the combined
control/transaction query, commit/rollback and one award for two placements.
Ten rollout fault controls include the actual prior content-normalization
closure, clean stopped backup, preservation and recovery.

The first native candidate reproduced title-zone `f35b4e3d`. A newer rest release
became live before staging, so that candidate was never deployed. The final
build preserves the reproduced rest zone `d9ab889a`, matching world `eafe4507`,
rest rules, current caches and signed client 2026111301. It changes nine effective
source files and seven units, retaining the 144 link inputs and current command
archive. Exact prior recompilation evidence is retained for the unchanged seven
incumbent objects and unchanged nine source files. See `native.py`, `feature.patch`,
`shipping-baseline.json`, `shipping-candidate.json` and `source-delta.json`.

`release.py` restores the original stopped-backup function and actual full
content hashing from the prior title migration wrapper. The old title control
guard remains independent. It uses shared deployment/GM locks, supported admission
drain, clean whole-game stop, fresh stopped backup, exact native saved-state boot
model and one market rotation. Award/counter digests stay fixed while closed;
earning may resume after opening. Never use world RPC while the game is stopped,
replay terminal actions, kill one production worker or restore a player snapshot.

Pre-opening recovery takes a fresh backup and reopens the current rest-capable
predecessor. It uses real occupancy RPC only while running and clean stopped
state otherwise. After opening, preserve all profile/award/counter state and
repair forward. The current schema and stable IDs are compatible with both builds.

## Exact native player QA — OPEN

1. Use an ordinary account, GM off. Log in with an existing recorded eligible
   goal and no award. Expect the award, chat and new-title alert without commands
   or opening a window. Rezone/relog: no repeated earned notice.
2. Reach level 50 from 49. Expect Seasoned Adventurer automatically after the
   save. Raise a tracked skill to its legal level-50 raw cap: expect its mastery
   award. Keep all seven crafts capped to verify Master Artisan.
3. Finish a personal Keeper Raid clear. Expect its completion title immediately
   after committed completion. A partial/missed-boss participant must not receive
   it. Finish High Keep's Osargen escort separately: High Keep Liberator must
   unlock at rescue completion without needing another NPC kill.
4. Finish The Last Lantern task9515. Expect its suffix automatically after native
   completion persistence. Full Classic conquest still needs all21 personal Raid
   clears; no other dungeon can substitute.
5. Kill home-zone Nagafen for Flamebreaker, then Vox for Dragonslayer. Confirm
   ordinary qualifying kills retain their automatic notifications.
6. Open Titles to choose an earned prefix or matching suffix. Confirm both
   choices use the same unlock, persist after zone/camp/relog, and remain after
   class release. Locked titles remain unavailable and earning does not replace
   the worn prefix/suffix. Check the native nameplate and new-title indicator.

Destructive storage/rollback/failure simulations belong only in the isolated
fixtures. Native UI/notification acceptance is not established by build hashes.

## Wiki impact

The current 631-file public title source reproduces exactly before ten scoped
outputs change; 621 retain their bytes. Titles, Commands, Features and owning
combat/dungeon/skill/craft/story guides explain automatic awards and paired
placements. Home needs no release announcement; generated item/zone/catalog
values, acquisitions, loot finder and Build Lab remain unchanged. Publication
waits for actual live activation; the global historical review ledger is not
advanced. `wiki-candidate.json` records exact content/package checks.
