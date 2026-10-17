# Commonlands leather padding and banker — October 16, 2026

The owner requested Leather Padding on a Commonlands smithing merchant, then a
banker in the same hub. The owner separately approved changing Leather Padding's
purchase multiplier from 2 to 3 to prevent a merchant buy/resell profit loop.

**Deployed October 16 at 06:09 EDT (10:09 UTC).** Exact SQL afterimages, unchanged
native binaries, the full item-cache comparison and healthy runtime passed.
Owner gameplay acceptance remains pending. [Deployment evidence](deployment.json).

## Content

- Haldra, **Smithing Supplies III**, NPC/merchant 999603: permanent slot 19 stocks
  existing Leather Padding item 16488. Berrin and Torvik already have 150 entries
  each. Haldra's original 18 entries are preserved. Location in EQ `/loc` Y,X,Z:
  **-1768, -395, 3.75** in East Commonlands (`ecommons`, zone 22, version 0).
- `items.sellrate` for 16488 changes 2 → 3; `price=400` and every other item field
  remain unchanged. This is item-wide purchase metadata, including old copies;
  crafting recipes, resale value and merchant rules remain unchanged. With the
  inspected 1.05 sell modifier and maximum 4% charisma discount, buying costs
  approximately 1.21 platinum or more, versus at most 1.04 platinum resale with
  the 2.5 buy modifier. Actual client quotes and coin deductions require QA.
- **Mira Coinwell**, subtitle **Banker**, NPC/spawn/group 999821, at
  **/loc -1584, -144, 3.75**, beside the bag/buff service area. Neutral human woman,
  native banker class 40, heading 128, permanent stationary 100% spawn. Uses the
  current Tessa service template, with merchant ID cleared and no quest, loot,
  faction or spell assignment. Banking uses native server behavior.

## Verification and operation

`operator.py` captures exact current rows, rejects occupied IDs and changed
preimages, and generates serializable forward/inverse SQL. Rehearsal uses
session-local tables that shadow every target table. Exact forward and inverse
afterimages pass. Changed item metadata, an occupied merchant slot and changed
NPC donor each correctly reject. The initial preflight caught an obstructed
approach, corrected by facing the banker east. It also exposed two rehearsal
SQL assembly issues, corrected before any runtime stop or live write.

Ten native map ground/headroom samples and one unobstructed approach ray pass.
Current production NPC/object/door and patrol coordinates were checked for
spacing and approach clearance. Visual acceptance remains separate.

Activation uses deployment and GM locks, closes the gateway, gracefully stops
the existing game container, verifies a compressed full stopped backup, and
applies only the six content-table scopes. The existing startup supervisor
regenerates shared item data and starts the same world/zone/loader binaries.
No client download, quest change, or native rebuild is required. This operation
does not promote a Git branch or imply acceptance of other pending releases.

No saved spawn state is deleted. `Zone::LoadZoneState` explicitly adds newly
created `spawn2` records missing from saved state. Do not use broad `#repop`,
delete unrelated state, or kill one production zone to refresh these additions.
The saved-state behavior was checked in
`akk-stack/code/zone/zone_save_state.cpp::Zone::LoadZoneState`.

Before reopening access, exact content afterimages, native binary hashes and
the complete item cache are checked. Only Leather Padding's cached SellRate
float may change; all other cache bytes must match. Inventory, character,
currency, multiclass and zone-state checksums must be identical across the
stopped SQL operation. Full backup gzip/integrity is checked; a separate full
backup restore was not rehearsed. Forward/inverse content rehearsal is distinct.

Private preimages, generated SQL, full backup and operation receipts are under
`/opt/nightcap/backups/commonlands-services-20261016/`. Local capture and terrain
evidence are in `E:/EQ_Local_Dev/artifacts/commonlands-services-20261016/`.
The operator is one-shot; do not rerun activation after its marker exists.

## Rollback and in-game QA

If needed, take a fresh backup and maintenance locks, stop gateway/game, compare
the current content to the captured afterimages, then use the generated
`rollback.sql`. It removes only the four newly added permanent banker records
and Haldra's slot 19, restoring Leather Padding's old multiplier. After the
banker has run, also inspect and remove **only** her non-corpse, non-metadata,
zone-22 instance-zero saved state matched by exact NPC/spawn/group identity.
Preserve all other states and subsequent player/bank activity. Regenerate item
data through the existing controlled startup. Never restore the old full backup
over player activity. Uncertain verification keeps the gateway closed.

1. In East Commonlands, visit Haldra at `/loc -1768,-395,4`. Close/reopen the shop,
   find Leather Padding, and buy one and a stack. Verify quote versus coin
   deduction, quantity, retained old stock and ordinary smithing use.
2. Sell a purchased padding: the payout must be less than its purchase cost.
3. Visit Mira Coinwell at `/loc -1584,-144,4`, near Bartholomew and the buffers.
   Check model, name, clear access and one banker. Right-click to open banking;
   deposit and withdraw a small amount of coin and an ordinary item.
4. Zone/relog and confirm bank persistence, permanent merchant stock, and no
   duplicate banker. Report owner acceptance separately from server verification.

Deployment receipt and final health evidence are recorded in `deployment.json`.
Owner in-game purchase/banking QA remains pending.
