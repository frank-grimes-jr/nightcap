# Classic dropped-gear focus coverage

Candidate; production and visible player acceptance are pending. User authorized test, main and deployment after validation. No custom content changes.

## Audit boundary

Fresh production capture dated November 20, 2026 checks all version-zero expansion-zero stock NPC → spawn → loot table → loot drop → equippable base item routes, with existing quality variants. There are 87,268 captured routes; expansion/content flags, probabilities, multipliers, NPC/trivial level gates and conditional spawns are retained. The unconditional usable pool is 1,470 families / 5,541 existing definitions; 1,381 have no focus. Including currently enabled conditional spawns yields 1,569 families, 1,477 without focus. Global loot adds 36 rawhide routes and no missing item definitions; Defiant's expansion-15 gate prevents its focuses from filling Classic gaps. Disabled conditional routes remain captured, not treated as currently obtainable.

The audit follows the server's explicit zone/loot era gates, not a claim that every expansion-zero database row is historically original EQ. Candidate items are established original Classic dungeon/raid drops. Quest rewards, merchants, spells, summoned items and custom NPC/reward content are outside dropped-stock modification scope. SQL full-row captures and negative-route dispositions remain reproducible in production.json.gz, supplement.json and coverage.json.

## Selected additions

19 stock families, all four existing qualities: 76 definitions. Only focuseffect and focustype change. Existing worn/click/proc effects, stats, sockets, restrictions, quality progression, loot chances and all other items remain unchanged. No existing focus is replaced. There is deliberately no focus on every mundane item.

| Base ID | Item | Example existing drop route | Added focus |
|---|---|---|---|
| 10351 | Brass Earring | crushbone / orc taskmaster | Improved Healing I |
| 10121 | Stone Collar | najena / a goblin magician | Improved Healing I |
| 10359 | Collar of Undead Protection | guktop / a froglok gaz squire | Mana Preservation I |
| 10318 | Onyx Ring | eastkarana / an evil eye | Spell Haste I |
| 10407 | Opalline Earring | unrest / an undead barkeep | Improved Healing II |
| 10341 | Glowing Stone Band | soldunga / goblin high shaman | Improved Healing II |
| 10355 | Reed Ring | guktop / a froglok realist | Spell Haste II |
| 1411 | Turquoise Eyepatch | soldunga / inferno goblin torturer | Spell Haste II |
| 10339 | Obsidian Bead Hoop | soldunga / Singe | Mana Preservation II |
| 1409 | Hooded Black Cloak | mistmoore / a cloaked dhampyre | Mana Preservation II |
| 2406 | Thick Banded Belt | gukbottom / a ghoul supplier | Improved Healing II |
| 1557 | Shawl of Protection | fearplane / a dracoliche | Improved Healing III |
| 11052 | Tobrin's Mystical Eyepatch | permafrost / Lady Vox | Spell Haste III |
| 20747 | Mithril Air Ring | airplane / a spiroc banisher | Mana Preservation III |
| 4344 | Golden Efreeti Bracers | airplane / Noble Dojorn | Mana Preservation III |
| 9315 | Shield of Prexus | kedge / a seahorse matriarch | Mana Preservation III |
| 4885 | Ethereal Mist Gauntlets | hateplane / Cleric of Innoruuk | Improved Healing III |
| 4875 | Rune Etched Gauntlets | hateplaneb / a spite golem | Improved Healing III |
| 4856 | Valorium Greaves | hateplaneb / a haunted chest | Spell Haste II |

## Balance policy

Stock haste is 15%, Improved Healing up to20%, Mana Preservation up to10%. Current Nightcap healing/mana focus selects the strongest endpoint; these are not the tenfold damage-focus rule. Ranks extend spell-level coverage, not percentage magnitude: I20, II44, III60, with existing5%-per-level decay. Haste also retains minimum base cast times I1s, II2s, III3s. Therefore II remains useful for2s Light Healing even with raid gear; III does not accelerate it. Minor Healing1.5s can use I. Limits use the spell's canonical minimum level across held classes, not the player's level. Native checks cover this distinction.

Same-category item/augment focus uses the strongest eligible source, not additive stacking from multiple pieces. Spell/AA contributions remain native separate sources and caps. Quality variants receive identical focuses. Before recovery/interruptions, the upper-bound new three-focus package gives1.2/0.85≈41% cast-limited healing throughput and1.2/0.9≈33% healing per mana; actual benefits depend on existing effects and legal spells. This is meaningful sustain, not interrupt immunity or instant casting. Greater Healing's spell data is unchanged.

## Validation and limitations

Catalog tests validate existing routes, all qualities, exact focus limits and focus-only SQL. Migration guards every original item field and supports idempotent forward/inverse; production promotion requires disposable DB forward/replay/inverse and exact native-cache comparison across all310,028 records.

The diagnostic reproduces the exact shipping zone hash and uses production item/spell caches,452 freshly captured rules and identical NPC definitions. Seven level20/35/50 legal held-class fixtures compare identical before/after equipment across five seeds and AA off/on. Sustain AA budgets spend39/99/108 points, not unrestricted AAs. It runs native timed casts, mana consumption, damage, avoidance, fizzle/channeling and healing under primary-hand pressure. Synthetic character IDs920100–920106 exist only in an isolated balance DB and have no player character rows.

This is a neutral-arena primary-hand pressure measurement, not a complete boss fight: no NPC AI/AEs, outgoing attack policy, pets, pathing, regen or timed buff processing. It cannot prove live encounter win rates or player acceptance. Measured results and deployment receipts will be added after validation.

## Exact in-game QA (OPEN)

1. Reconnect after deployment. Inspect Normal and upgraded copies of Brass Earring, Opalline Earring, Turquoise Eyepatch, Hooded Black Cloak and raid targets; confirm named focus and unchanged stats/clicks/sockets.
2. PAL/WAR level20 in Unrest against a dry bone skeleton: compare Minor Healing200 and Light Healing17 with Onyx Ring equipped/removed. I covers eligible1s+ spells. Keep gear and AAs otherwise fixed.
3. Level35 PAL/WAR in Lower Guk against a wan ghoul knight: compare Light Healing17 and Healing12 with Reed Ring/Opalline/Obsidian Hoop. Greater Healing15 is not yet a legal Paladin spell (level36). Repeat CLR/WAR, DRU/WAR and SHM/WAR using Greater Healing.
4. Level50 PAL/WAR in SolB against fire giants: compare mana, landed healing and interrupted casts with the listed haste/healing/mana focuses. Repeat with ordinary legal sustain AAs. Record attempts, landed casts, mana use and damage over a fixed interval.
5. In Permafrost, Fear, Hate, Kedge and Sky inspect the listed stock raid drops. Compare Greater Healing with Tobrin's Eyepatch, and Light Healing with HasteII. Confirm HasteIII does not accelerate2s Light Healing. Wearing multiple qualifying haste/healing/mana items must not sum same-category percentages.
6. Repeat full endgame gear with existing Classic/Prismatic/Dodging augments. Confirm HP/mana/Heal Amount/Spell Damage totals, legal sockets and worn defensive effects remain unchanged. Check normal zone/relog persistence. Keep actual encounter difficulty feedback distinct from synthetic measurement.

## Release contract

Content-only SQL plus matching item-cache rebuild through supported whole-runtime restart. Preserve current AA-fixed zone/world, signed client2026112001, spells, rules, custom/player tables and ongoing progression. No new client download. Guarded deployment requires a fresh stopped backup, zero-player maintenance window and healthy12workers; post-SQL failures hold access closed for review, never restore an old player snapshot. Wiki impact: equipment/focus guide, Features, home and release summary; generated custom item catalog values remain unchanged.
