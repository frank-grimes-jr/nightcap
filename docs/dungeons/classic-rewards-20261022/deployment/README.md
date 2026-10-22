# Combined dungeon release — deployment in progress

The owner explicitly requested live deployment of the21-dungeon options and
unique rewards for in-game testing. This authorizes main promotion for this
release; gameplay and balance acceptance remain open.

Source61230ac integrates main42603ee and its quest-tier matcher/native robe skinning.
The initial preflight rejected the superseded runtime before evidence creation or
gameplay changes. combine_build.py reproduces the new6da991b6 live zone exactly,
then combines its two quest objects with the verified dungeon objects/archives.
Candidate8c9b97d5 preserves the new matcher; six combined regressions pass. The
current game2026102204 client remains unchanged. Exact runtime pairing is in
package-manifest.json. Only the two October22 migrations and eleven plane
quests plus the new run-identity Lua module are installed. Existing Keeper
appearance/placement code, newer class armor and waypoint changes are retained.

rollout.py holds admissions and the whole supervised runtime, takes a stopped
backup, disables acquisition, applies expansion then rewards with separate
receipts, validates39schema/497content checks, regenerates and inspects the whole
cache, and restarts all12zoneworkers. The exact84newIDs and220MAGIC-only cache
changes are checked; all other cached items and spells remain exact. All player,
custom, dungeon and ownership state stays intact, apart from any precisely
authenticated native seven-day non-corpse saved-state expiry. Unexpected drift
holds access; it is never silently ignored.

Recovery after new runs/items exist must use compatible21-zone/414-item code,
with acquisition disabled if necessary. Do not down-migrate or restore an old
player database. The retained previous image and server-side compressed staging
files remain recoverable for diagnosis.

Fresh merged checks: ten focused dungeon checks pass (the Lua case needs Docker
permission);21wiki Python checks pass with9POSIX skips,13Node scenarios pass;
two release packaging/preservation tests pass. Earlier74/77suite outcome retains
two historical optional DB skips and one proven pre-existing unrelated SQL
generator drift. Independent operator review required executable modes, baseline
pairing, new NPC quest-shadow guards and capped rehearsal memory; all addressed.

A read-only probe found roughly1GBfree. Eighteen exact unmounted retired test
cache/staging files were losslessly compressed in place after decompressed SHA256
verification, recovering space to3.26GB. No backup/player/live file was removed.
Six additional historical dungeon/parity binaries were compressed the same way
to meet the reserve; a second receipt ends in-v2.json. An attempted local archive
export was denied by automatic approval review; no
export occurred. Archives remain on the server with
/opt/nightcap/releases/dungeon-space-20261022.json.

The fresh production-content rehearsal, activation and public wiki receipts will
be recorded here after they actually succeed. Candidate records retain their
original dates and scope. Exact owner QA: ../QA.md and ../../classic-expansion-20261022/QA.md.
