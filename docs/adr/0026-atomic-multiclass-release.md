# ADR 0026: Atomic multiclass release

> Current status (2026-09-15): implemented server/AA/PoK candidates are deployed for live QA; main gameplay acceptance remains pending. See [current status](../status.md). The dated evidence below retains its original scope and is not a current deployment checklist.


Date: 2026-09-13. The design and before-state evidence were recorded at eedc168.
Current status: candidate implemented on feature/aa-ownership; verification and
remaining gates are tracked in ../balance/native-aa-class-release-candidate.md.
No deployment or promotion has occurred.

## Problem and required result

The current Perl plugin updates character_multiclass, then calls the native
PurgeAfterClassRelease. That method refunds only currently usable ranks, erases
the usable map, deletes persisted AA rows, and calls SaveAA/Save independently.
SaveAA now preserves canonical earned ownership, so the released family survives
in storage. A six-rank Wizard family costs 30 points; with only three ranks usable,
the current release refunds 18 rather than 30, and complete suspension refunds zero.

Replace the sequence with a boolean native ReleaseMulticlassSlot entry point.
One transaction must commit the slot change, canonical earned-AA removal/refund,
wallet/spent/expended counters, and retained-class skill clamps. Failed or uncertain
persistence must not publish a successful class change.

## Implementation contract

- Validate integer slots before narrowing in Perl/Lua bindings. Only 2 and 3 are
  valid. Reject missing/invalid class IDs, duplicate classes, primary conflicts,
  and stale session versus persisted slots. Releasing Second promotes Third.
- Stage the retained mask without calling LoadMulticlassMask or changing session
  fields. Remove inaccessible families from the canonical earned map, including
  suspended ranks. Keep shared-class families irrespective of expansion access.
- Refund canonical cumulative cost for eligible non-grant-only ownership. Remove
  class-only grant-only families without refund. Match the existing nominal-cost
  policy: storage does not distinguish a free grant of an ordinary family from
  a paid purchase. Do not refund an already consumed charged AA; account for
  remaining charges consistently with the existing bulk-refund policy.
- Extend the shared persistence transaction to lock/compare class slots and
  skill preimages alongside ownership and counters. Verify participating tables
  are InnoDB. Check overflow before writes; rollback every participating change
  on any statement failure. No separate class UPDATE in the quest plugin.
- Stage skill values, persist their rows inside the transaction, then publish raw
  profile values and OP_SkillUpdate after commit. Do not call SetSkill during
  staging or publication: it independently writes the DB and changes RAM.
- Publish class fields/mask, usable AAs/profile, bonuses, packets, and success
  messages after acknowledged commit. Avoid a trailing general Save and avoid a
  second class read through SendAlternateAdvancementTable during publication.
- An uncertain class commit requires a fresh session, not just the earned-AA
  invalid latch: stale class/skill state can otherwise authorize gameplay and
  write skills back. Use immediate disconnect or a proven broader invalid-state
  guard; reconnect must reload all relevant state.
- Close SetMulticlassSlot's Lua-exposed bypass: clear via the atomic release;
  reject occupied-slot replacement unless a complete atomic replacement is
  implemented. Preserve same-class no-op and empty-slot selection semantics.
- The Perl plugin calls the new native boolean and reports failure without a
  fallback SQL mutation when the new binding is unavailable. Deploy plugin and
  matching binary together. Retire or safely gate the legacy write-then-purge API.

## Evidence and remaining tests

The seven initial controls cover full, partial, and suspended Wizard AA267 rank6;
shared Natural Durability rank6; both update-failure locations; and Second-slot
promotion. They exercise 36 native operations. These are ownership-state probes,
not a full logged-in character simulation. The mock client has ClientDataLoaded
false, so the old general Save exits early. The failure counter distinguishes an
armed character-update trigger from an actually executed failure; this limitation
must not be presented as proof of the live Save failure path.

Before accepting the implementation, extend controls to actual skill values and
skill-only releases, class-only grant-only and charged families, duplicate/stale
requests, invalid binding values, failure after class/skill writes, and postcommit
packet/session behavior, including actual GetClassMask bits and bonuses before
the harness recalculates them. Run matched native before/after controls, a fresh full
build, appropriate regressions, and explicit in-game QA before promotion. Native
reconnect and uncertain-COMMIT behavior remain explicit gates.

## Passive toggle priority

Read-only audit of both PEQ and the balance clone found 40,724 spells, 1,570 AA
abilities, 6,655 ranks, and no spell containing SPA472 (Buy_AA_Rank). Thus no current
spell can satisfy UseTogglePassiveHotkey. The source still has a reset/rebuy toggle
hazard, but adding a toggle requires a durable independent selection state or a
reviewed pair-aware ownership model first. Do not infer that today's empty toggle
pool remains empty after an expansion/catalog change. Evidence:
../balance/aa-toggle-catalog-audit.json.
