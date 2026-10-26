# Commonlands market: pairing and recovery

Candidate prepared. The owner authorized main promotion and live QA deployment
on October26; see [the exact authorization](deployment/AUTHORIZATION.md). Actual
activation and player acceptance are still separate.

## Before a release

Reconcile current main and live binary/client/schema evidence again. This candidate
is based on October24 coordinated v2 (deployed October25), not the older default
checkout. Build tool `tools/build_bazaar_candidate.py --resume` authenticates the
retained source, overlays only the selected bazaar sources and builds the complete
zone target. Keep its private manifest and exact source/binary hashes. It never
installs the binary. Never sync sources while its existing cmake process is live.

Run real-engine tests with `NIGHTCAP_TEST_DEPS` pointing to isolated PyMySQL and
`python tools/tests/test_bazaar_escrow.py`; these use a disposable tmpfs MariaDB.
Run `python tools/tests/test_bazaar_native.py` with MSVC or C++17. The fixture pins
the native custom-data parser/serializer and proves that unsupported metadata is
rejected before ownership moves. 32767 is native unlimited-charge persistence,
so a stack with that quantity is unsupported; ordinary charged objects retain it.

Rehearse the SQL against a private clone of the actual target schema, including
inventory's exact17 columns, transactional character_currency and absence of
triggers on the seven touched tables. No existing nightcap_bazaar_* table may be
silently reused. DDL is not transactional: a partial installation must be inspected,
never blindly rerun. State starts disabled, so partial readiness fails closed.
No inventory/currency/player records are rewritten by initial installation.

## Authorized activation only

A new production release requires owner approval under the branch policy. With
that approval, hold entry, gracefully stop the full supervised game runtime,
take and verify a fresh stopped backup, install the additive SQL once and pair
the exact reviewed zone binary with the current retained world/loader/cache/client.
This change adds no rules, shared ItemData fields, quest scripts or client assets;
world and item cache retain the current coordinated release. Verify all12 workers
use the intended zone and native/quest/database error counts remain clear.
Do not kill an individual production zone; its supervisor restarts everything.

Only after schema, binary and item-preservation checks pass, enable the one state
row (id1/version1) in a guarded operation. Perform QA.md with ordinary players,
including native search/inspect/direct delivery with zero vouchers, posting then
seller logout, partial stacks, proceeds, cancellation and planned restart. A client
button or voucher gate outside the Bazaar is an unresolved acceptance gate: keep
the market disabled until a paired client solution is verified if needed.
No signed client package has been changed or validated for this feature yet.

## Recovery

Disable new trading by changing only nightcap_bazaar_state.enabled from1 to0.
Keep compatible native code and all five new tables. Cancellation and collection
continue so owners can recover items/credits. Never truncate/drop escrow, restore
old player snapshots or replay a transaction whose COMMIT acknowledgment was lost.
The session quarantine intentionally disconnects on ambiguity, blocks stale saves,
and reloads authoritative inventory/wallet on reconnect.

Reconcile an incident using listing, remaining/status, item snapshot, seller
credit, inventory/currency and receipt together. Sold/cancelled item snapshots are
audit records, not inventory. Preserve later earned state. Removing the feature
requires a separately reviewed drain/reconciliation after all ownership is returned.

## Documentation

Record source, build, deployment and owner acceptance separately in evidence.json,
CHANGES/status and installed Nightcap knowledge. Six wiki articles have explicitly
unreleased candidate guidance; reconcile current published content and verify every
public file only as part of an authorized publication. No publication is claimed.
