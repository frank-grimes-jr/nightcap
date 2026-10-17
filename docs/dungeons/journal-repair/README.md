# Dungeon journal repair — October 16, 2026

Candidate repair for Palwar's live Befallen Raid report: the task title appears,
its objectives are blank, and a yellow completion message follows a named kill.
The read-only production check at 23:14:43 UTC found one personal objective
(skeleton Lrodd), no full-clear entitlement, and matching saved task activity.
Credit was retained. Run entry and a named kill are now owner-confirmed; checklist
rendering failed. Full-clear rewards and broader gameplay acceptance stay open.

## Cause and behavior

The installed task rows use None (0) activity types and all-zero steps. None is
supported by the native serializer but the owner reports blank RoF2 objectives;
the client rendering explanation remains an inference until visible retest.
The retained native `Tasks::GetActiveElements` also treats all-zero steps as
sequential, hiding later bosses. Its last required sentinel never completes,
so ordinary native completion cannot add the dungeon to Completed history.

The repair projects tasks 9700–9713 into explicit Kill (2) display activities,
still updated only through METHODQUEST and the authoritative dungeon ledger.
All bosses are active together. The required sentinel is step 1 and is never
credited. Task completion hooks and native task rewards cannot fire through the
dungeon service. A separate ledger-to-history adapter persists full clears and
sends Completed history, then removes only the matching active display.

Entry and Keeper Status print the required names and personal progress. A newly
credited boss gets a message naming it and explaining that the dungeon is still
in progress. The client's yellow Task Stage Completed notice represents a boss
objective. Full completion requires every personally credited boss. Permanent
counts and earned reward receipts remain in their original ledger.

Saved task acceptance times preserve the active display across reconnects.
Abandonment reconstructs the display without changing credit or reward rolls.
History failures retry on entry or Keeper inspection even after expiry/reset.
An old completed run cannot remove a newer active run of the same task; ambiguous
same-second acceptance times are conservatively retained until reconciliation.

## Verification and release boundary

`tools/tests/test_dungeon_journal.py` compiles the actual task projection, Journal,
history adapter and history recovery with failure-capable native fixtures. It
also executes the retained, manifest-verified `GetActiveElements` template for
all fourteen mode definitions, including out-of-order credit. Four journal tests
and all fifteen dungeon tests pass. The source review has no unresolved required
findings. These checks do not establish visible RoF2 acceptance.

Three previously untracked native task files are copied from the exact deployed
source baseline, then minimally patched. Compare them with the source hashes in
`../native-build-manifest.json`, not an older local overlay. `build_candidate.py`
compiles the three changed translation units without an old precompiled header
and links the fingerprinted retained objects. Added nonvirtual/free declarations
do not change object layout. Full input and binary manifests accompany the build.

This is a native zone repair: no migration, catalog revision, item definition,
shared ItemData ABI, rule catalog, quest or client asset change. Retain the
matching deployed world/shared_memory and production cache. Verify the actual
live pairing before installation; startup may regenerate cache from current
content. Do not install the old local-content cache or rerun initial dungeon SQL.

Production installation is pending. A controlled whole-runtime restart is
required; a quest reload is insufficient. Coordinate timing with the owner's
active raid. Use deployment/GM locks, fresh current preimages, closed access,
stopped backup, immutable zone-only image, running process/hash/health checks
and preservation checks. Preserve current run UUIDs, kills, corpses, claims,
inventory and expiry. Never reset the run or restore an older player snapshot.
The existing deployed dungeon image is the only compatible rollback candidate;
do not roll back past the dungeon service. Reconcile any history write after
access before retrying. Build, installation and owner acceptance are separate.

## Exact in-game retest after installation

1. Re-enter Palwar's existing Befallen Raid without resetting. Select
   **Befallen - Raid** in Tasks. All five names must be readable: skeleton Lrodd,
   Priest Amiaz, the thaumaturgist, Boondin Babbinsbort and Gynok Moltor. Previously
   earned credit and the original remaining time must be retained.
2. Hail the floating-eye Keeper (`/target Instance_Keeper`) and choose Status.
   Match each Required/Complete line to Tasks. Entry must also print this list.
3. Kill an uncredited miniboss. Its row completes and the other rows remain
   visible. The boss-credit chat names it. A stage notice must not add a full
   completion or deliver the personal item early. Gynok unlocks after four minis.
4. After the fifth personal credit, the active run disappears and Befallen - Raid
   appears under Completed with its boss objectives. Keeper count increases once;
   the existing reward path grants one item or retains a full-inventory claim.
5. Reconnect and inspect again. Credit, history/count and reward stay unchanged.
   A new run must start with clear objectives while the prior completion remains
   in history. On a disposable run, abandon Tasks and use Status to reconstruct.
6. Repeat checklist/out-of-order/full-clear/history checks for Grind and the
   remaining dungeon modes. Use an isolated test server for history-write faults,
   expiry/reset races and forced instance-ID reuse, never the live player's run.

Wiki assessment: dungeon guide and Recent changes need stage/full-clear and
blank-objective fallback guidance. Features, home, travel, commands, equipment,
generated hunt catalogs and the remaining articles keep their existing mechanics
and Live testing labels. No artwork, search, item stats or client update is needed.
