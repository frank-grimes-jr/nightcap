# October 17 combined release

The owner explicitly requested all recent changes on main and the server, with
documentation, wiki and patcher notes updated. This record owns the coordinated
release; earlier candidate reports retain their dated test evidence.

Status: complete server build/link and focused checks passed. Production activation,
signed channel publication and wiki publication are recorded separately below.
Owner gameplay and balance acceptance remain open even after deployment.

## Delivered scope

- Optional Recommended AA filter: up to ten next ranks across held classes,
  favoring survival, sustain and useful damage. Off by default; preserves the
  normal catalog, purchase authorization, prices and earned ownership. No new AA
  families or ranks are unlocked by this release.
- Six independent basic Monk attack timers, paired server and RoF2 proxy.
- Signed cooldown duration arithmetic and zero-duration completion fixes.
  Shared AA/item/spell/discipline identity collisions remain unresolved.
- Normal death EXP loss disabled with the existing default rule
  `Character:DeathExpLossLevel=256`; old losses are not refunded and Sacrifice's
  explicit cost is unchanged.
- Raise 20,490 existing stackable definitions below 100 to 100. Larger limits,
  nonstackables, recipes and other item columns are preserved.
- Reforging Box: three identical eligible Normal/Base items yield one Polished;
  higher qualities still require four and dungeon rewards remain separate.
- Retain the already activated 10% passive AA rate and idle worker correction.
  Retain Commonlands banker/Leather Padding operational evidence.

## Pairing and verification

The integration branch combines the separately tested feature commits. The
client proxy is 0.10.0 with 107 exact executable guards; signed game release
2026101702 retains all 106 managed files and changes only the DLL, AA window XML
and patch catalog. The minimum desktop launcher remains 0.6.0. Close the game
and use launcher Play to obtain the paired update.

`build.py` reconstructs the source from the fingerprinted deployed dungeon-journal
tree. Its 12-file reviewed delta is verified before a fresh full zone build;
`Client` layout changes prohibit reusing unrelated zone objects. World,
shared_memory, loginserver, UCS, supervisor and configuration scripts are retained.
There is no rule-catalog or ItemData ABI change. ItemData remains 1,332 bytes;
StackSize is the signed 16-bit field at byte 802.

Focused verification covers 816 recommendation class combinations; nine client
runtime groups and exact pinned executable guards; cooldown and Monk regressions;
2,048 native death EXP cases; actual inventory translation-unit failures and
reforge quest/package contracts; stack migration guards; launcher signing and
notes; server operator failures; and client publisher recovery. The six-failure
shared-identity audit is intentionally an open defect reproducer, not a passed
release test. `stacks-rehearsal.json` records nine MariaDB temporary-table cases
against the unchanged production preimage. See [QA.md](QA.md) for visible checks.

## Operator sequence

Check filesystem headroom before staging/building or stopping services. This
release encountered a full 72 GB production filesystem; only redundant transfer
archives and unused Docker build cache were reclaimed, with all image tags,
service lifetimes, volumes and backups preserved. Record the cleanup receipts
and require enough room for image layers, a full backup and regenerated cache.

Private staging is `/opt/nightcap/releases/october-17-2026`. Authenticate every
input through its release manifest. `rollout.py preflight` checks live rules,
services, source image, client channel, quests and content, builds an immutable
zone-only image, checks its ancestry/dependencies/native startup and predicts the
whole item cache with only the 20,490 StackSize fields changed.

After successful main promotion, `activate` stops the gateway and game together,
takes and verifies a stopped database backup, fingerprints player/custom data,
rehearses the death rule inverse, applies guarded item/rule SQL, installs the
matching quest, and starts the new game with access closed. Native hashes,
health, player data, unrelated content and the complete regenerated cache must
pass before `activated-closed.json` is written.

Then `client/prepare.py baseline` captures that exact closed-access state and the
reviewed publisher installs immutable assets before replacing the signed channel.
Verify its signature and all hosted files. `rollout.py open` verifies the pairing
and opens the gateway; `report` verifies the new lifetime and health again.
Publish the wiki only after activation. Each phase has exclusive receipts and
must not be replayed after an uncertain result.

## Recovery

An exception holds the gateway closed and keeps current data. Inspect the private
receipts, actual service state, channel and SQL before proceeding. Never replay
an uncertain mutation or restore player SQL from the pre-release backup. A
successful stop does not prove every native character flushed; this is recorded
explicitly in the shutdown receipt.

The immediately previous receipt-aware image and exact quest are retained.
The old image must pass hashes, native validation and login crypto checks before
selection. Return to it only with the matching old client: if the new channel has
been published, publish a newly signed **higher** release counter carrying the old
assets; do not serve the lower old counter. Keep the gateway closed until matching
client/server checks pass. Never silently restore a previous process lifetime.

Retain stack limits of at least 100 after access could have opened: players may
have formed larger stacks. Do not restore the old item cache or lower item limits.
Rebuild the cache from the current database using the retained ABI-compatible
shared_memory executable. Keep normal death loss disabled unless the owner asks
to restore it. Any quest rollback must preserve current inventory and receipts.
The SQL inverse is rehearsed only in temporary/rolled-back transactions before
access; it is not a post-release inventory recovery tool.

The client publisher's 15 failure/recovery tests cover interruptions around
channel replacement and closed gateway pairing. The server's seven operator tests
exercise stale preimages, cache changes and failures before/after opening access.
The wiki updater tests and performs a pointer rollback rehearsal while preserving
private downloads, origin configuration and all five service identities.

## Wiki impact

Reviewed all 21 maintained articles, 432 generated reward routes, commands,
catalog values, home, Features and Recent changes. Changed AA, combat, death,
stack and reforging guidance together; retained unrelated unreleased systems.
Reward values are unchanged. Reconciled older source drift for already deployed
AA class ranks, dungeon launch and journal repair against their dated deployment
records. Source review, actual publication and gameplay acceptance are distinct.
