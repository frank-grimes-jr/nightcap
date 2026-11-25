# Classic sympathetic inventory clicks

The production operator activates the six Ascended item definitions from gameplay commit 2d66fe1b6, promoted in main PR 534. Its four SQL files are the installed-world subset of the general migration. They require the two historical equipped clicks, four empty new clicks and the expected lower qualities. They update only changed click fields. The two spell definitions are checked read-only.

The v2 stage built the full item cache inside an isolated database on OVH. All 324,798 records were compared by item ID against the live cache. Six records matched the predicted click bytes and 324,792 matched their prior definitions. The SQL rollback restored the earlier item values before the final forward build. See [preflight evidence](production-preflight.json).

The previous v1 stage stopped on its initial disk-space check. V2 uses the separate archive filesystem for the candidate cache, logs and stopped backup. It checks headroom for the database clone and normal live runtime caches on the root filesystem. The title, stock item and equipment release operators provide the existing deployment locks, occupancy check, save drain, backup, startup validation, saved-state checks and market rotation checks. Never replay a completed activation. If activation stops after SQL, inspect its receipt before any recovery.

Use the [player QA steps](../../items/sympathetic-clicks/inventory-sources-20261125.md) after the open-world receipt exists. Reconnect and test each Ascended item from a general inventory slot and from an open bag.

The [published Equipment guide](https://wiki.nightcapgame.org/equipment.html#stock-sympathetic) covers all six inventory clicks. The [publication receipt](wiki-publication.json) and [HTTPS verification](wiki-https.json) cover 631 files and five private paths. Player QA remains open.
