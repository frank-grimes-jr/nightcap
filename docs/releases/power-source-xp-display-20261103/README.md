# Power Source training display — OVH release 2026-11-04

Owner fast follows on November 3: show where a training item is, and stop it adding
stats. Owner: "Yes, build both". Zone binary only, on top of
[Power Source item XP](../power-source-xp-20261103/README.md). Owner gameplay acceptance is open.

## What changed (patch `85dd2cea`)

- **Progress in the name.** An item training in the Power Source slot (slot 21) is sent
  to the client as `<name> [Training N%]`, or `[Trained]` at top tier, capped at the
  client's 63-character name limit. The name re-sends each time the whole percent
  changes. The chat message still fires only at 10% steps. Item links (`ItemPacketViewLink`)
  and real Power Sources keep their plain names.
- **No stats from slot 21.** The server already ignored the bonuses, but RoF2 sums the
  stats it sees in the item packet. Slot-21 training items, and the augments in them, now
  serialize with stats, resists, heroics, mods, haste/atk/damage shield and the
  click/proc/worn/focus/bard effects zeroed. The database item is untouched.
- **Swaps refresh both sides.** Moving an item into or out of slot 21 re-sends it to its
  new slot, so it shows stripped in 21 and full stats elsewhere. An item lifted from 21
  onto the cursor is re-sent full when it is placed. Packets are never pushed to the cursor.

`item_xp_policy.h` (`Percent`, `TrainingName`), `patches/rof2.cpp`,
`advanced_loot_inventory.{h,cpp}` (`RefreshTrainingDisplay`, award re-send),
`inventory.cpp` (`SwapItem` hook). Tests: `tools/tests/test_item_xp_policy.py`
(name and percent) and the `item_xp_award` fixture (packets per award; sub-percent
award sends none).

## Build and rollout

`build.py` copies the deployed Power Source source (`/tmp/nightcap-power-source-xp-20261103-v1`,
stripped zone `7b61b96c…`). It asserts those five files equal `85dd2cea^` (CRLF-normalized),
overlays the patch and builds zone only. World and shared_memory don't serialize items
to the client, and there is no rule or schema change. Stripped zone `335cbce1…`, ELF identity
passed ([native-identity.json](native-identity.json)). `rollout.py` chains the Power Source
release's guards, including its exact rule catalog check. No SQL. The boot log is checked
for `MySQL Error` and `Orphaned Rule`.

## Production (OVH, 2026-11-04 09:55 UTC) — deployed

Staged from `d6cccb8a`. The first staging attempt hung on its opening SSH check before
uploading anything, so it was killed and rerun. Preflight (run detached) built image
`da797daf…` over `3999a935…`; only the zone layer differs. Activation stopped gateway and game and took the stopped backup
`private-backup/peq-before.sql.gz` (66,149,554 bytes, gzip integrity passed). Game booted at
09:55:57 with access closed. Binaries, saved state, market, contract and rule catalog
verified. `open` restored the gateway. No client update; `database_restored: false`.

Rollback: `rollout.py rollback` only for a held activation before access reopens.
After that, redeploy the Power Source release image (`3999a935…`). The item data is the same.
Never roll back to binaries older than Power Source XP once items have trained.

Not verified: any in-game behaviour.

## Owner test

1. Put a training item in slot 21. Its name reads `[Training N%]`. Character stats
   (HP, mana, AC, attributes, resists, haste) do not change from before you inserted it.
2. Inspect it in slot 21: stats and effects show as zero. Link it in chat: the link
   shows the real item.
3. Kill a few mobs: the percent in the name climbs about 1% at a time, without relogging.
4. Drag it back to a bag or worn slot: full stats and the plain name return. Lift it
   from slot 21 to the cursor and drop it: same.
5. An augmented training item: the augment's stats don't count either.
6. A real Power Source in slot 21 keeps its normal name and stats.
7. At top tier the name reads `[Trained]`.
