# Items, loot, forging and economy

## Unique Classic dungeon relics — October22 live testing

Owner-authorized main PR293 and paired live deployment are verified. Source
0d61d9b47322 in E:/EQ_Local_Dev/_worktrees/classic-dungeon-options. Exact receipts:
docs/dungeons/classic-rewards-20261022/deployment/. Zone8c9b97d5 preserves the latest
quest-tier matcher after byte-reproducing live6da991b6; world49f87aaf and loader
6b314bf0 are paired with the414-MAGIC cache and12 quest/module files. Signed
game2026102204 remains unchanged. All12 workers,39 schema/497 content checks,
414 cache definitions/888 rejection cases and full-cache preservation pass.
Fresh stopped backup and exact player/custom-state preservation are recorded;
only precisely authenticated native seven-day non-corpse cache expiry is allowed.
Gateway is open. Owner gameplay and solo/multiclass balance acceptance remain open.

0d61d9b47322 in E:/EQ_Local_Dev/_worktrees/classic-dungeon-options appends42 authored
designs/84 Polished-Ascended variants at960330–960413. Every21 dungeon final owns
three designs, retaining80/18/2 quantity and90/10 quality rolls. Shared completion
pool and Grind remain. All414 dungeon definitions are MAGIC:220 existing flag
updates only. legacy_items() and existing_items() preserve frozen330 preimages.
Current items() applies MAGIC afterward and appends the new level-band templates.

New numeric power equals existing slot/band/quality ceilings; only stat pairs and
resist distribution change. Recommended level follows20/30/40/50 band; planes
require46. All remain tradeable, permanent, non-LORE, zero resale and unforgeable.
Authored inspect lore is narrative, not LORE ownership. No new heroics, haste,
regen, focus/proc multipliers or new spell/client assets are introduced.

Fear Visage of Unbroken Will uses SeeInvisible80; Hate Maestro's Unfinished
Requiem uses Invisibility42; Sky Astrolabe of the Eighth Island uses Levitate261.
EquipClick4/level46/unlimited charges, base10s casts and300/600/900s reuse. Groups
91/92/93 share both qualities/copies, native timers191/192/193 plus persisted
character_item_recast timestamps. Existing focus reductions apply. Levitate uses
Bat Wing13068 subject to native conservation and remains forbidden inside Sky;
it never replaces keys. Full click fields and inspect lore are cache-guarded.

Guarded SQL checks complete330 public preimages, utility spells, all new-ID refs
including dungeon members/loot and serialized checkpoints/corpses, item cooldown
groups, native timers and character_item_recast. Repeated or partial writes fail
closed. Rebuild common/shareddb and service consumers; pair world/zone/loader/cache.
Retain definitions/earned receipts on disable. No destructive live bootstrap.
Source/tests/evidence: tools/classic_dungeon_rewards.py, classic_reward_migration.py,
tests/test_classic_dungeon_rewards.py, rehearse_classic_rewards.py and
rehearse_classic_reward_cache.py; docs/dungeons/classic-rewards-20261022/.
39schema/497content predicates and414 actual cache rows/888 negative cases pass.
Independent review is complete; gameplay and balance acceptance remain open; live deployment is verified.


## Quest ingredient qualities — October22 deployed for live QA

Owner-authorized main PR290/c66df0e and the paired zone/seven-quest deployment
are verified in docs/releases/quest-tier-handins-20261022/deployment/. Source: E:/EQ_Local_Dev/_worktrees/quest-tier-handins.
Normal requirements accept exact generated Polished/Exalted/Ascended family
definitions (+200000/+400000/+600000) in shared Lua/native hand-ins and task
Deliver. Explicit tier requirements stay exact; epic/hunt/dungeon identities and
forging costs remain separate. Exact inputs are preferred; explicit qualities
reserve first. Failure restores tentative counts and actual item instances.
Inherited multiquest completion still clears the whole donation bucket, including
surplus; Lua retains separate trade-slot semantics.

Shakrn14075 in southkarana accepts Aviak Charm13737/213737/413737/613737 plus two
Star Rubies10032, granting the already-live Ascended Crafted Gauntlets604178.
Five soltemple scripts now share native matching for17 recipes. Kurron retains
three Darkforge pieces/raw900pp, faction and one letter/spawn; all64 ordinary
quality combinations pass. Declare submitted currency to CheckHandin, refund
once on success, use native returns on failure. Active root plugins/ differs
from unused captured quests/plugins/ fixtures; do not conflate their evidence.

Zone6da991b6 is the successor to byte-reproduced5dd5a655. Full supervised restart,
fresh stopped backup, all12 zone hashes and exact player/custom/content/cache/
client preservation verified before access reopened. Seven files only; the ten
already-live armor reward scripts remain unchanged. No SQL migration, world,
cache ABI or client update. Never kill one zone or restore player snapshots.
Windows/Linux native method tests, actual Lua callbacks,357 Perl assertions,
113 armor Lua cases,21 catalog guards and16 deployment fault tests pass.
Owner gameplay acceptance and complete task-delivery lifecycle QA remain open;
exact source/tests/build/rollback boundary and QA: docs/releases/quest-tier-handins-20261022/.

## THJ custom behavior and stock gear — October 19, deployed for live testing

Owner-authorized main promotion PR256/7104c6b and OVH activation are verified in
docs/releases/thj-behaviors-20261019/deployment/. Stage:
/opt/nightcap/releases/thj-behaviors-live-20261019. Matching world/zone/cache loader,
three guarded SQL components and regenerated target caches are installed. Signed
game2026101902 retains proxy0.11.0, its matching catalog and all136 unrelated assets;
all138 hosted files verify with shipped trust. Classic50 and209 starter families
remain. Owner gameplay and balance acceptance remain pending; ../QA.md owns tests.

tools/thj_stock_scaling.py uses pinned stock ProjectEQ2026-10-17 (not Daybreak
or THJ DB). All131 Normal observations match stock. Exact measured targets win;
ordinary top core stats2x, haste1.5x, SD=max(2INT,WIS), HA=2WIS, Accuracy=ceil(DEX/2),
new heroics=rounded finalstat/4 at Ascended only. Positive native SD/HA/Accuracy/
heroics and sparse utilities/Attack remain stock absent exact evidence. Intermediate
qualities interpolate1/3 and2/3.47809 families/143332definitions change;3563 overflow
families are excluded under actual ItemData bounds. Normal/starters/custom Hunt/
dungeon/augments/bags/quest epics retain treatment. Full285-column preimages guard
numeric SQL and inverse; bounded hash/value staging requires complete matching IDs; pet/WPM effects/sockets/ownership remain. Fresh setup
requires generating the ignored thj-stock-bootstrap.sql companion before SOURCE;
compressed artifact and SHA are retained. Legacy SD/HA planning protects this stock
projection. Do not rerun destructive bootstrap live.

## Combined THJ item/spell and pet/WPM deployed — October 18, 2026

Source: C:/Users/verre/.codex/worktrees/thj-item-spell-parity/EQ_Local_Dev. Owner-authorized main/OVH deployment is verified in
`docs/releases/thj-parity-20261018/deployment/README.md` and `receipts/`. PR235 promotes the tested source;
signed client2026101802/proxy0.11.0 and wiki20261018-thj-parity-v1 are published
and verified. Classic50 remains active; level65/PoP and389 stock additions stay
staged. Owner gameplay and balance acceptance remain open. Exact testing:
`docs/releases/thj-parity-20261018/QA.md`; measured limitations: `COMPARISON.md`.

The exact reviewed catalog contains131 observed Ascended targets. Clean
Blood Cord/Talisman screenshots override conflicting workbook attributes;
ambiguous relocations, below-Normal fields, augmented/ambiguous identities and
unknown proc presentation are deferred. Unobserved ordinary families retain
existing policy. Normal ordinary gear stays native; intermediate values only
cap at reviewed top reductions. No universal THJ multiplier is inferred.

The209-family starter policy preserves modest quality steps below comparable
Normal dungeon gear, fixed weapon delay and cultural armor exclusion. The historical October18 catalog had330 definitions. Deployed
dungeon_catalog.items() emits414 MAGIC definitions; existing_items() retains the
retuned330 and legacy_items() the dated pre-retune migration preimage. item_scaling_overrides.py owns the final fresh
bootstrap block and requires exact present identities. The generic two-column
SD/HA planner excludes these families; never rerun destructive bootstrap live.

thj_combined_content.py composes1393 existing-item changes from full285-column
captures in one transaction. It accepts only full original, companion or final
images; drift or failed final hashes rolls back all updates. Non-gear pet/WPM
migrations use include_gear=False. Numeric recovery restores1369 rows to the
companion baseline while retaining effects/sockets for owned augments. New
acquisition recovery removes links only; never restore old inventory/AA state.
Preserve Seru's two independent new links and original loot. Fresh target
preimages, matching caches/world/zone and client spell/dbstr pairing are required.
Source/tests: thj_item_parity.py, thj_item_migration.py, thj_combined_content.py,
item_scaling_overrides.py and test_thj_*, test_item_scaling_overrides.py.

Production installed all1393 full-row afterimages, matching caches and the paired
native image. Three rule-note strings now match compiled ruletypes.h because
world normalizes them on startup. Forward/disable/enable guards were rehearsed
on the retained public clone after that normalization; no live SQL repair was
needed. Keep numeric recovery separate from effects, sockets and owned state.

## Built-in item colors — deployed October 18

Current fix source: C:/Users/verre/.codex/worktrees/reforge-default-colors/EQ_Local_Dev,
native PR225 and operator PR227/228. PlainUpgradeItem and PlainForgeItem accept
zero or exactly ItemData::Color; any other nonzero instance color is dye and
remains rejected. Native constructors start with the definition color, which was
why ordinary Daggers of Marnek failed. Do not strip input colors or weaken exact
saved-row preimages. Output keeps its target definition color and binding.
Recipes, augment/ornament/custom/evolving guards and atomic receipts are unchanged.

Source: server-mods/code/zone/advanced_loot_inventory.cpp. The complete native
translation-unit fixture adds61 cases (all six tiers, zero/default/different dye,
output color/binding/receipts, zoneforge and saved-color drift), with policy/package
controls and12 operator groups. Retained cooldown inputs re-link byte-identically;
only this implementation object changes. No header/ABI, SQL, cache or client change.

Zone29b8093147ffbc4c0d387a4e3fa55a3a041dbb9ae7da731b493b21601a6dec2f
is deployed across12 zones; gateway open,47 player/28 custom tables preserved.
Keep cooldown migration and proxy0.10.0/game2026101801. Native changes require the
supported whole-runtime restart, not quest reload or killing one zone. Recovery
uses the immediately preceding cooldown-capable image without restoring player
snapshots or replaying migration. Evidence and exact Palwar three-Normal combine
QA: docs/releases/reforge-colors-20261018/. Owner confirmed Palwar's reported
three-Normal Dagger of Marnek combine on October18. Relog, actual-dye/customized
rejection and other tiers/zoneforge remain unconfirmed. owner-acceptance.json
records that scope; historical deployment receipts retain their earlier status.

## Ordinary loot rates and quest reward direction — October 18

20% Polished / 5% Exalted / 1% Ascended: deployed and globally reloaded; player balance QA remains open.
Existing Zone:LootTierRare/Epic/LegendaryChance DB overrides are 2000/500/100
out of10000 when activated; compiled defaults remain1000/200/25. One roll per
eligible ordinary equipment/bag drop, not kill. Missing variants stay base;
hunt/dungeon rates and3/4/4 reforging are separate. Existing generated loot is
not rerolled. No binary/cache/client change; world and all zones reload rules.

Actual deployed source is server-mods/code/zone/loot.cpp, matching the retained
October17 and October18 cooldown manifests. The older loottables.cpp pointer
does not describe this reviewed build. Exhaustive native roll test and five
temporary MariaDB guard/forward/inverse cases pass. Evidence/operator/QA:
E:/EQ_Local_Dev/_worktrees/loot-quality-rates/docs/ops/loot-quality-rates-20261018/.

## Substantial class-armor rewards — October22 deployed for live QA

Owner-authorized main PR285/7f97288 and the17:07UTC production receipt deploy37
Crafted/Lambent/Darkforge/Ivy Etched/Totemic rewards as existing +600000 Ascended
items, even when repeatable; cheap/basic hand-ins remain excluded. Source:
E:/EQ_Local_Dev/_worktrees/quest-armor-ascended; exact membership is
 docs/items/quest-armor-catalog.json. No new stats/sockets/eligibility or global
SummonItem hook. Armor of Ro, mixed cleric quests and cultural crafts remain
separate audits/candidates. Never imply every crafted item now qualifies.

Ten reward scripts change only final IDs. The eleventh, Kurron Ni, selects each
submitted Normal/Ascended Darkforge piece under the original platinum>=900 gate.
The later quest-tier PR290 deployment installs the native ingredient-quality
and currency correction described above. The39 historical Perl fixture subtests exercise
captured quests/plugins code, not the currently configured root plugins/ native
helper; they prove the tested fixture only. Preserve that distinction in QA.
113 Lua cases and21 catalog guards are additional candidate evidence.

Fresh roots/all-existing-version probes and37 paired-cache identities passed.
The zero-client admission hold used world lock plus gateway pause, then12
aggregate Quest reload acknowledgments; every world/zone lifetime and all5
service identities were unchanged. No restart/cache/client update. Palwar's
slots7/17/19 changed4176/4174/4180 to604176/604174/604180 in one full-row-guarded
transaction. All17 fields except item_id and every other inventory row stayed
unchanged. This authorized correction is not automatic owned-gear conversion.

Evidence/operator: docs/releases/quest-armor-20261022/deployment/.17 fault tests
and5 actual MariaDB temporary-table rehearsals pass. Recovery restores scripts
only, never player snapshots. An uncertain SQL client needs a successful-return
marker plus exact fresh state before reopening; missing completion/unknown DB
session stays held. Gateway hold is attempted before a failing world control.
Public wiki20261022-quest-armor-v2 verifies465files and preserves robe2203 and
waypoints. Native fresh-hand-in/equip/relog and balance acceptance remain open.

Successor PR290 is deployed: paired zone and seven files, including the corrected
Kurron. Ten live armor reward scripts are preserved; current quest-tier evidence
is linked above. Native fresh-hand-in and balance acceptance remain open.

## Gear bands and finished cultural armor — October18 candidate

The production audit confirmed ordinary damage already scales at rounded
110/120/135% of Normal, unchanged delay; low integers can plateau. The earlier
minimum +1 candidate is SUPERSEDED and must not deploy. Its CLI is retired and
bootstrap block removed. Historical migration artifacts are not current policy.

Owner now permits reductions to ordinary Normal starter gear. This replaces
the preserve-Normal/35AC entry-dungeon proposal; its CLI is retired. Current
offline candidate covers209 fixed starter families/836 definitions, including
all reviewed sizes, cloaks/girdle variants and Rusty/Bronze weapons. Normal
Bronze chest6AC, then7/8/9; dungeon Normal chest12/16/20/24 across20/30/40/50.
Starter weapon damage increases exactly1 per quality with unchanged delay and
strict Ascended ratio below every comparable Normal dungeon reward. Spell/heal
bonuses0/1/2/3 and no starter heroics.821 starter and292 dungeon definitions
differ; zero cultural-catalog overlap. No live/compiler/cache/client changes.

tools/starter_retune.py pins the209-ID allowlist and Rusty profiles independently
of input capture; unlisted/cultural substitutions reject. Eight focused tests,
three dungeon catalog and20 cultural regression tests pass. Fresh review found
two guard/test limitations, resolved and re-reviewed. Source/report:
docs/items/starter-retune-reference.json and docs/releases/starter-retune-20261018/.
tools/tests/test_starter_retune.py verifies every captured family/quality and
complete changed-field allowlists. This proves AC/ratio ordering, not combat
acceptance. Fine Steel, named/quest, bows/jewelry and other ordinary classifications
remain open. Full-row guarded item migration, legal multiclass/AA/pet encounter
measurements and owner QA precede activation. Item changes need matching cache
regeneration and supported runtime restart; no client ABI change is proposed.

Exception: only approved finished cultural crafted armor produces existing
ordinary +600000 Ascended outputs directly. Explicit reviewed catalog has1041
recipes/944 armor pieces; do not infer membership from race flags, names or kits.
General recipes also use racial kits. Excludes materials, intermediates, weapons,
jewelry, shields and held items; owned Normal items stay Normal. Disabled recipes,
skill/cost/failure/learning and returned tools remain intact.

Checkout E:/EQ_Local_Dev/_worktrees/weapon-tier-damage: docs/items/cultural-armor-catalog.json,
tools/cultural_armor.py, capture_cultural_armor.py, cultural_armor_migration.py,
rehearse_cultural_armor.py and tests/test_cultural_armor.py. Full-row SQL guards
1041 recipes/8820 entries/1888 definitions; only pure-success item_id changes.
No component consumers or task references found; production script literal scan
found no direct item dependencies.20 planner tests and11 full-catalog MariaDB
forward/inverse/drift cases pass; independent review complete.

NOT DEPLOYED. Activation requires authorization, fresh capture/backup and crafting
maintenance window. Recipe success rows load per combine in GetTradeRecipe, for
manual and browser paths; no binary/client change. Existing Ascended target cache
presence is still an activation gate. Any needed cache repair uses the current
paired runtime and supported full restart, never a zone kill. Inverse restores
recipe outputs only, never player inventories or already-crafted armor.
Evidence, exact manual/browser/failure/tool-return QA and open balance decision:
docs/releases/cultural-armor-20261018/README.md and ADR0064. No live acceptance.

## Item recast timer integrity

October17 PR220 deployed signed click-duration clamps before uint32 conversion;
excess reduction previously yielded roughly136 years. Ordinary/negative/equal/
excess focus and augment publication remain covered. Current production evidence
is docs/releases/october-17-2026/; earlier audit is cooldown-audit-20261017/.

The follow-up identity correction deployed October18 via PR223. Unlinked
-item_id in uint16 formerly aliased at65536 intervals and overlapped other domains.
The deployed implementation uses uint32
0x200000+itemID, rejecting IDs above the client limit0xfffff. Every item/augment
verify, set/get/delete and cooldown path uses the same identity. Linked item
groups remain unchanged and are not declared intentional by catalog membership.
The SELECT-only capture has1158 unlinked definitions; ownership is unproven.

Saved client timestamp and native PTimer may differ: GetItemCooldown and saved
publication preserve the longer remaining wait without changing either deadline.
Unlinked items publish through inventory timestamps/SendItemPacket; their recast
helper does not send a native group packet. Tests execute actual item methods,
including IDs64350/129886 and out-of-domain rejection, plus the longer-wait case.

Pair the rebuilt zone with stopped-game guarded SQL and the existing Monk client.
Migration copies ambiguous waits to every successor and merges immediate
character_item_recast timestamps. It preserves longest deadlines and checks item
membership/click/delay preimages, not counts alone. Rollback conservatively folds
waits back, removes all high keys before old code and retains item records. No
old player snapshot or timer wipe. No new ItemData/cache/DLL layout change.
Exact source,27 duration/item/discipline tests,15 database rehearsals, build,
review and visible QA: docs/releases/cooldown-identities-20261017/ in the checkout
listed in multiclass.md. Full grouped-item/spell/discipline family design is open.

## Item stack minimum 100 — deployed October 17

Raised exactly 20,490 already-stackable definitions below 100, including 6,734
tradeskill materials. Higher limits, nonstackables, charges, recipes, prices and
player inventories are preserved. Leather Padding 16488 goes 50→100; ore 10500,
water 13006 and bandages 13009 go 20→100. Existing stacks merge manually.

tools/item_stack_sizes.py produces guarded ID/old-limit SQL; three planner and
nine actual MariaDB temporary-table cases pass, including preimage drift and
post-update rollback. Current source is E:/EQ_Local_Dev/_worktrees/october-17-release.
Combined deployment verified every item column and the entire regenerated cache,
allowing only 20,490 signed StackSize fields at offset 802 in 1,332-byte ItemData.
The existing shared_memory binary and all other item policies are retained.
Evidence: docs/releases/october-17-2026/ and docs/ops/item-stacks-100-20261017/.

Items require supported cache regeneration/runtime restart, not rules/quest reload.
After access could open, keep the higher limits: never shrink under existing
stacks or restore old player SQL/cache. Banking/crafting/trade/relog QA remains open.

Item-policy audit refreshed 2026-10-13 for the deployed divine-summon exception; other item systems retain their October 12 audit scope. Keep the independent reward systems distinct; use their explicit catalogs and current source. A stale runbook still saying every zoneforge recipe costs three is superseded by the October 12 upgrade policy.

| System | Implemented contract | Source/evidence |
|---|---|---|
| Legacy quality loot | Base/Polished/Exalted/Ascended, offsets +200k/+400k/+600k; epics separate +800k. October18 rates20%/5%/1%; see activation status above. Per eligible drop, not kill. | `server-mods/code/zone/loot.cpp`, exact retained manifests and `docs/ops/loot-quality-rates-20261018/` |
| Classic hunt | Two independent 0.5% rolls per eligible death: augment and wearable; weights 60/30/8/2, top tier **Ascension**. 48 audited combat zones enabled, eight access-check zones gated. | `server-mods/code/zone/zone_hunt.cpp`, `common/zone_hunt_catalog.h`, `common/zone_hunt_policy.h`; `docs/releases/zone-loot-20261009/PRODUCTION.md` |
| Zoneforge | Baseâ†’Polished costs 3; Polishedâ†’Exalted and Exaltedâ†’Ascension cost **4** after Oct 12. No cross-family conversion. | `zone/zone_hunt_forge.cpp`, `common/item_upgrade_policy.h` (`ZoneCopies`) |
| Reforging Box | Live October17: four Polished→Exalted or Exalted→top tier, plus **three identical eligible Normal/Base→Polished** for ordinary and hunt families. Free reusable four-slot box900620 from Artisan Veyra999820; dungeon rewards and top tiers excluded. | `common/item_upgrade_policy.h`, `zone/advanced_loot_inventory.cpp`, `quests/ecommons/999820.pl`; `docs/releases/october-17-2026/README.md` and component reforge evidence |

Item links must remain <=1,048,575. Prove IDs free across relevant tables and references, not just `items`; use guarded migrations. New hunt IDs start at 940000 and bypass legacy tier upgrading/global multipliers. Exact audited spawn/NPC identity, zone/version, level and special gates govern hunt eligibility. Pets, owned/script-created victims, services and restored dead NPCs don't reroll.

Hunt type-22 augments fit eligible head/arms/hands/chest/legs/feet sockets. At player level >=50 only qualifying socketed hunt-augment heroic INT/WIS adds output-cap headroom: `min(30,floor(effective heroic total/2))` for Spell Damage/Healing Amount. It doesn't grant missing raw bonuses. Don't apply this credit to arbitrary gear, AAs, buffs, NPCs or other augments.

## Normal-item box recipe — deployed October 17

Three identical eligible Normal/Base items produce one Polished. Higher costs
remain four; ContainerSlots remains four and BoxCopies selects 3/4/4. Legacy
inputs require an existing +200000 exact next-quality definition; hunt inputs use
NextTier and enabled hunt state. Dungeon rewards remain separate. Stack units
count individually; charged nonstackables count once. Binding, instance exclusions,
all-slot preimages, receipt atomicity and uncertain-result quarantine remain.

Source: common/item_upgrade_policy.h, zone/advanced_loot_inventory.cpp, client
packet messages and quests/ecommons/999820.pl. Actual inventory translation-unit
failure tests, policy/package controls and ten quest assertions pass. Current
full zone and Veyra script were installed together, preserving player data.
No schema/ItemData change or reward catalog regeneration. Never deploy the frozen
October12 builder over newer dungeon/journal code. Retain earned inventory and
receipts during recovery. Current proof/QA: docs/releases/october-17-2026/;
component evidence: docs/releases/reforge-normal-20261017/. Owner QA remains open.

## Dungeon reward catalog deployed for live QA

October 16 deployed; `docs/dungeons/{catalog.json,README.md,QA.md}` owns
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
The regenerated production cache preserves all 309,410 old records and adds
exactly 330 items. Deployment and continuing runtime checks pass; gameplay and
balance acceptance remain open. `docs/dungeons/deployment/` pins the actual pair.

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

Forge and box inputs, output and durable receipt commit together after exact inventory preimage checks. Binding is preserved. Accept zero or the exact built-in definition color; reject different nonzero dye and socketed/ornamented/evolving/customized instances; bags cannot nest in the box. Stack quantity is physical copies; a charged result still yields one unit. `nightcap_item_upgrade_state` revision 2026101201 gates box behavior; `nightcap_item_upgrades` and `nightcap_zone_hunt_forges` retain receipts. Missing/mismatched enablement rejects. Uncertain commit or packet publication quarantines the session; don't automatically retry consumption.

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
