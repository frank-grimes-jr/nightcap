# The Heroes' Journey — Target Spec and Nightcap Gap Map

THJ is the design spec Nightcap replicates. This is the durable local record of THJ's systems (its wiki blocks scraping; sources at bottom, verified 2026-07-13) and where Nightcap stands against each.

## 1. Multiclassing — THJ's signature system

**THJ spec:**
- Every character combines **3 classes** (560 combos). 2nd/3rd chosen via guildmaster NPCs in the Bazaar after first login.
- You ARE all three simultaneously: all spells, disciplines, skills, AAs, and itemization from all three.
- **Best-of rule** for singular attributes: highest base HP, best AC softcap, highest skill cap per skill (MNK/WAR/PAL → WAR defense caps, MNK 2HB/block).
- All self-cast buffs **stack**; **multiple pets** simultaneously (one per pet class).

**Nightcap status:** Partial. Chronicler NPC (PoK, not Bazaar) grants up to 2 extra classes; AA access via per-character mask (clean); spells via *global* `spells_new` patch (deviation — THJ is effectively per-character; RoF2 client-side scribing forces the global patch); skills copied into `skill_caps`.
**Gaps:** best-of base stats (HP/AC/regen), self-buff stacking, multi-pet, revoke doesn't undo spell/skill access.

## 2. Item tiers

**THJ spec:**
- Every item exists in 3 versions: **Base / Enchanted / Legendary** (Enchanted ≈ boosted stats, Legendary ≈ boosted + heroic stats). All tradeable, all equippable at level 1.
- Drops roll tier by RNG; a server-wide **Luck buff** (donation-funded) boosts rates.
- **Upgrading paths** (evolving-item style): level an item in the power-source slot via kill XP; feed duplicate copies via a **Consume Item AA**; or combine up to **16 copies** (Base=1, Enchanted=4 points) in the **XL Gnomish Quadramorphic Combinerator** to produce Legendary.
- Legendary **attunes on equip**; special unattuner item to trade it again.

**Nightcap status:** Partial. 4 static tiers (Base/**Polished/Exalted/Ascended** at +200k/+400k/+600k id offsets — renamed 2026-07-15 to avoid THJ's Enchanted/Legendary vocabulary) drop via a `NPC::AddLootDrop` hook with rule-tunable chances (10%/2%/0.25%; rule names still carry the old Rare/Epic/Legendary tokens). Per-family scaling calibrated to **actual THJ Legendary** (measured off Necklace of Eternal Visions 9289, issue #25): HP/Mana ×1.45/1.90/**2.40**, AC/stats/resists/regens ×1.35/1.65/**2.00**, Endurance ×1.07/1.13/**1.20**, offense ×1.10/1.20/**1.35** (conservative — burst from AA/disc/augs). Capped advanced stats + heroics left untouched (heroics deferred to #8, which is where THJ's Legendary heroic *additions* belong). Class epics excluded; Ascended epics via quest (8× Essence of Ascension + 100k pp).
**Gaps:** no upgrade/combine path (drop-only), no luck buff, no attunement, 4 tiers vs THJ's 3 (deliberate deviation). Forgemaster quest is multiclass-blind (base class epic only).

## 3. Progression

**THJ spec:**
- **Account-wide** expansion unlocks, self-paced after a server-wide time gate. Two paths per expansion:
  - **Hero:** slay the era's flag bosses (Kunark = Lord Nagafen AND Lady Vox; hail the NPC that spawns for credit).
  - **Explorer:** gather specific items at **Legendary quality** and turn them in.
- Must clear an expansion's endgame to move to the next.

**Nightcap status:** Missing as a player system. Expansion lock is a GM-tool toggle (`/api/expansion/apply` sets `Expansion:CurrentExpansion` + level cap + zone locks). No player-driven unlock, no account-wide flags.

## 4. AAs

**THJ spec:** critical AAs auto-granted at level 1 per class; most AAs (through TBS) purchasable with **no level restriction**.

**Nightcap status:** Close. Level gates removed (all ranks level_req=1); AA visibility era-unlocked (`UseCurrentExpansionAAOnly=false`); multiclass AAs via mask with static `[CLS]` name prefixes; General/Archetype duplicate families deduped (2026-07-13, `multiclass_aa_dedup.sql` — winner keeps longest rank chain, revert log in `aa_dedup_migration`). Gap: no auto-grant of critical AAs (except custom Ancient Attunement PoK-recall granted on connect).

## 5. Quality of life

**THJ spec:** no XP loss / no corpse runs; permanent self & group buffs; debuffs clear when combat ends; instanced versions of most contested zones; **Bazaar-and-Back AA** (teleport to hub and return to exact spot); big bags; ornament transforms; no-MQ2 policy with detection.

**Nightcap status:** Partial. Instance Keeper NPC + 7 starter dungeons; permanent bard songs; Ancient Attunement (PoK recall, 10-min CD — one-way, no "and back"); PoK as universal start/hub (vs THJ's Bazaar); bag vendor. MQ2 is *used* here (solo QoL) — deliberate deviation.
**Gaps:** XP-loss/corpse rules unverified, general permanent buffs, debuff-clear-on-combat-end, return-trip teleport.

## 6. Economy / community

**THJ spec:** Bazaar as working trader hub (IP-restriction exempt); **Echo of Memory** — rare world-drop (also donation) currency for luck buffs and services; everything tradeable until Legendary-attuned.

**Nightcap status:** Missing/N-A. Solo server — economy systems are low priority by design. PoK vendor cluster (4 archetype spell vendors + bags) covers acquisition instead.

## Suggested build order for remaining gaps

1. **Progression unlocks** (Hero path first — boss-kill flags via quest script + `data_buckets`, account-wide) — biggest missing pillar, self-contained.
2. **Item upgrading** (Combinerator-style container combine is simplest — no evolving-XP plumbing).
3. **Buff stacking / permanent buffs** (C++ `spdat`/buff-slot work — invasive, do when confident).
4. Debuff clear on combat end (small C++ hook).
5. Best-of base stats for multiclass (C++ `CalcMaxHP`/softcap — pairs with #3).

## Sources (verified 2026-07-13)

- Announcement/feature list: eqemulator.org forums thread t=44193
- wiki.heroesjourneyemu.com — /en/progression, /en/FAQs, /classes-and-abilities (browser-only; blocks fetch)
- heroesjourneyemu.com/faq
- Community detail (drop mechanics, combinerator ratios): firesofheaven.org THJ thread; resetera.com THJ launch thread
