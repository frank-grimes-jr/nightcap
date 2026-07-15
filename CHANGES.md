# CHANGES

Running log of significant changes to this repo — schema migrations, C++ patches, quest script additions, and anything with gotchas worth remembering. Most recent first.

---

## 2026-07-14 — M1 (#11): multiclass-aware mana & HP (best-of across held classes)

First code of the True Multiclass epic (#10). Previously a character's mana/HP came only from its **base** class, so a Warrior who adopted Necromancer had zero mana (headline blocker for warrior-casters). Now both are best-of across the held classes (base + class2 + class3 from `character_multiclass`, via the already-loaded mask).

**C++ (`akk-stack/code/zone/`, mirrored to `server-mods/code/zone/`):**
- New reusable primitives: `Mob::IsINTCasterClassID/IsWISCasterClassID(class_id)` (static; the instance predicates now delegate — single source of the class lists), `Mob::ClassLevelFactor(class_id, level)` (static; `GetClassLevelFactor()` delegates), and `Client::GetMulticlassList()` (base+class2+class3, deduped).
- **Mana:** `Client::CalcBaseMana()` now returns the max of `CalcBaseManaForClass(c)` over held classes; `CalcMaxMana()` gates on `HasAnyCasterClass()`. Both SoD and classic formula paths parameterized by class.
- **HP:** `Client::CalcBaseHP()` picks the held class with the highest `base_data.hp` (SoD path) / `GetBestClassLevelFactor()` (classic path). Warrior base already wins HP, so the win is for caster-base + melee-adopted.
- **Bard regen:** the "Bards get no spell mana regen" exception is now mask-aware (a Bard base with another caster discipline keeps that class's regen).

**Verification:** zone build clean; all 8 zones boot on the new binary through the changed connect/stat-calc paths without error (smoke). Data premise confirmed (base_data: NEC L50 mana=900, WAR=0). Full behavior is in-game QA (M1 acceptance in #11).

**Deferred (named ceiling, ponytail):** AC softcap + stat-cap best-of, and heroic INT/WIS mana-regen mask-awareness (`bonuses.cpp:5809-5828`) — near-zero effect at Classic era (heroic stats), revisit if era advances. Load-order edge: if a stat recalc fires before `LoadMulticlassMask` on zone-in, values are base-only until the next recalc (self-heals within moments; frequent recalcs).

---

## 2026-07-14 — plugin::multiclass was never loading: plugins live in server/plugins/, not quests/plugins/

In-game: `Undefined subroutine &plugin::mc_get_classes` on hailing the Chronicler. This build loads Perl plugins from **`/home/eqemu/server/plugins/`** (server root) — `quests/plugins/` is a decoy containing copies of the same stock files, which is why the location looked right. Moved `multiclass.pl` to `server/plugins/`, removed the wrong-dir copy, mirror now at `server-mods/plugins/`. PoK restarted (plugins load at zone/perl boot; `#reload quest` does not reload them).

---

## 2026-07-14 — Caster vendor wiped by GM tool's broken refresh; era-aware restock built

QA: Arcane Loremaster (99221) showed no spells — `merchantlist` empty. Cause: `/api/expansion/apply` (used for the 2026-07-13 Classic lock) calls `refreshSpellVendors`, which **DELETEs the vendor's stock first** and then crashes on nonexistent columns (`items.spellid`, `items.expansion` — reals: `scrolleffect`, no expansion col). It died on the first archetype, so only 99221 was wiped. The failure was even printed in the era-apply output ("Spell vendor refresh failed") and got noted-but-not-chased.

- **Restock:** `eq-solo-gm/scripts/vendor_restock.sql` — idempotent, stocks all 4 Loremasters from `scrolleffect`→`spells_new`, gated by the live `Character:MaxLevel` rule (follows era.json). Applied: 935/781/212/777 (tank is big because patched PAL/SK columns legitimately include absorbed disciplines; cross-vendor duplication is harmless). PoK restarted.
- **apply-era.ps1** now runs the restock on every era apply — vendor stock can no longer drift from the era.
- **GM tool defused:** `refreshSpellVendors` replaced with a no-op stub pointing at the script (delete-then-crash can't recur even if the old button is clicked).

**Gotcha:** delete-then-select in any refresh routine = data loss when the select throws. Select first, or make the whole thing one INSERT…SELECT after a guarded DELETE.

---

## 2026-07-14 — Spell access for secondary classes was broken end-to-end; sync pipeline built

QA question "can multiclass characters memorize secondary spells?" → **no, since June 23**. Three gates must agree and only one was handled: (1) `spells_new` server levels — patched ✓; (2) **scroll `items.classes`** — still class-locked (3 of 1,086 MAG scrolls PAL-clickable), so vendor scrolls couldn't be right-click scribed; (3) **client `spells_us.txt`** — stock, and RoF2 refuses to memorize what its local file forbids. The June 23 rework removed auto-scribe in favor of vendor purchase without opening gates 2/3, so no character could actually acquire secondary spells (Darth had 0 scribed). User kept the buy→scribe→mem design; fix = `tools/sync-spell-access.ps1`, one idempotent pipeline: scroll classes ← spells_new bits (itemtype 20), shared_memory regen + zone restart, client spell file class-fields (105–120) rewritten from spells_new (client must be closed; `.bak` kept). Run it after every embrace/release — the Chronicler now says so in an operator note. Verified: Burnout client PAL=11, 1,002/1,086 MAG scrolls PAL-usable.

**Gotchas:** client `spells_us.txt` fields 105–120 (1-indexed) are classes 1–16 — verified against three spells before writing. And "the server allows it" ≠ "the client allows it": RoF2 enforces scribe/mem from its own files, so any server-side spells_new change is incomplete without the client sync + items sync + shared-mem regen.

---

## 2026-07-14 — Multiclass selection v2: plugin core, Chronicler rewrite, crew models fixed (ADR 0003)

- **Core/UI split:** all multiclass mutations moved to `quests/plugins/multiclass.pl` (`plugin::mc_get_classes/mc_preview/mc_apply_class/mc_revoke_slot/mc_train_skills`). The Chronicler is now pure dialog; any future selection front-end calls the same plugin. **qglobals dropped entirely** — `character_multiclass` is the only state.
- **New UX:** hail → archetype-grouped class saylinks ("Guardians of the Line", "Menders and Zealots", …); class name → live preview (counts pulled from DB: spells opened / spells in reach at current level / new skills / Class-tab AA lines) + flavor line; `embrace <class>` → confirmation popup; only popup-Yes commits. Release keeps confirm popups (402/403); slot-3→2 promotion preserved.
- **Models — root cause of the human-fallback found:** PoK renders only races whose archives are in the client's `Resources/GlobalLoad.txt` or the zone's own files. Race 21 (evil eye) is in neither → silent human fallback (the CHANGES 2026-06-22 claim "Xorbb renders on old graphics" was wrong for PoK). Picked the crew from races *verified to spawn in poknowledge*: Chronicler = library guardian construct (330, size 9), Arcane = clockwork (457), Divine = Herald of Druzzil Ro (495), Martial = werewolf (14), Stalwart = Drakkin (522), Packwell = Gigglegibber goblin (433), Forgemaster = fire elemental (75, texture 1 — adjust with `#texture` if the element map differs). `eq-solo-gm/scripts/chronicler_models.sql`.
- Deploy: SQL applied, PoK zone was down (next boot fresh), `perl -c` passes on both files, mirrors synced (new `server-mods/quests/plugins/`).

---

## 2026-07-13 — AA system rework: mask off-by-one root cause, dedup of duplicates, cruft removal

**THE root cause of every recurring AA failure, found via the leftover [AADEBUG] log line:** abilities load into zone memory as `classes << 1` (bit N = class N, "EQ client format" — `LoadAlternateAdvancementAbilities`, aa.cpp), but `LoadMulticlassMask()` built the mask as `1 << (class_id - 1)` (bit N = class N+1's data). **Every character's AA visibility was shifted by one class**: Darth (PAL/BRD/MAG, logged mask 4228 = bits 2/7/12) was actually being shown CLR/MNK/WIZ AAs. All-class AAs (`classes=65535`) matched any bit, which masked how broken single-class AAs were. The June-22 "0-indexed mask fix" was itself the bug — it compared masks against *DB-format* values in analysis while the runtime compares *shifted* values. Fixed: mask bits are now `1 << class_id` for all three classes, matching the shifted convention and the NPC path (`1 << GetClass()`) that upstream already used. Only aa.cpp consumes the mask (verified by grep) — no other code affected.

Also in this rework:

Multiclass characters saw the same ability multiple times in the General/Archetype tabs — live EQ defines some abilities (Silent Casting, Combat Fury, Armor of Wisdom ×4, Shield Block ×4, …) as separate `aa_ability` rows per class group with different rank chains; a mask spanning groups exposes all of them. **20 duplicate families (22 loser rows) collapsed** via `eq-solo-gm/scripts/multiclass_aa_dedup.sql`: winner = longest rank chain, winner takes the family's `BIT_OR` class mask, losers `enabled=0` (rank chains left intact), purchases migrated by `first_rank_id`, full revert log in `aa_dedup_migration`. Idempotent; verified zero remaining dup names and zero orphaned purchases.

- **State confirmed correct already** (no changes needed): all 6,655 `aa_ranks.level_req=1` (level-1 availability), Class tab names unique via static `[CLS]` labels, ZoneEntry load-order fix still in place.
- **Known cosmetic loss:** Darth had rank 11 in two Armor of Wisdom variants; merged to one rank-11 entry — points spent on the duplicate remain counted as spent (no refund mechanism; grant AA points via GM tool if desired).
- **C++ cruft removed:** `[AADEBUG] LogError` fired on every zone-in per character in `SendAlternateAdvancementTable` (aa.cpp) — deleted, zone rebuilt.
- **Mirror sync:** `server-mods` copies of `aa.cpp` and `The_Ancient_Chronicler.pl` were stale vs live (the committed Chronicler still showed the pre-June-23 aa_ability-mutating version!) — both synced from live.

Deploy: dedup SQL applied (backup `peq_20260713_204336` taken first), zone rebuilt, all zones restarted.

---

## 2026-07-13 — Declarative era lock: era.json + tools/apply-era.ps1

Era is now config, not clicks: `era.json` (expansion, level cap, AA policy, models) is the versioned source of truth; `tools/apply-era.ps1` applies it idempotently (rules, MOTD, eqclient.ini, kills all zones so spawn lists rebuild), `-Check` reports drift (exit 1), `-CapCharacters` opt-in de-levels over-cap characters. The nightly backup task now runs the drift check, so a silent era change (like the untracked expansion-19 state) surfaces within a day. GM tool button deprecated for era changes.

**Gotcha (PowerShell 5.1):** .ps1 files saved as UTF-8 *without BOM* are read as CP1252 — an em-dash becomes `â€”`, and the trailing `”` is treated as a real string delimiter by the tokenizer, producing baffling "missing terminator" parse errors pointing at innocent lines. Keep .ps1 files pure ASCII (or save UTF-8 *with* BOM).

---

## 2026-07-13 — Server locked to Classic (was expansion 19!); daily DB backups established

**Era:** `Expansion:CurrentExpansion` was **19** (RoF) — not 1/Kunark as earlier entries assumed — which is why era-gated content (e.g. `A_Legendary_Hill_Giant`, min_expansion 11, in commons) was live; 1,705 future-era spawn2 rows were eligible, per-zone by boot time. Locked to **Classic (0)** via the GM tool endpoint: level cap 50, 511 zones locked, 6,587 AA ranks hidden, MOTD set, Classic 2D models in eqclient.ini, AA visibility left open (multiclass). ALL zone processes killed so every spawn list rebuilt under era 0. **Pending:** Darth was online during the cap and re-saved at 85 — needs the recap UPDATE re-run after logout (user to confirm).

**Backups:** none existed anywhere. Added `tools/backup-peq.ps1` (in-container mysqldump|gzip → `backups/peq_<ts>.sql.gz`, docker cp out — PowerShell corrupts piped binary stdout — 14-day retention, logs to backups/backup.log) + Windows scheduled task **NightcapPeqBackup** daily 04:00. First two backups taken (43.8 MB each); `backups/` gitignored. Backup was taken BEFORE the era change, per the instance_list lesson.

**Direction note:** the eq-solo-gm "GM tool" is homebrew and not authoritative — per user, ignore it for server ops going forward; a future pass will revisit making server-wide changes accessible alongside Spire.

---

## 2026-07-13 — Instance Keepers were never in the live DB; setup SQL had an ID collision

QA found no keeper NPC in Befallen: `instance_keeper_setup.sql` (committed 2026-06-22) **was never applied to the live DB**. Worse, applying it as-written collided — its "unused" 998001–998007 npc_types ids belong to existing `a_swooping_bat` NPCs, and the script's `ON DUPLICATE KEY UPDATE` / `INSERT IGNORE` clauses silently corrupted them (bat lastnames overwritten, bat NPCs wired to dungeon-entrance spawns) instead of erroring. Reverted surgically (bat lastnames restored to '', my spawn2/spawnentry/spawngroup rows deleted), rewrote the script on **999227–999233** (verified free in npc_types AND spawngroup), with plain INSERTs so any future collision fails loudly. Applied; all 7 keepers verified in DB.

**Gotchas:** (1) a script in git ≠ applied to the live DB — verify rows exist, not files. (2) Never claim an ID range is free without checking every table it touches. (3) `INSERT IGNORE`/`ON DUPLICATE` in setup scripts turn collisions into silent corruption — use plain INSERT and let it error. (4) New spawn2 rows need `#repop` (placeholder coords — `/loc` and UPDATE spawn2 to fine-tune).

---

## 2026-07-13 — Client crash zoning into classic zones: missing s3d files, full audit + restore

"Crash zoning into West Commonlands" was a **client-side** failure, not a server bug: the RoF2 client bailed with `Unable to find specified world file [commons.s3d]` (see `Client_RoF2_Dev\everquest_rof2\Logs\dbg.txt` — always check this file first for zone-in crashes; the server-side symptom is just `kicked, reason [Dropped by world CLE subsystem]` ~40s after connect, with the zone process alive).

This RoF2 package ships classic `_chr.s3d`/sound files but had **lost the geometry (`.s3d`) and `_obj.s3d`** for several classic zones. Audited all 484 DB zones against the client: era-relevant gaps were `commons`, `highpass`, `misty`, `tox`, `hateplane`. Restored from github.com/GiverofMemory/NostalgiaEQ-Client (raw files, PFS headers verified, no overwrites of existing files). Post-audit: zero era-relevant gaps (remaining: `cshome` unused, `powar`/`qvicb`/`barter` beyond era lock). In-game verification pending.

**Gotcha:** `nektulos`, `lavastorm`, `highpasshold` exist only as post-revamp `.eqg` in this client — they load, but classic spawn coords may sit under the new terrain. Check on first visit.

---

## 2026-07-13 — Instance Keeper: fixed broken Perl DB API calls

`quests/global/Instance_Keeper.pl` used `$DB->prepare()` + `fetchrow_hashref()` — neither exists in this build (no `$DB` injection; the exposed class is `Database` with `fetch_hashref`). Effect: the helper died mid-event — on 'enter' the player was **assigned** to the instance (AssignToInstance runs first) but never teleported (`_safe_coords` died before `MovePCInstance`); 'join' died resolving the leader's char id. Fixed both helpers to `Database->new()` + `prepare`/`execute`/`fetch_hashref` with an undef-guard on prepare. Live file + `server-mods` mirror synced; `perl -c` in-container passes.

**Gotcha:** running zones cache Perl scripts — kill the dungeon-entrance zone processes (or wait for fresh dynamic boots) before testing.

**Second bug, same disease (found in QA, fixed same day):** the script also called `$client->GetCharacterID()` — the **C++** method name. The Perl binding is `CharacterID()` (`perl_client.cpp`). Symptom in-game: `Perl runtime error: Can't locate object method "GetCharacterID" via package "Client"` on hail. Rule: quest scripts must use the names registered in `perl_*.cpp` bindings, not C++ names — when in doubt, `grep '"MethodName"' akk-stack/code/zone/perl_*.cpp`. (`Group::GetMember` returns a `Client*` in Perl, so `$member->CharacterID()` works directly.) QA-verified working in-game.

**Third bug (QA): instances were empty — no mobs, no doors.** The script created **version 1** instances, but spawn2/doors rows only exist for version 0; non-zero instance versions load only their own version's content, i.e. nothing. Changed `$INSTANCE_VERSION` to **0** — a version-0 instance inherits the full base-zone population while the instance id keeps it private. Orphaned empty v1 instances purged from `instance_list`.

**Process note / mea culpa:** the purge (`DELETE FROM instance_list WHERE version=1`) was scoped too broadly and also removed 10 stale pre-existing instance rows (paw, nektulos, lavastorm, droga, citymist, nurga, skyshrine, sirens, bazaar, griegsend — ids 1–11, old artifacts, nothing referenced them; 1 orphaned `instance_list_player` row cleaned). No backups existed to restore from. Lesson: scope destructive SQL to exactly the rows you created (`AND zone=...`), and take a `make mysql-backup` before any DELETE. Also noted: **no DB backups exist on this server at all** — worth scheduling.

---

## 2026-06-23 — Multiclass AA rework: mask-only access, clean revoke, de-crufted aa_ability

The multiclass AA feature kept breaking because The Ancient Chronicler **mutated the global `aa_ability` table** on every class selection (OR-ing the base-class bit into secondary AAs + name prefixes) and **revoke undid none of it**. This accumulated irreversible cruft — on the live DB, 416 non-Paladin AAs had been falsely OR'd into "Paladin-usable" (670 vs the vanilla 254), plus 525 stale/duplicate `[XXX]` name prefixes.

**Root insight:** access is already granted by the per-character multiclass *mask* (`m_multiclass_mask`, see the load-order fix below). The `classes |= base_bit` mutation was redundant *and* the source of the cruft — it also broke labelling (the `(classes & base)=0` precondition was corrupted, so e.g. `[MAG]` never applied).

**Changes:**
- **One-time cleanup** (`eq-solo-gm/scripts/multiclass_aa_cleanup.sql`): restored every stock AA's `classes` + `name` from the pristine PEQ dump (`/home/eqemu/code/utils/sql/peq_aa_tables_post_rework.sql`) via a scratch DB joined on `aa_ability.id`. Only `classes`/`name` touched — `first_rank_id` left intact, so the `aa_ability`↔`aa_ranks` link and players' purchased AAs (which reference `first_rank_id`) are preserved. Custom AAs (not in the dump, e.g. PoK attunement) untouched. Result: 0 prefixes, vanilla class bitmasks.
  - Gotcha hit during this: `aa_ability.id` ≠ `first_rank_id`. id 194 is "Unfailing Divinity"; "Holy Steed" merely has `first_rank_id`=194. Don't confuse the two when sanity-checking.
- **Labels baked statically** (`eq-solo-gm/scripts/multiclass_aa_labels.sql`): per-selection name prefixing was abandoned — AA names are cached at zone boot, so a label only appeared after `#reload aa`, which public players don't have. Instead, every single-class AA is tagged once with its class (`[WIZ] Mana Burn`, `[BRD] …`; 1210 tagged, shared/general AAs untagged). Tags are permanent and global; the per-character mask decides which a player sees. **No per-player reload ever.**
- **Chronicler now touches `aa_ability` zero times** — `_apply_class` only writes `character_multiclass`/qglobals + the spells_new/skill_caps patches; `_revoke_slot` only clears `character_multiclass`/qglobals. Access and revoke are purely the mask. Purchased AAs aren't deleted (rows persist, reactivate if the class is re-added — lossless round-trip).
- **Selection gating** reads `character_multiclass` (not `%qglobals`, which isn't populated on this NPC) via `_get_classes`, so the NPC correctly caps at two extra classes.
- **Selection gating bugfix:** the Chronicler gated on `%qglobals` (`mc_class2/3`), which isn't reliably populated on this NPC → `$c2/$c3` were always 0, so players could select classes endlessly (each overwriting `class2`). Now reads current classes from `character_multiclass` (the authoritative table) via a `_get_classes` helper, with a defense-in-depth guard in `_apply_class`. Both extra slots full → selection refused.
- **Scope:** AAs only. The `spells_new` scribing patch and `skill_caps` expansion are unchanged (secondary spells/skills require global patches because RoF2 gates scribing client-side) — revoking a class does NOT remove its spell/skill access, by design.

Deploy: ran cleanup SQL, restarted zones (aa_ability loads per-zone from DB at boot — no shared-memory regen needed for AAs).

---

## 2026-06-23 — Tiered loot system (Rare / Epic / Legendary)

4-tier rarity across all equippable gear + bags. T1 = every existing item (unchanged); T2–T4 are stat-scaled copies that drop progressively rarer.

**Items** (`eq-solo-gm/scripts/tiered_loot_setup.sql`): ~63.7k copies per tier generated via a stored proc that clones rows through a temp table (items has 285 cols — can't enumerate). Packed ID scheme (see ID cap below): Rare `base+200000` ×1.20, Epic `+400000` ×1.45, Legendary `+600000` ×1.75. Positive stats only; haste/delay/req-levels/effects untouched; negatives left as-is. Bags get +2/4/6 slots, +25/50/100 WR, →Giant. Name tags ` (Rare|Epic|Legendary)`.

**RoF2 item-ID cap = 1,048,575.** Item *links* encode the id as `%05X & 0x000FFFFF` (`common/say_link.cpp`), so ids above that wrap and link to the wrong item (the original `+1,000,000` scheme failed in-client — link resolved to a different item). Inventory/summon use full 32-bit ids, but links are the binding constraint. All tier ids stay packed under the cap (max ~820k).

**Drop mechanic** (`akk-stack/code/zone/loot.cpp`, `NPC::AddLootDrop`): one hook at the chokepoint every dropped item passes through. Base items (id < 200000) that are equippable/bags roll `Int(1,10000)`; on a hit it swaps `item2` for `GetItem(id+offset)`. Zero loot-table edits; covers all current+future NPCs. Tunable via `Zone:LootTier{Rare,Epic,Legendary}Chance` rules (1000/200/25 = 10%/2%/0.25%), added in `common/ruletypes.h`.

**Class epics** are auto-Epic: excluded from tier generation (so the hook's `GetItem` returns null → no random upgrade). Legendary epics generated explicitly at `base+800000` ×1.75, granted only by the **Legendary Ascension** quest (`akk-stack/server/quests/poknowledge/Epic_Forgemaster.pl`, NPC 999226 in PoK): carry your epic unequipped + hand in 8× *Essence of the Legend* (item 900000, ~1% global drop on lvl 55+ via `global_loot`) + 100,000pp → epic removed, legendary granted. No-drop-safe (epic detected/removed from inventory via CountItem/RemoveItem; only the tradeable essence + plat are handed in — no-drop items can't be put in a trade window).

**Deploy:** run the SQL, rebuild zone, regenerate shared memory (`./bin/shared_memory` — items are served from a shared-mem cache, so new items need it), restart all zones.

**Open item:** the user wanted item-name *text* colored blue/purple; RoF2 has no per-item name-color field and the client is read-only, so rarity is shown via name tags instead.

---

## 2026-06-22 — AA-vanishes-on-relog: REAL root cause found (load-order vs multiclass mask)

The recurring "AAs I buy disappear on zone/relog, and the points are not refunded" bug — finally the actual cause, not a symptom. Affected **every character**, not just multiclass ones (reproduced with Origin, an all-class `classes=65535` AA).

**Root cause:** the multiclass mod changed `CanUseAlternateAdvancementRank()` (aa.cpp:1635) to gate on `GetClassMask()` (the multiclass mask `m_multiclass_mask`) instead of computing the class bit inline. But `m_multiclass_mask` is **0 until `LoadMulticlassMask()` runs**, and the connect order is:

1. `OP_ZoneEntry` handler → `LoadAlternateAdvancement()` (client_packet.cpp:1536) loads each owned AA, calling `CanUseAlternateAdvancementRank()` per AA. **Mask is still 0 here.**
2. `OP_ClientReady` → `CompleteConnect` → `SendZoneInPackets()` → `LoadMulticlassMask()` (client.cpp:841). Too late.

With a 0 mask, `a->classes & 0 == 0` → `CanUse` returns false for **every** AA → `LoadAlternateAdvancement` (aa.cpp:1511) silently skips it. The AA isn't loaded into memory; the `character_alternate_abilities` row survives (so the point still reads as spent) but the ability is gone and the point is never refunded. At *purchase* time the mask was already populated (player fully connected), so buying worked — the asymmetry that made it look intermittent.

**Fix:** call `LoadMulticlassMask()` immediately before `LoadAlternateAdvancement()` in the ZoneEntry handler (client_packet.cpp, right after `ReloadExpansionProfileSetting()`). Rebuilt zone, restarted all zones.

**Self-healing:** previously-dropped AAs were never deleted from `character_alternate_abilities` (SaveAA's `ReplaceMany` doesn't delete unlisted rows), so with the correct mask they reload on the next zone-in and the points reconcile.

**Latent issue left as-is:** `LoadAlternateAdvancement` still *drops* (rather than refunds) any AA that genuinely fails `CanUse` (e.g. a real expansion mismatch), losing the points. Not hit by normal play now that the mask is correct; revisit if an expansion-gated AA ever legitimately fails.

---

## 2026-06-22 — Multiclass vendors reworked: 4 archetypes, restocked, relocated, Sphinx Chronicler

Replaced the 3 "Keeper" spell vendors with **4 archetype vendors** clustered at the Crescent Reach stone in PoK, and gave the Chronicler a Sphinx model.

- **NPCs 999221–999224** redefined as Arcane / Divine / Martial / Stalwart Loremaster (Caster / Priest / Melee / Tank). 999224's `npc_types` row had been deleted in the earlier cleanup — recreated, plus its spawngroup/spawnentry/spawn2.
- **Placement:** all 5 NPCs (4 vendors + Chronicler 999220) moved to a cluster around (-118, 30, -156.87), Turd's loc by the Crescent Reach stone. PoK floor z = -156.87.
- **Chronicler model → race 21 (King Xorbb / Beholder eye)**, size 8. (First tried race 86 Sphinx, but it's invisible without Luclin models on; Xorbb is a classic model that renders on old graphics.)
- **Bag vendor** added: NPC 999225 "Bartholomew Packwell", merchant 99225 — stocks one container of each distinct slot size 8→40 (best per size: Giant bagsize, highest weight-reduction). 22 bags.
- Cluster final position: just south of Mister Magelo (202388) at y≈248–264, z=-125, clear of the tree.

**Vendor restock — root cause the vendors were empty:** the GM tool's `/api/vendors/refresh` (`eq-solo-gm/api/server.cjs`) queries `items.spellid` and `items.expansion`, **neither of which exists in this DB**. The scribable spell id is in `items.scrolleffect`; there is no `items.expansion` column. So the endpoint errored every call and never stocked anything. Restocked directly in SQL using `scrolleffect`, gated by spells_new scribe level ≤ 60 (server is expansion 1 / Kunark):

| Vendor | merchantid | classBits | items |
|---|---|---|---|
| Caster (Nec/Wiz/Mag/Enc) | 99221 | 15360 | 1113 |
| Priest (Clr/Dru/Shm) | 99222 | 546 | 685 |
| Melee (Mnk/Rog/Ber/Brd/Rng/Bst) | 99223 | 49608 | 358 |
| Tank (War/Pal/SK) | 99224 | 21 | 237 |

Pure-melee classes (War/Mnk/Rog/Ber) have no scribable spells at exp 1, so Melee stocks Brd/Rng/Bst and Tank stocks Pal/SK.

**Gotcha — merchant NPCs need class 41.** An NPC is only right-clickable to shop if `npc_types.class = 41` (Merchant); `merchant_id` alone just links the inventory. The vendors were initially given their archetype classes (12/2/7/1) and couldn't be opened — fixed to class 41. (Also: npc_types/merchantlist/quest scripts are cached at zone boot, so changes to them need a full zone *restart*, not `#repop`. And dynamic-pool zones run as a bare `bin/zone` with no zone name in the command line — find the live one via its log filename `<zone>_..._<PID>.log`, not `pgrep -f "zone poknowledge"`.)

Full reproducible setup is in `eq-solo-gm/scripts/multiclass_setup.sql` (rewritten sections 2/3/5/6). **`/api/vendors/refresh` in the GM tool is still broken** (wrong column names) — left as a separate TODO.

Apply: changes are live in the DB; `#repop` PoK to spawn/move the NPCs.

---

## 2026-06-22 — Moved ftp-quests passive port range off Hyper-V reserved range

`docker-compose.yml` — `ftp-quests` passive FTP ports moved `30000-30049` → `21000-21049` (both `FTP_PASSIVE_PORTS` env and the published port mapping; they must match). Control port stays 21, so FTP clients need no change.

**Why:** after a host reboot, Windows `winnat` reserved the dynamic range 29995–30194, which overlapped the old passive range. Symptom: `make up`/`docker compose up` aborts with `ports are not available: ... bind: An attempt was made to access a socket in a way forbidden by its access permissions` on a port like 30040, and the abort also skips any services compose hadn't started yet (phpmyadmin, peq-editor → their nginx proxies then crash-loop with `host not found in upstream`).

**Gotcha:** Hyper-V/WSL dynamic port reservations shift on every reboot and live in the ~29995–50000 area. Keep host port mappings below that (21xxx is safe). Check current reservations with `netsh int ipv4 show excludedportrange protocol=tcp`. Bouncing `winnat` (`net stop winnat && net start winnat`, elevated) frees them temporarily but the conflict recurs next reboot — moving the port is the durable fix.

---

## 2026-06-22 — AA-vanishes-on-relog: root cause was stale zone processes

The recurring "purchased AA disappears after I zone/relog" bug was **not** a code bug — the `LoadMulticlassMask` 0-indexed fix (`1 << (GetClass()-1)`) was already correct in source and in the latest zone binary (built 15:33). The problem: several zone processes (qeynos, commons, freporte, freportw, arena, + static pool) were still running from 15:28 — *before* the rebuild — so they served the old buggy binary with mask `1 << GetClass()`.

A process runs whatever binary existed when it started. Killing only *some* zones after a rebuild leaves the rest stale. Whether an AA survived a relog depended entirely on which zone process the player was in: for a Paladin (class 3), buggy mask = `8`, but Paladin AAs have `classes=4` → `4 & 8 = 0` → filtered out of `SendAlternateAdvancementTable` on every zone-in. The data was never deleted from `character_alternate_abilities` — it just stopped being sent to the client.

**Fix:** killed *all* zone processes so eqlaunch respawned every one against the current binary. No code change.

**Gotcha (reinforced):** after `make zone`, you MUST kill **every** `bin/zone` process, not just the zone you're testing in. Dynamic zones already booted keep the old binary until killed. Verify with `ps -eo pid,lstart,cmd | grep '[b]in/zone'` — every start time must be *after* the binary mtime (`ls -lL --time-style=full-iso /home/eqemu/server/bin/zone`).

---

## 2026-06-22 — Multiclass System

A system that lets characters learn up to 2 additional class disciplines beyond their primary. Gated at level 20 (2nd discipline) and level 50 (3rd discipline).

### NPC hub
- **The Ancient Chronicler** (NPC ID 999220) placed in Plane of Knowledge at (-80, -25, -157)
- Companion NPCs 999201–999224 removed — all redundant with existing PoK trainers/vendors; skill training is handled programmatically by the script
- Setup script: `eq-solo-gm/scripts/multiclass_setup.sql`

### Perl quest script
**`akk-stack/server/quests/poknowledge/The_Ancient_Chronicler.pl`** — new file

Key design choices:
- Uses qglobals (`mc_class2`, `mc_class3`, scope 5 = character-permanent) as the in-session source of truth, not direct DB reads. The `character_multiclass` table is the persistent store read by the C++ zone binary on zone-in.
- `_apply_class()`: inscribes spells from `spells_new`, patches `spells_new` so base class can memorize secondary spells, expands `skill_caps`, unlocks AAs via bitmask OR on `aa_ability.classes`, trains skills to cap.
- `_revoke_slot()`: removes only spells exclusive to the revoked class (not shared with base or kept class). Promotes slot 3 → slot 2 when revoking slot 2.

**Deleted `akk-stack/server/quests/poknowledge/999220.lua`** — this ID-based Lua script took priority over the name-based Perl script for all events. EQEmu loads `<npcid>.lua` before `<NPC_Name>.pl` — if both exist, the Lua wins.

### C++ changes (akk-stack/code/zone/aa.cpp + client.h)
- `LoadMulticlassMask()` — runs on every zone-in; reads `class2`/`class3` from `character_multiclass`, builds `m_multiclass_mask` for AA display filtering.
- `SetMulticlassSlot(slot, class_id)` — persists discipline choice to `character_multiclass` (called from Lua; currently unused since Lua script was deleted, but preserved for future use).
- `GetClass2()`, `GetClass3()`, `GetClassMask()` — Lua-exposed accessors.

**Bug fixed (same session):** `LoadMulticlassMask` built the mask with `1 << GetClass()` (1-indexed), but `aa_ability.classes` uses `1 << (class_id - 1)` (0-indexed, Warrior = bit 0 = value 1). For Warrior (class=1), the mask was `2` instead of `1`.

Symptom: purchased base-class AAs disappeared on every zone. Root cause: `AutoGrantAAPoints()` runs on every zone-in, calls `SendClearPlayerAA()` + `SendAlternateAdvancementTable()`. The bad mask caused base-class AAs to fail the class filter and never be re-sent after the clear.

Fix: `1 << (GetClass() - 1)` and `1 << (m_class2 - 1)` / `1 << (m_class3 - 1)`.

To rebuild after C++ changes: `docker exec akk-stack-eqemu-server-1 bash -c "cd /home/eqemu/code/build && make -j$(nproc) zone"`. The server binary is a symlink — no copy needed. Kill zone processes after build so they restart with the new binary.

### Database schema
**`character_multiclass`** table in `peq`:
```sql
CREATE TABLE character_multiclass (
    id              INT UNSIGNED NOT NULL AUTO_INCREMENT,
    character_id    INT UNSIGNED NOT NULL,
    class2          TINYINT UNSIGNED NULL DEFAULT NULL,
    class3          TINYINT UNSIGNED NULL DEFAULT NULL,
    applied_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_character_id (character_id)
);
```
The `id` auto_increment PK is required — `SetMulticlassSlot()` in the C++ does `SELECT id FROM character_multiclass WHERE character_id = ?` to check row existence before deciding INSERT vs UPDATE. Originally created with `character_id` as PK (missing `id`), causing error 1054 on every interaction. Fixed via `ALTER TABLE`.

### Bug fix — zone crash on NULL class2/class3
`LoadMulticlassMask()` in `aa.cpp` called `Strings::ToUnsignedInt(row[N])` without checking for null. When `class2` or `class3` is SQL NULL (valid state for a character with only one discipline set), `row[N]` returns `nullptr`, and constructing a `std::string` from null throws `std::logic_error` → `std::terminate`. Fixed with null checks: `row[N] ? Strings::ToUnsignedInt(row[N]) : 0`. Also patched existing rows: `UPDATE character_multiclass SET class3 = 0 WHERE class3 IS NULL`.

### Gotchas discovered
1. **EQEmu script priority**: `<npcid>.lua` always loads before `<NPC_Name>.pl`. If both exist for the same NPC, the Lua handles all events.
2. **`spawn2` has no `enabled` column** in this EQEmu version. Omit it from INSERTs.
3. **`character_spells` column is `spell_id`**, not `spellid`.
4. **`aa_ability.classes` is 0-indexed**: Warrior (class 1) = bit 0 = value 1; Cleric (class 2) = bit 1 = value 2. Use `1 << (class_id - 1)` in both Perl and C++.
5. **C++ zone binary auto-initializes `character_multiclass` rows** on player zone-in (via `LoadMulticlassMask` + `SetMulticlassSlot`). Table schema must match what the binary expects or every zone-in produces SQL errors.

---

## 2026-06-22 — AA window class prefix (issue #4)

`akk-stack/server/quests/poknowledge/The_Ancient_Chronicler.pl`

When a player learns a secondary/tertiary discipline, AA abilities that are newly unlocked for their base class get their names prefixed with the source class abbreviation — e.g., `[NEC] Lich Form`, `[WIZ] Mana Burn`. The prefix appears in the Title column of the AA window.

- Added `%CLASS_ABBREV` hash (traditional EQ 3-letter codes: WAR, CLR, SHD, SHM, etc.)
- In `_apply_class()`: prefix UPDATE runs **before** the classes bitmask expansion so the `(classes & base_bit) = 0` condition still identifies newly-unlocked AAs. `NOT LIKE "$prefix%"` guard prevents double-prefix on re-application.
- Prefixes are NOT stripped on revoke — the AAs remain accessible after revoke and the prefix still accurately indicates origin class.

The RoF2 client binary has no EQType or mechanism for a dynamic "Class" column, so modifying `aa_ability.name` is the only server-side path to surfacing class origin in the AA window.

---

## 2026-06-22 — Discipline login notification (issue #3)

`akk-stack/server/quests/global/global_player.lua` — added to `event_connect`

On every login, if the character has any secondary/tertiary disciplines set in qglobals (`mc_class2`, `mc_class3`), a yellow chat message lists all active disciplines:
`Active disciplines: Warrior (Primary) | Necromancer (Secondary) | Wizard (Tertiary)`

No client XML changes required — uses existing qglobals set by The Ancient Chronicler. The character window in RoF2 has no EQType binding for secondary/tertiary class data; the client binary is fixed and can't be modified, so a login message is the cleanest non-invasive alternative.

---

## 2026-06-22 — Instance system (issue #1)

`eq-solo-gm/scripts/instance_keeper_setup.sql` — NPC types, spawngroups, spawn2 for 7 starter dungeons (befallen, unrest, highkeep, najena, cazicthule, permafrost, soldungb).

`akk-stack/server/quests/global/Instance_Keeper.pl` — single generic script used by all Instance Keeper NPCs. NPC's `lastname` field stores the target zone short name. Handles: hail (status + options), enter (create if needed + move), join (follow group leader's instance), reset (popup confirm → destroy + recreate), status (remaining time).

Key Perl API used: `quest::CreateInstance`, `quest::DestroyInstance`, `quest::GetInstanceIDByCharID`, `quest::AssignToInstance`, `quest::AssignToInstanceByCharID`, `quest::MovePCInstance`, `quest::GetInstanceTimerByID`.

Group behavior: leader says 'enter' → all online group members are assigned to the same instance and notified via Message(). Non-leaders say 'join' to teleport in.

Instances use version=1, duration=43200s (12h). Placement coordinates are pulled from `zone.safe_x/y/z` as a starting point — adjust per zone with `/loc` in-game.

---

## 2026-06-22 — Bard songs permanent (issue #5)

`eq-solo-gm/scripts/bard_songs_permanent.sql` — new file

Updated 430 bard beneficial buff spells in `spells_new` to `buffdurationformula = 50` (DF_Permanent). Targets spells where `classes8 > 0 AND classes8 < 255 AND buffdurationformula != 0 AND goodEffect = 1`. Skips DDs, debuffs, charm, and mez (goodEffect = 0). Script is idempotent — already-permanent spells are excluded.

No zone restart required — spell data is read fresh per cast.

---

## 2026-06-22 — pok_attunement_setup.sql fixes

`eq-solo-gm/scripts/pok_attunement_setup.sql` corrected to match actual DB schema:
- `spells_new` column names: `GoodEffect` → `goodEffect`, `base1` → `effect_base_value1`, `limit1` → `effect_limit_value1`; added missing string columns (`you_cast`, `other_casts`, `cast_on_you`, `cast_on_other`, `spell_fades`, `descnum`, `typedescnum`, `effectdescnum`, `effectdescnum2`)
- `aa_ability` INSERT: added `deities`, `charges`, `first_rank_id`, `enabled`, `reset_on_death`, `auto_grant_enabled`; removed legacy columns
- `aa_ranks` INSERT: removed `aa_id`, `passive`, `total_cost`, `rank`; added `prev_id`, `next_id`
