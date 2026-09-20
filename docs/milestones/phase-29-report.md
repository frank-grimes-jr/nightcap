# Phase 29 - Finite living economy

Date: 2026-09-20. Candidate follows the EC tunnel hub on dev/test.

## Built

- Twelve eligible city merchants, ten distributed quantity-one lower-tier finds
  per generation, with normal merchant stock untouched.
- Ten playable-appearance tunnel NPCs, six sellers/four buyers, exact linked
  offers, bounded shared auctions and occasional local chatter.
- Twelve reviewed Classic items with captured P1999 Green references, income
  adjustment and explicit seller/buyer spread. Five finds and seven tunnel items.
- Durable restart-only generation; era and earning-rule guards; atomic native
  item/wallet/stock/audit exchange, stale-quote rejection and uncertain-commit
  quarantine. Explicit ordinary hand-in refunds.
- Disabled setup, ownership-guarded content, scoped rollback, native/SQL/quest
  regression tests, map evidence and precise [owner QA](../economy/QA.md).

## Not Included

No client patch, unlimited traders, player population-count spoofing, arbitrary
loot-table scan, live wiki requests, global item repricing, or automatic later-era
catalog expansion. No change to drop rates or vendor rules themselves.

## Remaining Gates

See [verification](../economy/VERIFICATION.md) for current build/test completion.
Activation requires the paired build, verified backup and controlled restart.
Owner in-game UI, persistence/recovery and pricing-balance acceptance remain open;
no main promotion is implied. The 10.53x estimate represents combined loot-sale
income, not direct coin drops. Initial breadth is intentionally small and should
be expanded only after economic feedback and fresh source verification.

## Operational Learning

Native temporary stock can acquire a synthetic merchant slot while a window is
open. Allocate above all hidden/native slots, detect collisions, close the quote,
and guard the central purchase dispatcher so queued packets cannot fall through.
Currency updates must also refresh carried weight. Atomic storage alone does not
prove native client presentation; retain normal-account in-game QA.
