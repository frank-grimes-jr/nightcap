# Multiclass tome learning — October 24, 2026

Owner authorized main and server deployment after the rogue audit. Candidate is
under verification; no deployment or native player acceptance is claimed yet.

Production snapshots, image/service fingerprints, build inventory, package
manifests and detailed receipts remain private and are excluded by this release's
.gitignore. Committed summaries report aggregate validation only. Operators use
the locally configured NIGHTCAP_DEPLOY_SSH_TARGET; no production address is
embedded in the published wrappers.

Tome learning now follows canonical held classes, including a secondary or third
Rogue when the primary class is a caster. Discipline learning/use levels remain.
The server scans every discipline slot for duplicates before choosing a free
slot, saves successfully before changing the profile, and consumes a right-click
tome only on success. Failed right-clicks preserve the original item instance.
The existing TrainDiscipline API still returns a replacement to consumed
hand-in/quest callers on failure. No AA catalog, balance, SQL or client changes.

## Plan and acceptance

1. Reproduce against the actual current native method and item-click branch.
2. Repair effects.cpp, client_packet.cpp and the client.h helper declaration.
3. Verify canonical ownership, level boundaries, full/duplicate lists, invalid
   definitions, database failures, compatibility refunds and exact consumption.
4. Build zone against authenticated retained live sources and reproduce the
   predecessor before compiling. Review source and rollout independently.
5. Integrate the scoped feature into dev/test, then promote its scoped main PR
   under the owner's explicit authorization. Dev/test already contain separate
   unapproved dungeon/quest candidates; do not include those in this deployment.
   Install one zone-only image layer with fresh stopped backup and preservation
   checks; verify all 12 workers before reopening access.
6. Update status/CHANGES, wiki guidance and installed knowledge with exact receipt
   and player-QA boundaries. Preserve the current signed client and content.

The right-click operation saves a discipline then deletes the inventory item;
it does not introduce a cross-table crash-atomic inventory transaction. A crash
between those operations can retain an already-known tome, but failure never
intentionally consumes the original. Existing trainer/quest refund semantics
return a newly summoned item, not the original instance. These boundaries are
distinct from the repaired normal/error paths.
The existing inventory deletion API also does not report SaveInventory/SaveCursor
write failure; that can leave an already-learned tome after reconnect. This change
does not claim transactional inventory persistence or repair that shared API.

## Verification

Independent tests compile real GetSpellMinLevel/GetMulticlassList, the canonical
catalog, learning methods and tome packet branch. Original source: 34 failures,
9 controls passing. Fixed source: all 43 pass on Windows/MSVC. Database/inventory
IO are isolated fakes; simulated reload does not establish live client acceptance.
All43 also pass on Linux. Adjacent early-scribing1, canonical spell-access2 and
cooldown27 tests pass. Independent review found and closed a rollback guard gap:
unverified or uncertain activation cannot be blessed as a fresh recovery baseline.
The revised source/operator has no remaining required findings. Full native build
and actual deployment evidence remain pending; owner gameplay QA remains open.

## AA and high-level tome audit

The production read-only audit matched all 530 released Rogue-accessible AA
ranks across 96 families to level-1 purchase requirements. All 1,845 compiled
policy ranks also return level 1. No generic AA purchase/activation gate above
60 was found. The reported AA problem still needs its exact name and error.
Assassinate's level-60 combat rule is separate; the Anatomy execute effect is
excluded from the released pool, and Assassin's Wrath is a different modifier.

Canonical Rogue tomes comprise 193 item records for 189 disciplines; 178 item
records require levels above 60. Widened item masks are not eligibility proof.
This repair preserves those discipline gates and fixes learning for eligible
held classes. Sneak Attack is a level-20 discipline and is a valid level-30
SK/Shaman/Rogue test. No AA or discipline-level rebalance was performed.

## Exact owner QA

- Karl, level30 SK/Shaman/Rogue: right-click Tome of Sneak Attack66390 from its
  bag. Exactly one disappears; Sneak Attack appears in Combat Abilities.
- Zone or reconnect: the discipline remains. Hide for at least four seconds,
  meet positioning/endurance requirements, and activate it; check reuse.
- Try another copy: rejection preserves the same item and location.
- A level19 Rogue cannot learn it; a level20 Rogue can. A non-Rogue cannot learn
  it even if widened item labels appear permissive.
- Repeat with Rogue in primary/secondary/third slots and an INT-caster primary.
- Higher-level disciplines remain level-gated. Releasing Rogue removes current
  use eligibility; it does not erase learned disciplines or grant another class.
- Full list and injected database-save failures are automated tests; do not fill
  a live player's list or break production persistence just to test them.
- All released rogue AA ranks remain level1; obtain the exact AA name/error for
  the original separate report before changing any AA mechanics.

## Recovery

No DB/schema/content/client migration. Retain the immediate prior immutable image
and all current player state. Rollback selects that image through the same
supported full-runtime stop/start, new stopped backup, guarded startup-expiry and
market reconciliation, worker/content/cache/client checks, then access reopening.
Never kill a single production zone or restore an old database/player snapshot.
An uncertain action must be inspected through its immutable receipts before any
continuation; do not blindly replay activation.
