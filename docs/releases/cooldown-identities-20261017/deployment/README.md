# October 18 authorized live-test rollout

The owner explicitly requested promotion to main and deployment to the server
for live testing on October 18, 2026. This authorization covers the reviewed AA,
item and discipline identity correction; it does not declare the remaining shared
skill/content groups fixed or establish gameplay acceptance.

Stage `/opt/nightcap/releases/cooldown-identities-20261018` privately on OVH.
The manifest authenticates every input, the retained runtime helper, the previous
native image hashes and unchanged signed client channel. Candidate zone SHA256:
`d3908e0348715e94955d84f629e4f27e91f15c7dd661e437efbba580ce3d216a`.
The complete candidate tree was built from the prior fingerprinted release;
only `bin/zone` changes in the production image. During staging, signed client
2026101801 superseded 2026101702: all 106 previous assets remain byte-identical,
including the proxy and timer configuration; 32 Classic zone S3D assets were added.
Preserve that newer channel and bind the manifest to its reviewed hash. The initial
preflight rejected the channel drift before changing access, runtime or SQL.

`rollout.py preflight` checks healthy service lifetimes, disk space, absent
migration state, exact live binary/catalog/cache/client inputs and private native
ports. It builds and validates the immutable image without changing access.
The previous receipt-aware image is retained and verified offline.

After main promotion, `activate` holds deployment/GM locks, rejects maintenance
or an in-flight GM write, stops gateway then the whole game, and verifies both
stopped. It fingerprints player/custom state, saves exact timers and item
timestamps privately, and takes a fresh gzip-verified full database backup.
Exit zero does not prove every native character flushed; the shutdown receipt
preserves that limitation. No individual zone is killed.

The stopped catalog generates forward and reverse SQL through the reviewed
generator. The operator hashes these inputs and rehearses both directions in a
fresh, explicitly named disposable schema, using actual catalog columns, timers
and item timestamps. It removes only that schema. A failed rehearsal leaves live
timers unchanged and both services stopped.

Before live SQL, an exclusive attempted receipt prevents blind replay. One
MariaDB session applies the guarded conversion without `--force`. Verification
requires the exact schema receipt, unchanged old timer rows/item timestamps,
an exact timer backup and a bounded successor for every active possible deadline.
No timer wipe or player-data restore is allowed.

The candidate starts with gateway closed. Verify all twelve running zone hashes,
retained other binaries, two healthy checks at least sixteen seconds apart,
stable lifetime, zero restarts and no detected native/quest/SQL errors. Preserve
all player/custom data except explicit timer additions and the existing market
startup rotation. Authenticate exactly one market epoch increment, unchanged
policy, expected fresh offer count/eligibility and unchanged trade audit. The
whole item cache, rules, catalog, quests, public client and unrelated service
lifetimes remain unchanged.

`open` rechecks the frozen manifest, conversion, preservation and market receipts
before opening the gateway. It never compares/restores old player snapshots after
access may have opened. `report` verifies the running release and schema receipt.
The exact owner test route is [../QA.md](../QA.md).

## Failure and recovery

Each failure independently attempts to stop both gateway and game, even when one
stop has an uncertain acknowledgment. The held receipt records actual observed
states and stop failures; never assume a hold succeeded. Inspect all receipts,
service state and the authoritative database receipt before taking another step.
Do not repeat `activate`, replay forward SQL, or silently start the previous
uint16 binary after migration may have committed.

To roll back, keep gameplay stopped and a fresh current backup. Use the retained
original migration catalog and reverse SQL under the same maintenance locks,
after checking current catalog/schema preimages and every new key's mapping.
Verify current deadlines were conservatively folded back, the receipt is absent,
and **all** namespaced rows were removed before selecting the retained image.
Never restore the pre-release player snapshot. Unknown new keys or drift keep
access closed for a revised reviewed recovery. Old code restores old collisions.
After access has opened, preserve every subsequent earned item, timer and receipt.
