# Advanced loot: owner live QA

The owner authorized direct main/production deployment on September 30, 2026.
These checks record **manual acceptance, still open**. See [production evidence](PRODUCTION.md)
for deployment status. The older [isolated fixture plan](QA.md) remains separate.

## Start here

1. Close the running Nightcap client and relaunch through the usual Nightcap
   starter. Let it install game release **2026093006**, then enter the live server.
   Use the managed Nightcap installation; leave `Client_RoF2_Dev` read-only.
2. Enter `/advloot`. Confirm a separate Advanced Loot window opens, can move/close,
   and reopens with the command. Check text, keyboard focus and usable buttons.
3. Turn on **Advanced loot**, **Apply filters** and **Auto show**. Leave
   **Auto loot all**, **Split coin** and **New items only** off. Use Ask for Bone Chips.
4. In **East Commonlands (`ecommons`, zone 22)**, defeat naturally spawned
   **a_decaying_skeleton** through ordinary combat until a corpse has Bone Chips
   (item 13073). Drops are random; an empty corpse is not a failed loot check.
   Stay within **25 units** when collecting. Record your chips and coin before/after.

No spawning, forced drops, database edits or server restarts are needed for this
live player checklist. The server's ordinary item rights and restrictions apply.

## Solo loot and saved filters

| Check | Expected result |
|---|---|
| Kill a skeleton with loot | Window appears with the item, quantity and corpse; coin is collected once. |
| Select, inspect, find corpse, then Loot | Correct item details and corpse; one award and row disappears. Repeated clicks give nothing extra. |
| Set Bone Chips to Always loot; defeat more skeletons | Eligible chips enter inventory automatically. Ordinary bags/corpse restrictions still apply. |
| Set chips to Never | Chips are not offered as personal loot or automatically collected. They remain on the corpse. |
| Open Filters, search Bone Chips, reset to Ask | New eligible chips await a decision; stored filters can be edited without a current corpse. |
| Leave a drop | Offer disappears while the physical item remains on the corpse. |
| Several corpses and duplicate chip rows | Each physical drop is distinct; search/paging works. Loot All takes eligible displayed/search-matching loot once. |
| Close the window; toggle automatic display | `/advloot` still opens it; the display setting controls automatic opening. |
| Save a filter/setting, camp and return | Same character retains it. A second character has independent choices. |
| Disable advanced loot | Automatic display/collection stops. Normal corpse looting works. Re-enable afterward. |

## Shared loot with two live characters

Use two consenting characters A and B, grouped and present for kills, with A as
leader. Start with both using Ask for Bone Chips.

1. Defeat another natural skeleton carrying chips. Both see the shared item and
   master. It should not disappear through competing automatic pickup.
2. A targets B and assigns the item. B alone can collect it. Leaving an assignment
   returns the item to shared control.
3. Start a roll: A selects Greed, B selects Need. After **60 seconds**, B wins.
   Repeat both Need, both Greed, all Pass and saved Always Need/Always Greed.
   Never excludes the character from an award while filters apply.
4. Open Free Grab and try both clients. Exactly one receives the item; automatic
   Loot All does not race for it.
5. Enable coin splitting on the collecting character. Record both wallets across
   several kills. Combined coin increases must equal the original purses, with
   per-denomination remainders going to the collector. Bots take no shares.
6. Camp the master with a decision pending. A connected participant who retains
   original loot rights becomes master. Pending votes, deadline and assignment
   survive. A later joiner must not gain ownership of an old drop.

## Restrictions and client lifecycle

- Kill from farther than 25 units: the owned row can be listed, but collection
  waits until you approach. Find Corpse helps locate it.
- Try with full bags, then make space and retry. Loot stays on the corpse until
  it can fit; the advanced window must not overflow the cursor.
- On a naturally acquired **NO TRADE** drop, automatic pickup/Loot All must not
  accept it. Manual pickup asks for confirmation; cancel grants nothing.
- With a naturally acquired **lore** item already owned, another copy must remain
  unawarded. Native augment/container restrictions also apply.
- Zone and return, camp/reconnect, use `/loadskin` with the managed skin, and
  close/reopen the window. No crash, stale-zone award or duplicate collection.
- Use normal corpse looting for an eligible pending item. The advanced row
  disappears. Classic looting cannot take another character's shared award.
- Check the existing pet window/commands and classic model appearance for
  regressions in the combined client package.

Record unencountered NO TRADE/lore/raid cases as **not exercised**, not passed.
Fault injection, saved-checkpoint replay, unusual quest vetoes and database commit
failures remain operator checks in the isolated plan; do not inject them live.

## Report a problem

Include character, zone, approximate time, item/corpse name, action, screenshot
and expected/actual inventory or coin change. For a suspected lost or duplicate
award, stop retrying that drop and preserve the state for receipt reconciliation.
Disabling advanced loot is the player fallback. Operator recovery must retain
the receipt-aware server and claims; an older binary or blanket DB restore can
resurrect awarded drops or erase later player progress.
