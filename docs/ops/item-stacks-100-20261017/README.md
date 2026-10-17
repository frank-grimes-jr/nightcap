# Item stacks of at least 100 — October 17, 2026

Prepared and rehearsed; **not applied to production**. Main promotion, the
controlled game restart, wiki publication and owner gameplay acceptance remain
pending. Source base: `origin/main a59974d`. No C++ or client changes are needed.

## Behavior and scope

Raise `items.stacksize` to 100 only where `stackable=1 AND stacksize<100`.
Preserve existing limits of 100 or more, nonstackable definitions, charges,
prices, item stats and recipes. Already-owned copies receive the new limit when
the shared item cache is regenerated; existing stacks are not automatically
merged. This saves inventory slots but grants no items, stat power, recipe
success, skill points or cheaper per-unit purchases. Reusable nonstackable tools,
containers and equipment remain nonstackable.

The fresh OVH read-only audit found 20,490 affected definitions, including 6,734
marked as tradeskill materials. There are 9,283 definitions already at 100 and
670 above 100. Examples: Leather Padding 16488 is 50; Small Piece of Ore 10500,
Water Flask 13006 and Bandages 13009 are 20. All become 100. Arx Energy Crystal
18441 remains 1,000. These are database-wide definitions, not a promise that
every item is obtainable in the current era.

All three-column candidate preimages are retained privately in
`E:/EQ_Local_Dev/artifacts/item-stacks-100-20261017/before.tsv`, with generated
`prepared/forward.sql` and `prepared/plan.json`. The snapshot SHA-256 is
`1159f19f22ecc865c31c5fc2bed078381a345d0c47feb7b4e6f79b21b7e7e692`.
Re-capture immediately before activation and reject/review any difference.

## Source and verification

`tools/item_stack_sizes.py` reads a bounded TSV capture and generates one
transaction that checks the item table engine, absence of triggers, total
candidate count and each item's old stackability/limit. Only matching item
IDs have `stacksize` assigned. Drift or SQL failure rolls back. It rejects
repeat execution after success. It never connects to or applies to a database.

`server-mods/code/common/shareddb.cpp::LoadItems` loads StackSize directly.
`common/patches/rof2.cpp` serializes it for the existing client; inventory and
merchant paths use that loaded limit. Existing tradeskills count physical units
and preserve leftovers. No new rule, binary, ItemData ABI or signed asset pair.

Verification on October 17:

- Three local planner tests pass (validation, original limits, deterministic output).
- Nine actual MariaDB rehearsals pass in session-local temporary tables created
  from the production item schema. Full 20,490-candidate success, 1/20/75/100/200/
  max-int boundaries, nonstackables, missing/replaced/added/changed candidates,
  repeated application and an injected post-update failure are covered.
- Rehearsal afterimages explicitly compare ID, stackability, stack size, name,
  price and charges. This is not an all-column cache comparison. The actual
  schema's `information_schema.COLUMNS.EXTRA` query returned no automatic or
  generated fields; no item triggers exist. The only SQL assignment is stacksize.
- Existing native tradeskill fixtures pass: 18 experimental-combine and 7
  automatic-combine tests. They do not prove visible RoF2 interaction or durable
  inventory persistence. Independent review found no blocking defects.

The first rehearsal attempts found two test-harness issues (same-name schema
cloning and a nested-block delimiter); both were corrected before all nine
passed. No live item or runtime mutation occurred. See `rehearsal.json`.

## Activation after owner authorization

1. Use the current OVH production operator and deployment/GM locks; inspect the
   actual active image/supervisor. Close player access and gracefully stop game.
   Preserve other services and all existing native/client files. Do not kill a
   single zone: the supervisor restarts the entire runtime when a child exits.
2. Take and verify a fresh full stopped database backup. Capture item preimages,
   player/custom-table digests, native hashes and the current item cache. Compare
   candidate IDs and limits with the reviewed snapshot. The planner's output
   directory must be new; retain original evidence.
3. Run the reviewed `forward.sql` against `peq` without `--force`. Verify exactly
   the captured IDs now have limit 100, zero stackable definitions remain below
   100, and every other item column/player table is unchanged. An uncertain
   acknowledgement requires inspection, not automatic retry.
4. Start the same game image through its supported supervisor to regenerate
   shared items. Compare the complete cache: only affected StackSize fields may
   change. Retain current equipment race, trade/LORE, divine resale and dungeon
   definitions. Verify all processes/health and errors before reopening access.
5. Record the actual deployment, then replace candidate wiki notices together
   and verify an authorized public release. No launcher download is required.

Recovery: retain the higher limits if access has opened or is uncertain. Do not
lower limits underneath stacks now owned by players or restore old player data.
Before any access, a separately reviewed inverse may restore only the captured
old limits after exact afterimage checks, followed by cache regeneration. This
change supplies no automatic down migration. Transaction failure rollback was
rehearsed; full production startup/cache and post-commit recovery are still pending.

## Exact owner QA after activation

1. At Haldra, Smithing Supplies III, East Commonlands `/loc -1768,-395,4`,
   close/reopen the shop and purchase Leather Padding. Combine two stacks of 50
   into 100. A 101st unit must occupy a second stack. Check actual coin charged.
2. Buy Small Piece of Ore or Water Flasks from the tunnel crafting suppliers.
   Merge five existing stacks of 20 into 100; split off 1 and 20, then recombine.
   Count all units before and after; prices per unit must remain unchanged.
3. Use a known eligible recipe at its matching tunnel station and in a carried
   tradeskill container. Experiment must consume only required units and retain
   leftovers. Craft One/Craft All/Stop must preserve normal results and failures.
4. Bank and withdraw a 100-stack at Mira Coinwell; zone and relog. Check inventory,
   bank and material counts persist. Trade a stack to another character if possible.
5. Confirm a previously larger stack keeps its limit, and a charged nonstackable
   tool/equipment item still cannot merge. Check full-inventory result handling.

## Wiki review

See `wiki-review.md` and the exact staged patch. All maintained guides and the
generated hunt catalog were assessed; candidate notices belong in tradeskills,
Features, home, In development and Recent changes. No recipe, command, reward,
zone-stat or generated hunt-equipment value changed. Local changes are not public.
