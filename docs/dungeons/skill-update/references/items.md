# Items, loot, forging and economy

Item-policy audit refreshed 2026-10-13 for the deployed divine-summon exception; other item systems retain their October 12 audit scope. Keep the independent reward systems distinct; use their explicit catalogs and current source. A stale runbook still saying every zoneforge recipe costs three is superseded by the October 12 upgrade policy.

| System | Implemented contract | Source/evidence |
|---|---|---|
| Legacy quality loot | Base / Polished / Exalted / **Ascended**, offsets +200k/+400k/+600k; epics +800k. Historical defaults 10%/2%/0.25% per eligible item drop, not per kill. Verify active rules before tuning. | `akk-stack/code/zone/loottables.cpp` in full source; tracked `server-mods/code/zone/loot.cpp` is not automatically the legacy hook; old SQL generators need reproducibility review |
| Classic hunt | Two independent 0.5% rolls per eligible death: augment and wearable; weights 60/30/8/2, top tier **Ascension**. 48 audited combat zones enabled, eight access-check zones gated. | `server-mods/code/zone/zone_hunt.cpp`, `common/zone_hunt_catalog.h`, `common/zone_hunt_policy.h`; `docs/releases/zone-loot-20261009/PRODUCTION.md` |
| Zoneforge | Baseâ†’Polished costs 3; Polishedâ†’Exalted and Exaltedâ†’Ascension cost **4** after Oct 12. No cross-family conversion. | `zone/zone_hunt_forge.cpp`, `common/item_upgrade_policy.h` (`ZoneCopies`) |
| Reforging Box | Four identical Polishedâ†’Exalted or Exaltedâ†’top tier for either family. Free reusable four-slot box 900620, Artisan Veyra NPC 999820 in EC tunnel. No Base/top-tier recipe. | `common/item_upgrade_policy.h`, `zone/advanced_loot_inventory.cpp`, `quests/ecommons/999820.pl`; `docs/releases/item-upgrades-20261012/README.md` |

Item links must remain <=1,048,575. Prove IDs free across relevant tables and references, not just `items`; use guarded migrations. New hunt IDs start at 940000 and bypass legacy tier upgrading/global multipliers. Exact audited spawn/NPC identity, zone/version, level and special gates govern hunt eligibility. Pets, owned/script-created victims, services and restored dead NPCs don't reroll.

Hunt type-22 augments fit eligible head/arms/hands/chest/legs/feet sockets. At player level >=50 only qualifying socketed hunt-augment heroic INT/WIS adds output-cap headroom: `min(30,floor(effective heroic total/2))` for Spell Damage/Healing Amount. It doesn't grant missing raw bonuses. Don't apply this credit to arbitrary gear, AAs, buffs, NPCs or other augments.

## Dungeon reward catalog candidate

October 16 candidate only; `docs/dungeons/{catalog.json,README.md,QA.md}` owns
definitions and acceptance. IDs 960000–960329 remain below the RoF2 link ceiling.
Twenty-four shared designs (8 armor, 8 weapons, 6 accessories, 2 bags) use bands
20/30/40/50 and Normal/Polished/Ascended qualities: 288 definitions. Each dungeon
also has exactly three exclusive Raid designs in two qualities: 42 definitions.
Explicit budgets/defaults and cache-field checks prevent hidden stat drift.
Weapon delay is stable; bags use 6/8/10 slots, up to 100% weight reduction.

Grind completion grants Normal. Raid personal/exclusive qualities are 90%
Polished/10% Ascended; exclusive corpse count is 1/2/3 at 80/18/2%, without design
duplicates. Shared designs are uniform without class filtering. Run seed,
per-character reward ID and physical-drop UUID are durable; reconnect cannot
reroll. Completion grants once per character/run through the existing atomic
inventory/receipt transfer. Full inventories leave Keeper claims after expiry/reset.
All definitions are permanent, tradeable, non-attunable, non-lore and zero resale.
Existing legacy/zoneforge conversions exclude this range; do not treat dungeon
qualities as offsets or hunt Ascension. Native loot remains additional.

Source: `common/dungeon_{policy,catalog,contract}.h`, `zone/dungeon_service.cpp`,
`common/shareddb.cpp`, `tools/dungeon_{catalog,migration,contract}.py` and guarded
20261016 dungeon SQL. Tests: `tools/tests/test_dungeon*.py`, rehearsal/activation/
concurrency scripts, existing inventory/corpse adapter evidence and native cache
verification. Pair all native binaries with the cache; no client asset changes.
Local automated verification is not gameplay/balance acceptance or deployment.

## Commonlands Leather Padding stock

October 16 owner-requested content deployed on OVH: Haldra / Smithing Supplies
III (NPC/merchant 999603) sells Leather Padding 16488 in permanent slot 19 at
EC `/loc -1768,-395,3.75`. Berrin and Torvik already have 150 slots each. Owner
approved `items.sellrate` 2→3; base price 400, resale and recipes are unchanged.
Current merchant rules otherwise permit buy/resell profit at multiplier 2.
Purchase multiplier 3 keeps the best charisma-adjusted purchase above resale.
Changing this shared item metadata required regeneration through the current
supervisor's controlled game restart; stock-only edits support `#reload merchants`.
No binary or client update. All 309,410 cached definitions were compared; only
item 16488's SellRate float changed. Exact forward/inverse and three drift rejection
rehearsals pass. Production is deployed; owner purchase/crafting QA remains pending.
Source/operator, QA and deployment/cache evidence:
`E:/EQ_Local_Dev/docs/ops/commonlands-services-20261016/`. Preserve this additive
stock when regenerating an older full tunnel merchant catalog.

## Equipment race policy

The owner confirmed javelins work with signed client 2026101501, then Bronze
Knuckles exposed a separate Half Elf race exclusion. Its base 30981 and quality
variants have Monk/Beastlord classes 16448, original races 62219, primary-only
slots 8192 and no deity/required-level gate. The owner chose class match for any
playable race, while keeping non-player definitions unavailable.

`common/equipment_race_policy.h::ApplyRacePolicy`, called after restrictions in
`common/shareddb.cpp::LoadItems`, projects effective Races=65535 only for common
items with playable class/race bits and a worn slot 0..22 or nonzero AugType.
Preserve zero AND unsupported-only masks such as 65536. Raw SQL is unchanged.
Class, deity, level, slots, weapon conflicts, augment fit, trade/LORE/resale and
every other field remain. Bots/other effective-item consumers share this policy.

PR #204 merged policy 5cea9cb and guarded operator 11e1add as fd5e6e0. The owner
explicitly authorized push/merge/deploy with restart on October 16. Production
image 581322f0… / loader 71dfdd18… is deployed, with access open. The full 309,410-item
cache changes 90,852 race fields and preserves 1,535 non-player definitions and
every other byte. Closed-access checks preserve 47 player/11 custom tables,
content/rules/quests, supporting services and all 106 signed assets. All 12 zones
retain the AA-duration hash 19cd3387…, with zero candidate restarts/detected errors.
A fresh complete backup passed gzip checks; no SQL migration or restoration.

Read `docs/releases/equipment-race-policy-20261016/README.md`, deployment.json,
deployment/manifest.json, build-manifest.json, cache-rehearsal.json and
verification.json in `C:/Users/verre/Documents/Codex/2026-10-15/g/work/multiclass-equipment`.
Source tests: `tools/tests/test_equipment_race_policy.py` compiles actual loader
and both SwapItem directions; `eq-client-dll/tests/equipment-native.cpp` executes
78 checks with actual race/equip/inspection paths. Other client restriction and
object-storage helpers are fixtures; server tests cover deity/level separately.
The retained archive/link inputs reproduce the prior loader 139194a9… before
one-object replacement; 126 members remain identical, ItemData stays 1332 bytes.
Local 308,928-item old/new/old rehearsal preserves all other cache bytes and
recreates the original cache. All 37 operator recovery/pairing tests pass on
Windows and the production host. Independent review has no remaining blockers;
the provenance finding was resolved, and the optional second model was declined.

Pair with existing signed client 2026101501/proxy0.9.1-dev; no new download.
Future loader/cache updates require the supported whole-game restart and fresh
approval. Keep the latest world/zone/login/UCS binaries. Before possible access,
recovery regenerates the old image cache and requires exact preflight equality;
otherwise hold gateway closed. Never restore stale SQL/cache over changed data.
After uncertain access, retain candidate/subsequent activity and reconcile.
Bronze Knuckles remains primary-only. Owner inspection/equip/relog/class-release
QA is still pending; rollout health does not establish visible gameplay acceptance.

## Ordinary tradeskills: stacked materials and Craft All

Owner-authorized PR #200 merged to main and deployed to OVH October 13 for live QA, paired with signed game release 2026101304/proxy 0.9.0-dev. Owner gameplay acceptance remains pending. Experimental combines count physical stack units, consume exact recipe requirements and retain leftovers in bags/world stations. Charged nonstackables count as one. Prefer a unique exact quantity recipe, otherwise require one feasible recipe; ambiguous/missing/unrelated/augmented inputs consume nothing. Reacquire containers and rebuild plans after both quest callbacks. Native generic world containers have null parent ItemData and GetID()==0; only portable bags require parent ItemData.

Recipe-browser automatic combines validate the real carried bag or owned nearby station, character/skill/class/race/quest gates and empty cursor. They gather a complete fresh ingredient plan from carried slots/bags before consumption, aggregate duplicate rows and retain native success/failure/salvage/skill gains. Container-consuming recipes require exact Experiment inputs. Reforging Box, molds and augmentation keep separate paths. Ordinary persistence remains native; this is not a new atomic receipt contract.

Source: server-mods/code/zone/tradeskills.cpp and common/tradeskill_policy.h. Tests: tools/tests/test_tradeskill_stacks.py and test_tradeskill_auto.py extract production functions; 25 groups/74 scenarios pass. SQLite executes emitted SQL; result generation and by-ID metadata boundaries are mocked. Retained full native source matches original tradeskills SHA 53cd12b0e8c4e677cfaac87108634086e6c7b53ed1f869c5820c121dde286c8f. Isolated zone build/link passes using tools/build_tradeskill_candidate.py. No DB migration, rule or ItemData layout change. Pair the rebuilt zone with proxy 0.9.0-dev/config/catalog/tradeskill XML; use supported whole-runtime refresh, not quest/rule reload. Preserve the current divine-summon loader/cache. All 12 zones and 106 hosted signed assets verify with zero candidate restarts/detected errors; closed-access checks preserved 47 player/11 custom tables, current policies/content/quests and other binaries. Fresh full backup passed gzip/completeness verification (no separate restore rehearsal). Native visual, real packet timing, stack persistence and owner QA remain pending in docs/tradeskills/README.md; deployment.json, deployment-manifest.json, hosted-verification.json, build-manifest.json and verification.json record evidence. Never restore old player inventory on rollback.

## Transaction and recovery boundary

Forge and box inputs, output and durable receipt commit together after exact inventory preimage checks. Binding is preserved. Reject socketed/dyed/ornamented/evolving/customized instances; bags cannot nest in the box. Stack quantity is physical copies; a charged result still yields one unit. `nightcap_item_upgrade_state` revision 2026101201 gates box behavior; `nightcap_item_upgrades` and `nightcap_zone_hunt_forges` retain receipts. Missing/mismatched enablement rejects. Uncertain commit or packet publication quarantines the session; don't automatically retry consumption.

Disable acquisition/combining for operational rollback while preserving definitions, sockets, earned items and receipts. Never restore old inventory after player activity or roll back below receipt-capable binaries. The box NPC supplies the container; it is not a four-item hand-in quest.

## Divine summoned weapons

PR #197 merged to main and deployed on OVH October 13. Existing `SpellEffect::SummonItem` and `SummonItemIntoBag` already select Ascended (+600000) for eligible base equipment when the variant exists. Paladin/Cleric hammer spells retain that behavior; Unswerving/Celestial Hammer pets are separate.

`common/divine_summoned_weapon_policy.h` covers eleven hammer families at all four quality offsets: bases 6307, 6309, 6313, 5800, 15996, 5798, 29365, 77517, 90491, 90492, 90493. The loader calls `ApplyMerchantPolicy` **after** FreeTrade and zeros both Price and FixedSellPrice for all 44 definitions. This closes unlimited summon-to-platinum sales, including old inventory copies. Combat stats, procs, bane, equip/class/level gates, raw SQL, effective trade flags and temporary lifetime remain unchanged. `#sellall` skips and retains them; an explicit ordinary merchant sale packet may discard one for zero coin.

Wrath/Striking/Requital summon 606307/606309/606313: damage/delay 8/32, 8/29, 9/29; undead bane 3/4/5; each has +20 Spell Damage/+20 Healing Amount and remains primary-only. Ascended has no box/zone-forge successor; no production recipe references any of the 44 definitions, and the Epic Forgemaster uses its separate explicit catalog. Later hammer spell and item-level gates stay intact.

Only `shared_memory` was rebuilt from retained production-matching source/link inputs; ItemData remains 1,332 bytes. The active world's/zone's/login's/UCS's binaries, including the October 13 AA-rank repair, were preserved. Cache regeneration requires the supported full-game restart; rule/quest reload alone is insufficient. No SQL migration or client download. Do not deploy an older main-checkout zone over the newer active binary. Exact image and native hashes: `docs/releases/divine-summons-20261013/deployment-manifest.json` and `deployment.json`.

Native summon/resale and adjacent policy tests plus cache/operator recovery tests pass; independent review has no remaining blockers. Old/new/old loader rehearsal over 308,928 local definitions reproduces the original cache exactly. Production compared 309,410 definitions and preserved every cache byte outside the 88 owned price fields, 47 player tables, 11 custom tables and runtime/public fingerprints. All twelve zones are healthy, gateway reopened, zero new restarts/detected errors. Owner encounter balance and visual QA remain **pending**: `docs/releases/divine-summons-20261013/README.md`. Source tests: `tools/tests/test_divine_summoned_weapons.py`; release folder contains the cache checker, guarded operator and recovery tests.

## Trading, LORE and sales

- `Items:FreeTrade` projects effective flags and fixed former-NO-DROP resale from raw SQL definitions. `IsAttuned()` is persisted state; `IsAttunedForTrade()` handles permission. All native binaries and regenerated ItemData cache must match. Raw SQL `nodrop=0` doesn't establish effective restrictions.
- Originally NO DROP objects pay **1pp per physical unit**, not per charge, through ordinary merchants and `#sellall`; normal pricing otherwise remains. New hunt rewards and all 44 divine summoned-weapon definitions have zero resale. Preserve bags themselves. Native merchant previews can differ from the server's actual payout. `common/item_trade_policy.h`, `docs/releases/free-trade-20261004/README.md`.
- **LORE disabled on OVH October 12** with `Items:DisableLore=true`: loader clears effective LoreFlag/LoreGroup, preserving SQL originals. Rebuild cache/restart; rule reload alone is insufficient. Re-enabling after duplicates exist can delete cursor conflicts; reconcile ownership first. `docs/releases/remove-item-lore-20261012/README.md`.
- Latest source `gm_commands/sell_all.cpp::IsSellAllSupply` protects food/drink and every loaded spell `component[]` or item-valued `no_expend_reagent[]` across classes/eras, in general slots and bags, even for fixed-resale items. It reads current spells each check; absent spell data blocks sales. The merchant button invokes this same command and adds no sale policy. PR #183 merged; the runbook added a **verified October 12 deployment** during this audit, retaining all other rules/content and reopening the gateway. Manual acceptance remains pending. Recheck `docs/ops/sellall-supplies-20261012/README.md` for later changes.
- Food/drink requirements were removed in the October 11 native release; optional item bonuses, recipes and alcohol remain. This doesn't make those items disposable.

## Tests and historical traps

Focused tests under `tools/tests/`: `test_item_upgrade_policy.py`, `test_item_upgrade_package.py`, `test_advanced_loot_inventory.py`, `test_zone_hunt.py`, `test_zone_hunt_native.py`, `test_free_trade.py`, `test_remove_item_lore.py`, `test_sell_all.py`, `test_food_drink.py`. Disposable DB rehearsals are separate and require their documented environment. Client Combine/visual and progression-balance acceptance remains distinct.

Older item generators omitted later flat SpellDmg/HealAmt additions; do not regenerate live tiers from the old script without a full comparison. The September combat/item repair report is a candidate, not proof every proposed stat change deployed. The finite living economy has a separate catalog, offer lifecycle and receipts; do not overwrite it with generic merchant restock. Route it through `docs/economy/` and current status before changes.
