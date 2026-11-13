# Worn ATK on stock tiered equipment

November 13 local test runtime validation. Existing item definitions supply the ATK sent to the RoF2 item window and consumed by the server. The candidate changes only the attack field of 405 existing definitions across 135 stock families. Production was queried read-only. The live default ruleset has a 250 worn ATK cap. The signed client, combat code, cap, acquisition and custom equipment require no changes.

## How families qualified

The linked Legendary values in EquipmentDB agree with the October ATK hypothesis on 229 of 232 families. There were 141 differences against production, of which 138 followed the hypothesis. The fourth workbook duplicates the first EquipmentDB. The second workbook adds 124 populated ATK observations spanning 121 overlapping IDs. Only formula-confirmed, ID-matched ordinary stock families with no contradictory ATK evidence and no existing exact ATK override enter the new model. Of the 157 qualifying families, 22 already match. The remaining 135 produce the guarded migration. The Singing Short Sword has a separate epic tier family.

With positive stock ATK, the target adds ceiling(stock STR / 4) to stock ATK. With zero stock ATK, the target is ceiling((stock STR + stock DEX) / 2). Polished and Exalted use Nightcap’s existing one-third and two-thirds interpolation with half-up rounding. The directly observed tier is Legendary, mapped to Ascended. Stock Normals and every item outside the ID list retain their existing policy. Individual Ascended increases range from the values in the [per-item delta](changes.csv) up to +30 on Staff of Transcendence (requires level 65). Of the 135, 54 have a required level at or below 50, including 36 with a recommended level above 50. Required level alone does not establish era access.

| Stock family | Evidence | Candidate |
|---|---|---|
| Armguard of Shadows | Normal 50, both top-tier sheets 53 | Polished 51, Exalted 52, Ascended 53 |
| Heavy Yttrium Chestplate | Normal 15, both top-tier sheets and existing Ascended 20 | Existing 15 / 17 / 18 / 20 |
| Charm of Nimble Landings | EquipmentDB 10, Sheet2 row 31 gives 12 | Hold at current Ascended 0 |
| Leaf-twined Guards | EquipmentDB 13, Sheet2 row 6 gives 47 and also differs on other fields | Hold at 0. Required level 65 |
| Bracer of Timeless Rage | Both November worksheets give 23. The earlier exact catalog and production give 25 | Retain 25 |
| Girdle of Focus | Both sheets give 20 versus formula 14 | Hold at 10 pending independent item evidence |
| Cloak of Wishes | Sheet 22 versus formula 20 | Hold at 15 |
| Burning Mask of Terror | Sheet 8 versus formula 0 | Hold at 0 |

[EquipmentDB workbook](https://docs.google.com/spreadsheets/d/1DQEuJrpqiIV4TgdagLp56_2eu0pm1ujipQuY99FhvSo/edit) · [Sheet2 workbook](https://docs.google.com/spreadsheets/d/1aisSR_up03KrCuIL2nJeA3VIwNT3LKzng0w8HV_p67s/edit) · [Reconciled ID, row and ATK observations](worksheet-check.csv) · [Pinned stock model](../../releases/thj-behaviors-20261019/stock-REVIEW.md).

## Item value, worn contribution and displayed rating

The shared loader copies items.attack to ItemData::Attack. RoF2 sends that field in the item packet. The ordinary worn path checks required level, applies recommended-level scaling, and caps the sum using the rule plus item, spell and AA cap bonuses. The signed Inventory panel on production consumes Client::GetTotalATK(). It weights worn ATK by 1.342 and also includes skills, STR and other bonuses. Integer truncation can affect the last display point. Melee offense has a separate calculation. These measurements quantify item contribution and Inventory rating; they do not establish percent DPS.

The compiled fixture uses the actual recommended-level function, capped ATK assignment, final clamp and GetTotalATK body. Offense skill 110, primary skill 140 and STR 180 are fixed to isolate the ATK field; the item’s other stats are held equal.

| Ascended Armguard case | Effective worn total, current → candidate | Displayed rating change |
|---|---:|---:|
| Level 60, other worn ATK 0 | 50 → 53 | +4 |
| Level 50, other worn ATK 0, recommended level 60 | 42 → 44 | +3 |
| Level 60, other worn ATK 199 | 249 → 250 | +1 |
| Level 60, other worn ATK 200 | 250 → 250 | 0 |
| Same 200 with +10 ATK cap from AA | 250 → 253 | +4 |

## Local test runtime validation

The persistent local akk-stack database and item cache now contain all 405 intended values. Its older setup had generated ATK at 1.10×, 1.20× and 1.35× stock. All 405 local preimages matched that generator, 34 were already at their targets, and 371 required a write. The test migration used the full local item preimages and changed ATK alone. Its original stock fields, custom sockets and effects were preserved. The forward/rollback pair pinned to the November 13 production snapshot remains the production-source candidate.

The stopped, empty test world was backed up before installation. After restart, the world and all eight zone workers mapped the rebuilt item cache and admissions were open. Of 308,928 effective cached item records, 371 differed solely in the ATK field; 308,557 were byte-identical. A probe linked against the local RoF2 encoder decoded 405 actual item-link packets plus eight controls. It verified the Armguard tiers at 50, 51, 52 and 53. The spell cache and server executable hashes remained the same.

A separate native zone diagnostic equipped, removed and re-equipped the cache-loaded Ascended Armguard on a synthetic Ranger at levels 50 and 60. Against a copy of the same item with ATK 50, effective worn ATK rose from 42 to 44 at level 50 and 50 to 53 at 60 before the cap. Inventory rating increased by 3 and 4 respectively. At 250 pre-existing worn ATK there was zero change to rating, melee offense and the paired native mitigation rolls. Each case used 20,000 landed-hit mitigation rolls at a fixed mitigation value of 300. Full encounter DPS remains unmeasured. The actual local predecessor Armguard had 68 ATK.

[Machine-readable DB, cache, packet and equip results](test-runtime.json) · [RoF2 packet probe](rof2_atk.cpp) · [Native equipment and mitigation probe](zone_probe.cpp). Visible RoF2 window rendering and player-driven encounters have not been observed. The public wiki and OVH runtime were outside this test activation.

## Reproduction and test-stack handoff

- Run `python docs/items/stock-worn-atk/plan.py --check` from the repo. It checks both migration files and the item-by-item CSV against all captured fields. The planner rejects unexpected Normal, tier-identity and ATK drift.
- The local MariaDB rehearsal loaded 926 complete production item rows into a disposable schema. It checked full-row equality after forward, replay, reverse and reverse replay, and rejected late drift on a Normal stat and an unrelated socket before writing any target. The 135 unchanged Normal rows are locked as guards and excluded from UPDATE. Both migrations set only ATK.
- Fresh setup uses the usual `python tools/thj_stock_scaling.py --bootstrap eq-solo-gm/scripts/thj-stock-bootstrap.sql`. A full comparison against the prior bootstrap isolated exactly the same 405 ATK cells. Its dated receipt is [bootstrap-check.json](bootstrap-check.json). Use forward.sql.gz for an existing test DB and rollback.sql.gz to reverse the same scoped definitions. Rebuild the item cache and reload it in the matching test runtime before checking equipped characters.
- In RoF2 on a test stack, inspect a clean Ascended Armguard, record / remove / re-equip with other gear fixed, then relog. Repeat at 50 and 60 and below, near and at the cap. Record STR and any buff/AA cap modifiers. Compare the before/after difference for the same item; equipping it also changes STR. Check the unchanged Heavy Yttrium chest, the two conflicting items, an equipped custom Hunt augment and the training slot. Record native combat parses separately before a broader rollout. No live visual or combat parse is claimed.

Relevant hooks are `tools/thj_stock_scaling.py`, `common/shareddb.cpp`, `common/patches/rof2.cpp`, `zone/bonuses.cpp`, `zone/client.cpp` and the signed Inventory summary in `zone/gm_commands/nightcapui.cpp`. The C++ paths are under `server-mods/code/`. This is a content candidate with a test-only wiki preview.
