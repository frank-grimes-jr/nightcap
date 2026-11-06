# Augment-only main and OVH release — November 6

Owner: **“Looks good. Merge the augment changes to main and deploy to OVH for live QA.”**
Icon artwork is accepted; gameplay/solo balance QA remains open. This release
uses the main-based augment candidate and excludes the separate capacity
configuration on dev/test. Native/quest source matches the tested source; no
client assets, rules, ItemData ABI, capacities or quest scripts change.

Payload: zone `bc88a4688d722c89f882ddb3328cf0d26867781fea49199ef681abe4f6c51892`,
232 item definition updates, exactly two zone enable flags (48 and186), matching
shared item-cache regeneration. Preserve compatible current world/shared_memory
and the current signed client. Existing metadata-aware binaries remain required.

Fresh probe on November6 matches live display zone335cbce1/image da797daf, healthy
services and >21GiB free. All reviewed 232 full item rows, 56 zone rows and17
spell definitions match. Private probe/capture stays out of Git/public outputs.

`rollout.py preflight|activate|rollback|open` chains the retained November4
operator's authenticated guards. Every action holds both deployment/GM locks and
rejects replay or a maintenance fence. Preflight builds a zone-only image,
clones public content, applies/inverses the exact SQL in isolation and runs both
loaders. It requires exactly232 cache records to change and every unrelated
record/identity to match. Full content contracts remain checked: any changed
expected values are derived by the same query against only the rehearsed target
item/config tables, with SQL fingerprints bound, and inspected before activation.

Activation closes access, performs a supported whole-runtime stop, takes and
validates a fresh stopped backup, applies full-preimage transactional SQL and
boots the matching image/cache. It checks unrelated content/rules, the complete
saved-state boot model, one market rotation, all native identities and cache
records before reopening. The old full-row guards now also have indexed identity
predicates; this avoids production-sized scans without weakening any preimage.

Failures hold access closed. `rollback` is allowed only after a held activation,
before opening, and only for a complete known before-state or after-state. It
inverses item/config definitions and boots the compatible base image; it never
restores player snapshots. After opening, inspect receipts and use a fresh
compatible forward repair. No automatic replay and no single-zone process kill.

Six Linux tests exercise exact cache change sets, indexed/full-row predicates,
complete contract/SQL binding, pre-stop drift, held SQL failure and held access.
The complete release candidate's 52 checks and native link evidence remain in
`docs/audits/augments-20261106/`. Stage/preflight/deployment receipts are added as
each phase actually finishes; authorization alone is not completion evidence.

Live QA: fully relog for refreshed item definitions; test High Keep Guard Heltch
(6000), Guard Golgon(6001), Qeynos Hills Guard Yalroen(4048), Osargen rescue adds,
daytime Kithicor, Cazic-Thule and new Hate Blackspire, both expeditions, shield/
dodge/focus stacking, full bags/forging and saved corpse recovery. Follow the
complete nine-part spike in the audit README. No client download is required.
