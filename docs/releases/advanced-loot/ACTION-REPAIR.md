# Advanced loot action repair — October 2, 2026

## Accepted behavior and evidence

Owner reports Loot All silently does nothing and requests Ignore next to each
item, saved in a filter list. Owner authorizes main and live publication before
their in-game acceptance. The running 0.7.3 client log shows All clicks, sent
commands and accepted server snapshots. This establishes that clicks reach the
server; it does not establish why each individual transfer failed.

Source diagnosis: earned drops appear throughout the zone but all collection
was restricted to 25 units; All silently discarded decline results and skipped
NO TRADE. The range regression failed before the fix and passes afterward.

## Change

- Advanced collection permits explicit earned corpse rights anywhere in the
  current zone/instance. Classic clicks and public corpses keep 25-unit range.
  Existing corpse, player-state, lore, cursor, bag and receipt checks remain.
  Existing automatic earned coin collection/splitting now shares this range.
- Loot All processes eligible items across the matching paged list, with the
  same ordering/result limit. It reports delivered/unavailable outcomes; an
  uncertain transfer stops the batch and requires reconnect rather than retry.
- NO TRADE items require a second bulk click within 30 seconds. Consent is
  scoped to session/revision and exact captured physical items, including bag
  contents and corpse generation. New drops are excluded; every transfer is
  rechecked after preceding quest callbacks. Changed state cancels consent.
- Each drop has Ignore; it saves Never for this character. Filters has Remove,
  returning the item to Ask. Existing Use saved rules setting still controls
  application; the filter is persisted even when that setting is off.
- Loot All, Filters and Settings are prominent. Search is in Filters; returning
  to loot clears search so invisible text cannot restrict bulk collection.

## Candidate verification

Actual production bulk functions compile in a dependency fixture covering
multi-page batches, decline/uncertain outcomes, expired/replayed confirmations,
new drops, changed bags and a callback mutating the next item. Native callback
fixtures cover direct Ignore/Remove, confirmation, cancellation and expiry.
The access fixture and four UI geometry checks pass. These do not establish
native rendered or real inventory acceptance. Independent review found no
remaining concrete correctness or consent-expansion blocker.

Fresh paired world/zone build and signed client release are pending. The
candidate retains current main's spell-menu fix and current production assets.
No database schema/rule/quest mutation is required. Rollback may use only a
receipt-aware server image; never restore a pre-award database or erase receipts.

## Owner live QA after publication

1. Close EverQuest normally, click Play in the existing launcher, enter Darthy
   in East Commonlands, and open `/advloot`.
2. Kill eligible mobs with several tradable drops. Move over 25 units away;
   Loot All must put eligible items from all pages in bags and show a count.
3. Ignore Bone Chips directly on its row. Filters must show Never loot; relog
   and confirm the saved rule persists. Remove it and confirm it returns to Ask.
4. With a NO TRADE drop, first All collects tradable items and offers Confirm
   NO TRADE. Second click collects only the prompted set. Navigation/expiry or
   changed drops must require a new review.
5. Full bags, lore conflict or occupied cursor must produce visible feedback
   without deleting/duplicating items. Public/unowned corpses remain range-bound.

Manual gameplay acceptance is pending the owner's live session.
