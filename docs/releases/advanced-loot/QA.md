# Advanced-loot native acceptance

**Not executed.** Use a separate QA client, candidate world/zone, isolated database
and isolated quest directory. These commands create test loot; do not run this
recipe against production or the read-only `Client_RoF2_Dev` installation.
No promotion to `test` or `main` is recorded by this document.

The separate client and signed launcher are packaged under
`E:/EQ_Local_Dev/artifacts/advloot-20260930/qa/` (release 2026093005).
Installation and startup passed. The isolated login/world/ecommons services are
running, with hashes and fixture-only database state in [service evidence](gameplay-qa.json).
The QA client targets `127.0.0.1:15998`, but client access is deliberately inactive
until world port 9000 is freed and published for QA. The live local game-server
container currently owns that port. A temporary cutover requires owner approval
because it interrupts that server; it has not been performed.
The concrete [access and restore plan](QA-ACCESS.md) preserves the isolated
runtime and database and returns the live container to its prior running state.

Use fresh accounts `advloota` and `advlootb`; their generated credentials are in
the private local artifact directory, outside the package and Git. The isolated
quest directory is empty except canonical hand-in helpers, so production quest
acceptance requires separately staged fixtures. No production characters were copied.
See [package evidence](qa-package.json).

## Fixed fixtures

Read-only reference lookup on September 30, 2026:

| Fixture | ID | Observed definition |
|---|---:|---|
| East Commonlands | zone 22, `ecommons` | QA location |
| `a_decaying_skeleton` | NPC type 22003 | Level 1; persistent type for saved-state cases |
| Bone Chips | item 13073 | Tradeable, not lore, stack size 100 |
| Holy Dirt of Brell | item 1068 | NO TRADE, not lore |
| Worthless Coin | item 1041 | Tradeable, standard lore (`loregroup=-1`) |

Use two fresh QA characters, A and B. Record their character IDs, initial wallets
and inventory, candidate hashes, screenshots and logs. Give administrative command
access only on this isolated server. Turn the GM flag off for classic-loot rights
checks. Both characters should initially have Enabled, Apply Filters and Auto Show
on; Auto Loot All, Auto Split Coin and Show New Only off.

### Make one controlled corpse

In `ecommons`, spawn the fixture with `#npctypespawn 22003`. Target the new
skeleton, then run:

```text
#npcloot remove all
#npcloot money 5 2 3 7
#npcloot add 13073 5 0
#npcloot show
```

Confirm the target's complete contents before killing it. **Kill through normal
combat** so A receives native kill credit; `#kill` is unsuitable for this check.
The fixture purse is 5 platinum, 2 gold, 3 silver and 7 copper. Replace or extend
the item command with `#npcloot add 1068 1 0` or `#npcloot add 1041 1 0` for the
NO TRADE and lore cases. Never change the persisted NPC loot table.

## Solo window and filters

1. Kill one fixture within 25 units. The separate Advanced Loot window opens with
   Bone Chips, quantity 5, and the skeleton source. Coin enters A's wallet exactly
   once. `/advloot` closes and reopens the window without opening classic loot.
2. Inspect the item, use Find Corpse, then Loot. Exactly five chips enter inventory
   and the row disappears. Rapid repeated clicks must not add more chips.
3. Mark chips Always Take and kill another fixture. Chips collect without a loot
   click. Repeat with Always Need and Always Greed while solo. Reset to Ask.
4. Mark chips Never. Its personal offer disappears and remains on the corpse;
   another kill does not offer or collect chips. In Filters, search `Bone Chips`
   and change it to Ask. The filter record disappears and pending eligible chips
   can be offered again. A's choice must not change B's filter.
5. Camp and reconnect. Verify the saved filter and every setting. Disable Apply
   Filters temporarily, then restore it. Disable Enabled and verify automatic
   collection/show stops and classic looting remains usable.
6. With Ask, kill nine separately prepared fixtures before looting. Verify paging,
   search, selection and distinct physical drops of the same item ID. Loot All
   collects eligible items matching the current list/search, once each.
7. Leave an item. It disappears from the offer list while remaining on its corpse.
   Classic looting can collect it when native rights and effective filters allow.

## Restrictions and lifecycle

- Kill beyond 25 units: the owned row is visible, but pickup is disabled. Find the
  corpse and approach; pickup becomes available. Test a locked corpse and another
  player's open classic-loot session. Neither may be bypassed.
- Fill all inventory/bag slots, then try manual and automatic collection. The item
  remains on the corpse with no cursor overflow. Free space; retry using Loot or
  Refresh and verify exactly one award. Unchanged failed automatic attempts must
  not repeatedly execute loot scripts.
- Hold a cursor item with the native empty-cursor loot rule enabled. Loot must fail
  without replacing it. Test stunned, mezzed, feared, feigned, dead, trading and
  buyer/trader states. Ordinary combat/casting must not be interrupted by a window.
- Offer Holy Dirt of Brell. Automatic settings and Loot All must not accept it.
  Loot presents confirmation; cancel/selection change gives nothing. Confirm gives
  one item. Also test a NO TRADE augment/container fixture before release.
- Loot Worthless Coin once, then offer another. The second remains pending and no
  duplicate enters inventory. Also test lore augments and duplicate lore within a
  container before release.
- Zone, die, disconnect and reconnect with pending rows. Old-zone actions must not
  affect new corpses. Repeat `/loadskin`, close/reopen, decay and entity-ID reuse.
  Verify native layout, keyboard focus, edit text, button labels and no crashes.
- Consume an eligible row through classic looting. The advanced list updates and
  cannot award it again. A classic request must not steal a shared award.
- Disable advanced loot for both characters before making a new group corpse.
  Classic manual pickup must put the item on an empty cursor. Classic auto pickup
  must equip an eligible item in an empty worn slot, with native level/class,
  attunement, two-hand/offhand, instrument and dual-wield restrictions. Otherwise
  it uses inventory, then an empty cursor if bags are full. Repeat an evolving
  equipment item and confirm its equipped state survives relogging.
- With administrative access, verify classic `GMAllowed` recovery of a corpse
  belonging to B even when A has Never set for that item. Turn A's GM flag off and
  repeat: native rights must apply again. The advanced window must never expose
  this classic-only override. A malformed/quarantined checkpoint stays blocked.

## Two-player shared loot

1. Group A and B with A as leader and both eligible/in zone. Kill the fixture.
   Both see the shared offer and its master. Neither automatically takes it.
2. A targets B and assigns it. The row identifies B; only B can take it. B leaves
   an award; it returns to shared control. Assign a NO TRADE item and verify B's
   own confirmation is still required.
3. Start a roll. A chooses Greed and B Need. Wait 60 seconds: B wins. Repeat with
   both Need, both Greed, all Pass, Always Need/Greed and Never. Refreshing the list
   must preserve a manually selected vote. Never must exclude an award while
   leaving the master's shared view usable.
4. Open Free Grab and click from both clients. Exactly one character receives the
   item. Auto Loot All must not race to claim free-grab items.
5. Enable Auto Split Coin for A. With exactly these two clients in the group, one
   fixture gives A 3pp/1gp/2sp/4cp and B 2pp/1gp/1sp/3cp. Their combined increase is
   the original purse. Repeat without splitting, then in a raid. Bots/mercenaries
   consume no shares; verify current raid item-looter restrictions separately.
6. Disconnect the master and the selected winner at each stage; change group/raid
   membership and raid loot type. A connected participant who retains native
   rights becomes master; a new group leader outside the original roster cannot
   claim it. Votes/deadlines and existing awards survive the handoff. Returning
   old masters cannot seize control while the replacement remains eligible.

## Operator fault and saved-state gates

These require the isolated server, not just player observations. They remain
open until recorded against the real candidate process.

- Save a living fixture and a corpse with nontrivial charges, augment/custom data,
  rights and a running roll. Restart the zone. Compare the complete item metadata,
  remaining rights and distribution decisions before and after.
- Retain a checkpoint, award its item and coin, then replay that checkpoint.
  Receipts must suppress the awarded physical drops and purse. Also exercise a
  legacy checkpoint lacking UUIDs and malformed saved extensions.
- Inject inventory, currency and receipt failures and a lost commit acknowledgement.
  Confirm no pre-commit inventory publication, no duplicate award, and quarantine
  on uncertain outcomes. Do not delete receipts or manually grant replacements
  without reconciling the stored afterimage.
- Exercise quest loot vetoes and dynamic-zone restrictions. Verify native task,
  discovery, adventure and audit behavior after a successful transfer.
- Finish and rehearse a receipt-aware rollback. A previous binary must not load
  unreconciled checkpoints containing already awarded items.

Record each result as pass/fail with exact build hashes and evidence. Automated
dependency-fake fixtures and the SQL rehearsal do not close these native gates.
