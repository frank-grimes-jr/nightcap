# Rogue tome repair phase — October 24, 2026

Built: canonical held-class tome learning, item-preserving right-click failures,
whole-list duplicate detection and save-before-profile ordering. Public consumed
hand-in/quest refund behavior remains. Independent native tests cover43cases on
Windows/Linux; the original source failed34with9passing controls. Adjacent
early-scribing, class access and cooldown checks pass. Rollout guards have24offline
test groups on both platforms; independent review's rollback-baseline finding was
fixed. Exact [release status and QA](../releases/rogue-tomes-20261024/README.md).

Excluded: discipline level reductions, early tome storage, AA catalog/balance
changes, inventory persistence redesign and automatic player grants/refunds.
All released rogue AA purchase levels are1; the unnamed client AA report remains
unresolved pending its exact name/error.

Delivered: scoped main PR330 and verified production activation; 12 workers,
93 saved-state tables, 577 contract checks and fresh backup pass; access is open.

Open: actual client right-click/activation/relog QA and broader inventory
crash/write atomicity. Wiki20261024-rogue-tomes-v1 verifies all 483 public files;
16 Linux publisher/recovery tests pass and only three files changed.
The user explicitly authorized main/server deployment; this is not gameplay
acceptance. Never restore player snapshots during recovery.
