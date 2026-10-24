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

Open: actual client right-click/activation/relog QA, broader inventory crash/write
atomicity, and deployment/publication verification until recorded by receipts.
The user explicitly authorized main/server deployment; this is not gameplay
acceptance. Never restore player snapshots during recovery.
