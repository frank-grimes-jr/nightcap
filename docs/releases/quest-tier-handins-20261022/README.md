# Quest item qualities — October 22 candidate

Normal-item quest requirements now accept the verified Polished (+200000),
Exalted (+400000), and Ascended (+600000) definition of that same item. The
reported regression is Shakrn Meadowgreen (14075), South Karana: Aviak Charm
213737 plus two Star Rubies 10032 must award Crafted Gauntlets 4178 and 25,000
ordinary quest EXP. The reward does not inherit the ingredient's quality.

This is an implemented, tested candidate, **not deployed or player accepted**.
Production's twelve zone executables were read on October 22 and all matched
`5dd5a6558c837ff2e4724edcd12afcabd2e846379a9ca7b8a6e57e7715600f7b`.
The build authenticates and reproduces that baseline before replacing the two
implementation objects; `native-build-manifest.json` records the result.

## Coverage and contract

- The shared Lua `lua_modules/items.lua` helper covers Shakrn and 1,033 deployed
  quest files using that helper/native API. Perl's `check_handin`, `givenItems`,
  and `takeItems` already delegate to `NPC::CheckHandin`; 1,337 deployed quest
  files call those APIs. Counts are source references, not a claim of 2,370
  individually accepted gameplay tests.
- Native task **Deliver** objectives use the same item-family policy while
  retaining exact NPC, zone, area, activity-state and quantity checks. Loot,
  tradeskill and other objective types retain their existing behavior.
- Five older Temple of Solusek Ro scripts bypassed the native checker for
  ingredients that have quality variants: Gardern, Joyce, Sultin, Vilissia and
  Vurgo. Their 17 recipes now use `plugin::check_handin`; rewards/factions/EXP
  remain. Vurgo's manual resummoning is removed so native returns preserve
  actual instances, charges and binding.
- IDs **and** exact generated names must match. An explicitly tiered requirement
  remains exact. Epic +800000, hunt and dungeon catalogs stay separate; this
  does not alter reforging recipes, quality costs, reward tiers or item stats.
- Exact items are preferred over better qualities. Explicit quality requirements
  reserve their inputs first. Mixed ordinary qualities can meet a Normal count;
  one instance cannot meet two requirements. Failed ingredient/money/unknown-ID
  checks restore tentative native counts. Normal hand-in returns preserve
  instances. Retained partial multiquest items keep real IDs. The existing
  multiquest completion rule still clears its entire donation bucket, including
  surplus: this fix does not make extra multiquest donations refundable. Lua's
  existing one-item-per-trade-slot convention is unchanged.

`production-audit.json` is a dated, read-only capture: shared helpers, the exact
Shakrn quest, 33 potential bypass scripts and joined item definitions. Twenty
Normal ingredient families in the five scripts have variants. Other literal
bypasses request items without variants. The five Riwwi loops are food/drink
turn-ins; generation requires equipment slots/stats or a bag. Tipt's riddle
counts use ground-spawned riddle tokens. These are not equipment-tier paths.
No Polished-family base names longer than 52 bytes were found in the bounded
name-length query. Future content additions must rerun this audit rather than
assume every hand-written quest delegates to a shared checker.

## Verification

The exact compiled `NPC::CheckHandin` method and `ClientTaskState::CanUpdate`
filter are exercised by `tools/tests/test_quest_handins.py`. Lua executes the
captured, unchanged Shakrn quest against the actual shared helper. Perl exercises
all 17 migrated recipes at four input qualities, extras, repeats and omissions
(221 assertions). Original native/Lua regressions failed on Polished; original
Perl scripts failed 68/221 assertions. See `verification.json` for final commands
and exit statuses. Native build and automated tests do not establish player QA.

Author and fresh independent review cover correctness, item preservation,
explicit-tier boundaries, API availability, source provenance, cost (four trade
slots), and wiki impact. Review found one dialogue encoding regression in the
copied Vilissia script; its three legacy separators now use ASCII hyphens.
The inherited multiquest surplus rule is explicitly retained. Complete task
delivery/event/inventory lifecycle remains player QA beyond the compiled filter
test. Review is not human approval. Exact player checks: [QA.md](QA.md).
Decision: [ADR 0066](../../adr/0066-tiered-quest-ingredients.md).

## Activation and recovery

Promotion through dev/test is authorized by the workspace agreement. Main and
production activation require current owner sign-off. Before an authorized
activation, compare fresh running hashes, source manifests and all six quest-file
preimages against this capture; retain any intervening release. Take a fresh
backup and use the supported whole-runtime release procedure. Deploy the rebuilt
zone, `quests/lua_modules/items.lua`, and five `quests/soltemple/*.pl` files as one
release. Lua's module cache needs a verified reload/restart; a quest-only reload
cannot install native changes. Do not kill a single production zone process.

No SQL, world, rule catalog, shared ItemData/cache, launcher or client change is
required. Preserve the current client/world/cache pair. Retain fresh predecessor
zone and quest files for recovery, restart through the supervisor, and verify
hashes. Never restore player inventories, quest/task history or earned rewards
from an old snapshot. Publish the prepared wiki notices only with the authorized
release, switching their candidate labels after verified activation.
