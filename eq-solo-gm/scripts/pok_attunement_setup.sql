-- =============================================================================
-- Ancient Attunement — PoK Recall AA
--
-- Grants all characters an AA that teleports them to Plane of Knowledge,
-- bypassing expansion locks. Auto-granted on login via global_player.lua.
--
-- Run against the `peq` database:
--   docker exec -i akk-stack-mariadb-1 mysql -ueqemu -peqemu peq < pok_attunement_setup.sql
-- =============================================================================

-- 1. Make PoK always accessible regardless of expansion lock.
--    Without this, the teleport spell itself would be blocked by the server's
--    expansion check when the destination zone's expansion > current setting.
UPDATE zone SET bypass_expansion_check = 1 WHERE short_name = 'poknowledge';

-- =============================================================================
-- 2. Create the teleport spell.
--
--    We detect the correct teleport SPA (effectid1) from existing transport
--    spells in this database rather than hardcoding a version-dependent value.
--    If no teleport spell exists (empty server), defaults to SPA 46.
--
--    All class columns are 255 (cannot memorize) — this spell is AA-only and
--    should not appear in the spellbook or vendor lists.
-- =============================================================================

SET @teleport_spa = COALESCE(
    (SELECT s.effectid1
     FROM spells_new s
     WHERE s.teleport_zone IS NOT NULL
       AND s.teleport_zone != ''
       AND s.effectid1 > 0
     LIMIT 1),
    46
);

INSERT IGNORE INTO spells_new
    (id, name, targettype, skill, GoodEffect, Activated,
     cast_time, recovery_time, recast_time,
     effectid1, base1, limit1, max1,
     effectid2, effectid3, effectid4, effectid5, effectid6,
     effectid7, effectid8, effectid9, effectid10, effectid11, effectid12,
     teleport_zone,
     classes1,  classes2,  classes3,  classes4,
     classes5,  classes6,  classes7,  classes8,
     classes9,  classes10, classes11, classes12,
     classes13, classes14, classes15, classes16)
SELECT
    99001, 'Ancient Attunement', 6, 5, 1, 1,
    5000, 1500, 600000,
    @teleport_spa, 0, 0, 0,
    254, 254, 254, 254, 254, 254, 254, 254, 254, 254, 254,
    'poknowledge',
    255, 255, 255, 255,
    255, 255, 255, 255,
    255, 255, 255, 255,
    255, 255, 255, 255;

-- =============================================================================
-- 3. Create the AA ability.
--
--    category 0 = General tab in AA window
--    classes  65535 = all 16 classes (bitmask all bits set)
--    races    65535 = all races
--    expansion 0 = Classic era (always visible)
--    spell_type 1 = activated (clickable, has recast timer)
--    spell_refresh 600 = 10-minute recast shown in UI (in seconds)
-- =============================================================================

INSERT INTO aa_ability
    (id, name, category, classes, races, drakkin_heritage, status, type,
     spell_type, spell_refresh, expansion, aa_expansion, special_category,
     sof_type, sof_cost_mod, grant_only, auto_grant, auto_grant_level,
     auto_grant_time, auto_grant_points, icon)
VALUES
    (2220, 'Ancient Attunement', 0, 65535, 65535, 255, 0, 0,
     1, 600, 0, 0, -1,
     0, 0, 0, 0, 0, 0, 0, 0)
ON DUPLICATE KEY UPDATE
    name      = VALUES(name),
    classes   = VALUES(classes),
    expansion = VALUES(expansion);

-- =============================================================================
-- 4. Create AA rank 1.
--
--    cost 0       = free (no AA points required to purchase)
--    level_req 1  = available from level 1
--    spell 99001  = the teleport spell above
--    spell_type 1 = activated (not passive)
--    recast_time  = 600 seconds (10 minutes); units may vary by EQEmu version
--    passive 0    = player must click to activate
-- =============================================================================

INSERT INTO aa_ranks
    (id, aa_id, upper_hotkey_sid, lower_hotkey_sid, title_sid, desc_sid,
     cost, level_req, spell, spell_type, recast_time, passive, total_cost,
     grant_only, expansion, rank)
VALUES
    (22200, 2220, 0, 0, 0, 0,
     0, 1, 99001, 1, 600, 0, 0,
     0, 0, 1)
ON DUPLICATE KEY UPDATE
    spell      = VALUES(spell),
    level_req  = VALUES(level_req),
    cost       = VALUES(cost);

-- =============================================================================
-- Verification queries (run manually to confirm):
--   SELECT id, name, teleport_zone, effectid1 FROM spells_new WHERE id = 99001;
--   SELECT id, name, classes, expansion FROM aa_ability WHERE id = 2220;
--   SELECT id, aa_id, level_req, spell, recast_time FROM aa_ranks WHERE id = 22200;
--   SELECT short_name, bypass_expansion_check FROM zone WHERE short_name = 'poknowledge';
-- =============================================================================
