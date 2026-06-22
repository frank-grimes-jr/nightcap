# CHANGES

Running log of significant changes to this repo — schema migrations, C++ patches, quest script additions, and anything with gotchas worth remembering. Most recent first.

---

## 2026-06-22 — Multiclass System

A system that lets characters learn up to 2 additional class disciplines beyond their primary. Gated at level 20 (2nd discipline) and level 50 (3rd discipline).

### NPC hub
- **The Ancient Chronicler** (NPC ID 999220) placed in Plane of Knowledge
- Four companion NPCs (999221–999224): spell vendors by archetype (arcane, priest, martial) and a provisions keeper
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

### Gotchas discovered
1. **EQEmu script priority**: `<npcid>.lua` always loads before `<NPC_Name>.pl`. If both exist for the same NPC, the Lua handles all events.
2. **`spawn2` has no `enabled` column** in this EQEmu version. Omit it from INSERTs.
3. **`character_spells` column is `spell_id`**, not `spellid`.
4. **`aa_ability.classes` is 0-indexed**: Warrior (class 1) = bit 0 = value 1; Cleric (class 2) = bit 1 = value 2. Use `1 << (class_id - 1)` in both Perl and C++.
5. **C++ zone binary auto-initializes `character_multiclass` rows** on player zone-in (via `LoadMulticlassMask` + `SetMulticlassSlot`). Table schema must match what the binary expects or every zone-in produces SQL errors.

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
