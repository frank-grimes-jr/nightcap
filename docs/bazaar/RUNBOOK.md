# Commonlands bazaar operations

Current release: combined main PR345/e43f2d4b and the integrated world/zone/shared_memory
runtime are deployed for live QA. Signed client2026102601 provides Sell / My Listings;
existing commands remain available. All12workers,51schema/565content checks and
102saved-state tables, including all5Bazaar tables, verify. Native owner QA remains
open. See [current evidence](seller-panel/evidence.json), [release procedure](seller-panel/deployment/README.md)
and [button-based QA](seller-panel/QA.md). The earlier command-only deployment below
is historical evidence, not the current binary/client pairing.

## Before a release

Reconcile actual main, current runtime/client/schema and deployment ownership.
The combined builder tools/build_bazaar_grip_integrated.py authenticates and preserves
the weapon-only source/binaries before adding the four Bazaar panel inputs. Full
source/binary manifests and ELF runtime-identity proofs retain exact provenance.
Do not edit sources under an active build. Use the guarded operator and fresh
stopped backup; never kill a production zone or replay an uncertain operation.
Recovery must retain grip-aware code once1HS metadata exists; a blind rollback to
pre-grip binaries can load2HS beside shields. Never restore old player snapshots.
The exact prior unmounted Bazaar stage executable is losslessly archived with its
restoration receipt; restore/authenticate it before old stage use, not as a live rollback.

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
CHANGES/status and installed Nightcap knowledge. Six bazaar guides describe live testing and unresolved native acceptance. Wiki
publication is recorded separately in deployment/wiki-publication.json and
wiki-public-verification.json; local edits alone never establish publication.
