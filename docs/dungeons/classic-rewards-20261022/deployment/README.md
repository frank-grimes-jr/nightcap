# Classic dungeon options and rewards — live testing

All 21 Classic combat dungeons, including Fear, Hate and Sky, now offer Raid,
Grind, Enter, Join, Status, Claim Rewards and Reset. The 14 additions have 42
unique designs in Polished and Ascended versions; all 414 dungeon reward
definitions are MAGIC. Existing reward identities and other stats remain.
Planar relics include level-46 equipped utility clicks with shared family reuse.
Main PR293/3af85bb and the paired live deployment are verified. Owner gameplay
and balance acceptance remain open.

The owner explicitly authorized this main promotion and live deployment for
in-game testing. The current combined zone8c9b97d5 reproduces the previous
6da991b6 baseline and retains its quest-tier matcher. World49f87aaf and
shared_memory6b314bf0 are paired with the regenerated cache, eleven plane scripts
and the run-identity Lua module. Current signed game2026102204 is unchanged.
Exact hashes are in package-manifest.json and combined-build-manifest.json.

Fresh production-content preflight and activation both pass39schema/497content
checks and414 actual cache definitions/888 drift-rejection cases. Of309760 prior
item records,309540 remain byte-identical and220 change only MAGIC0→1; exactly84
new IDs appear. Spell cache and unrelated content/scripts/client remain exact.
The live receipt records a fresh stopped full backup, preserved player/custom
state, native expiry counts, market rotation and all12 healthy zone workers.
All91 tracked state tables remained exact; native expiry removed zero rows.
Runtime started18:58UTC and access reopened19:01UTC on October22.
Access is open; no player database was restored. See preflight-verification.json
and live-verification.json. Gameplay/balance acceptance is separate from these
automated checks. Exact owner tests: ../QA.md and
../../classic-expansion-20261022/QA.md; every new item is in ../REWARDS.md.

The first isolated loader exceeded1536MiB; the corrected rehearsal uses a3GiB
cap with at least4GiB available host memory. Subsequent isolated attempts exposed
CREATE TABLE LIKE omitting foreign keys and an incomplete list of copied content
dependencies. Actual SHOW CREATE DDL and every runtime-contract dependency now
form the clone. All failed attempts cleaned their temporary DB/user/config/cache
and preserved live services/content. Evidence remains in stage/attempts. No
contract checks were relaxed. Three release regression tests pass; independent
review checked schema isolation, memory bounds, cache preservation and evidence
freshness. Earlier source tests retain their recorded74/77 result: two historical
optional DB skips and one proven pre-existing unrelated SQL-generator drift.

Disk reserve was recovered by losslessly compressing36 exact unmounted historical
staging/test files in place, each verified by decompressed SHA256. Adjacent
.dungeon-space-20261022.gz copies and three dungeon-space-20261022 receipts remain
on the host. No active file, backup or player data was removed. Automatic approval
review rejected an unnecessary local export of those internal artifacts; no
export occurred, and in-place retention completed the space recovery.

Wiki20261022-classic-dungeons-v1 follows the latest native-robe publication.
Seven guides and search now show Live testing, with14 Keeper locations and95
additional boss objectives. All465 public hashes/security headers and five
private-route denials verify;16 Linux updater tests and actual pointer rollback
pass. Locally21 wiki checks pass with9 POSIX-only skips, plus13 Node scenarios;
the live page and added Keeper table render clearly and the contents link works.
Seven guides, directory and search are the exact nine changed public files.
Current robe2204, quest tiers, class armor and waypoints remain. The48-zone,
384-item Hunt catalog and commands are unchanged. See wiki-review.json,
wiki-publication.json and wiki-public-verification.json.

Recovery must retain compatible21-zone/414-item code, definitions and earned
state; disable acquisition and forward-repair if necessary. Never rerun the old
October16 bootstrap, down-migrate newly used IDs, or restore an old player DB.
Production supervises all native children: never kill an individual zone.
Retained deployment tools are one-attempt operators, not blind retry commands.
