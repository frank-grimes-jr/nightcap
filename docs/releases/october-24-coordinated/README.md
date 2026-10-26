# Coordinated October 24 release

Owner instruction: coordinate all pending changes and move them into main and the server. This authorizes this release's promotion and production activation; it does not record gameplay acceptance.

## Release scope

- NPC departure removes matching stale feign memory; restored stationary NPCs retain canonical homes. The original Lower Guk bedroom train is not proved resolved.
- Newly enrolled High Keep Raid runs include guard suspicion, alarm, compact boss route and Osargen extraction. Existing runs, Grind and public High Keep retain prior rules.
- The Ashen Compact adds the held-Shadow-Knight level50 campaign, curated Kael, fourteen items, native journals and Everfrost entrance/return. Paired HE91 archives preserve Camil HE90 and existing models.
- Integrates already-published handbook, Build Lab, loot finder, Hole and Rogue tome wiki work into the release source. Retains production tome learning and all prior gameplay fixes.

Older NPC Admin PR122 and superseded historical PRs are separate from this queued test release unless the owner explicitly adds them.

## Pairing and activation

Build from the fingerprinted retained Rogue tome source; exactly the reviewed current native overlay may differ. Ship world, zone, shared_memory, three guarded SQL components, fifteen exact-ID scripts, the regenerated item cache and signed client2026102402 together. Classic50 remains; only curated zone113 access is added.

The guarded operator rehearses the actual production public schema/content in a temporary clone, validates51 schema/565 content checks, exact four new table definitions and441 reward-cache definitions, and preserves all prior cache records. It refuses existing Kael instances/saved spawns and colliding reservations rather than clearing them. Full native restart is required.

Before changes: hold gateway, stop full game with exit0 and below the supervisor's75second kill deadline, capture current saved state and a new verified stopped backup. Apply each component once with immutable attempted/committed receipts. After cache/binary/content pairing, enable both new admission flags in one transaction. Verify all12 workers, exact player/custom-state preservation, native expiry and market rotation before reopening. Publication occurs only after verified activation.

The independent review found and closed an opening guard gap: campaign/schema failures now hold the runtime before delegation. Unit and independent failure tests cover no reopen/no restore on failure. Detailed production inventories and receipts remain in ignored private/ and private host stages.

## v2 package

The v1 preflight stopped in `cache_check`: Warhelm 990510 stores races=4095, but `ApplyRacePolicy` loads wearable player gear with every race (65535) and the contract copied the SQL mask. The owner confirmed every race may equip it, matching Camil's Winged Helm. `tools/dungeon_contract.py` now projects loaded races; only the 990510 case changed. Natives were rebuilt and packaged as v2 (`private/v2/`, host stage `october-24-coordinated-20261024-v2`). v1 package, stage and `preflight-v1.log` are retained. After pruning 1.545 GB of unused Docker build cache (the disk was 98% full), the v2 preflight passed with the full cache contract (441 items, 882 drift rejections) and 0 changed existing items.

## Deployed

v2 was activated on 2026-10-25 at 11:41 UTC and access reopened. [`open-receipt.json`](open-receipt.json) records the PASS: v2 image `a2a40ce1c2d9`, world/zone/shared_memory matching `native-build-manifest.json`, 12 zone workers, restart count 0, 0 native/quest/database errors, 92 state tables, verified stopped backup, campaign flags enabled, client 2026102402, no database restore. Owner gameplay acceptance (QA.md) is open.

## Recovery

Never restore an old player snapshot, replay uncertain SQL, or downgrade to old dungeon completion code after new rescue/campaign runs exist. Pause new enrollment by setting both new flags disabled in a reviewed guarded operation; retain compatible schema, content, items, receipts and native runtime for earned delivery. Any uncertain activation stays closed pending receipt-aware diagnosis and tested continuation. A fresh recovery needs a fresh stopped backup and the current signed client/wiki pointers.

Nineteen explicitly reviewed unmounted historical staging files were losslessly compressed; adjacent .oct24-recovery.gz files and original-byte hashes retain recovery. The first pass stopped at a shared-inode file without modifying it; a separate continuation selected only verified single-inode files. Old historical operators require restoring their exact pinned staging files first. Active images, installed files and database backups were preserved.

## Acceptance boundary

Source/native tests, target rehearsal and delivery are distinct from full in-game route, model, pacing and balance acceptance. Exact owner checks are in QA.md and the linked feature checklists. Current status and final receipts are added after activation.
