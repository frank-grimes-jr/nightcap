# Plane of Hate paired release — October29, 2026

Main PR362 (`8b23d739`) and the owner-approved server, signed client and wiki
release are deployed. Admissions are open. The independent final live verification
passed at 14:46:21 UTC; owner in-game rendering, pathing, encounter and complete-run
acceptance remain open. Fully exit EverQuest and press Play in the launcher before
testing the new layout. Authorization is retained in [AUTHORIZATION.md](AUTHORIZATION.md).

New Raid/Grind runs from the Commonlands Keeper use hateplaneb186 with Nightcap's
existing NPCs, combat stats, loot, epic items, XP, Hunt families and completion
rewards. Existing unexpired 76 runs remain in their original layout. No player,
inventory, earned receipt or corpse migration occurs. Both layouts retain dungeon
index19 and tasks9738/9739. Public spell destinations stay unchanged. The
[feature runbook](../README.md) owns behavior, coordinates and exact owner QA.

## Verified deployment

- [Final independent live verification](final-verification.json):12 zone workers,
  51 schema and650 content checks, eight paired runtime files, unchanged post-open
  service identities and preserved quest/content/cache state.
- [Open receipt](open-receipt.json):102 saved-state tables, authenticated normal
  market rotation, zero native/quest/database errors, zero game restarts after
  activation, gateway open and no database snapshot restoration.
- New game image:
  `sha256:0dec2bfc8b2e83a30301c2fc203c5688d44a2b39cf354b5e0e0b2ba8ed38f9dd`.
  Its verified start was `2026-10-29T14:34:01.172258115Z`.
- Signed client2026102901: seven terrain/model assets added,141 existing assets
  retained. [Publication](client/published.json) and
  [public verification](client/public-verification.json) authenticate all 148 files,
  the production signature and retained history. The inherited proxy/catalog,
  launcher and unrelated assets remain unchanged.
- Wiki20261029-hate-layout-v1: six guides plus search changed,492 files preserved.
  [Publication](wiki/wiki-publication.json) and
  [public verification](wiki/wiki-public-verification.json) confirm499HTTPS hashes,
  security headers and five private-source404routes. Configuration, private
  downloads and all five service identities/start times remained unchanged.

The additive SQL installed176 private spawn points,47 grids and255 waypoints. The
native contract authenticates the private population and original175 spawn policies,
including randomized respawn variance. Original public spawn/NPC/loot/task/zone
tables and owned-table rows outside the reserved scope were preserved. Two local
Hate quest replacements preserve their original backups. Content and cache
pairing, stopped-state checks and the supported whole-runtime restart precede
admission reopening; individual production zone workers were not killed.

## Disk guard and retained recovery evidence

The first preflight stopped at its final disk reserve guard before changing
service state, gameplay content or publication. Its original evidence remains.
One pinned, unmounted historical Hate Keeper staging executable was compressed
losslessly with a round-trip SHA256 check and durable restoration receipt;
production images, volumes, backups and player data were not removed.
[disk-preservation.json](disk-preservation.json) records its exact original path,
archive, hashes, owner/mode and restoration instructions.

The independently reviewed [preflight continuation](preflight_resume.py) bound
the original failed log, start receipt, manifest, operator and already-built image.
It repeated all guards without rebuilding or changing services. The resumed
[preflight receipt](preflight-receipt.json) passed31 public checks and the previous
51 schema/565 content contract. [Activation](activate-receipt.json) then verified the
new 51/650 contract, saved state and the new native generation before the client
release and gateway opening. The host had710008832 free bytes at reopening;
recheck headroom before any future staging or backup.

The authoritative protected host evidence is under
`/opt/nightcap/releases/hate-layout-20261029-v1/evidence/`, including the stopped
backup receipt, quest preimages, content-install receipt, expected boot state,
market reconciliation and verified-closed/deployed receipts. Local summaries do
not replace those guarded originals. [review.json](review.json) records independent
operator, disk-continuation and final-verifier review and tests.

## Recovery and remaining QA

Retain 186-capable native code, private rows, grids, quests and client assets once
successor runs or corpses exist. A paired forward repair is the default recovery.
Do not run the isolated rehearsal inverse against live runs, restore an old player
snapshot, replay an uncertain inventory/publication write or downgrade to binaries
that cannot recognize successor state. A client correction must use a higher
release number than2026102901; preserve prior signed history. Any future production
change requires its own authorization.

The [owner QA checklist](../README.md#required-owner-qa) covers new level 46 entry,
creature models, doors, ground-level access to all four bosses and the Book of Souls,
patrol/pull difficulty, original loot/Hunt rewards, Raid gating/completion, Grind
respawns, reconnect persistence and old 76 run continuity. Automated route proofs,
runtime checks and successful publication do not establish those gameplay results.
