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
UPDATE zone SET bypass_expansion_check = 1 WHERE short_name = 'poknowledge';

-- =============================================================================
-- 2. Create the teleport spell.
--
--    Detects the correct teleport SPA from existing spells rather than
--    hardcoding a version-dependent value. Defaults to SPA 46 if none found.
--
--    All class columns are 255 (cannot memorize) — AA-only, never appears
--    in spellbook or vendor lists.
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
    (id, name, targettype, skill, goodEffect, Activated,
     cast_time, recovery_time, recast_time,
     effectid1, effect_base_value1, effect_limit_value1, max1,
     effectid2, effectid3, effectid4, effectid5, effectid6,
     effectid7, effectid8, effectid9, effectid10, effectid11, effectid12,
     teleport_zone,
     you_cast, other_casts, cast_on_you, cast_on_other, spell_fades,
     descnum, typedescnum, effectdescnum, effectdescnum2,
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
    '', '', 'You are transported to the Plane of Knowledge.', '', '',
    0, 0, 0, 0,
    255, 255, 255, 255,
    255, 255, 255, 255,
    255, 255, 255, 255,
    255, 255, 255, 255;

-- =============================================================================
-- 3. Create the AA ability.
--
--    category -1   = General tab
--    classes 65535 = all 16 classes (bitmask, all bits set)
--    races   65535 = all races
--    type 0        = activated ability
--    first_rank_id = set to the rank row we create below (22200)
-- =============================================================================

INSERT INTO aa_ability
    (id, name, category, classes, races, drakkin_heritage, deities,
     status, type, charges, grant_only, first_rank_id, enabled,
     reset_on_death, auto_grant_enabled)
VALUES
    (2220, 'Ancient Attunement', -1, 65535, 65535, 127, 131071,
     0, 0, 0, 0, 22200, 1,
     0, 0)
ON DUPLICATE KEY UPDATE
    name          = VALUES(name),
    classes       = VALUES(classes),
    first_rank_id = VALUES(first_rank_id),
    enabled       = 1;

-- =============================================================================
-- 4. Create AA rank 1.
--
--    cost 0        = free (no AA points required)
--    level_req 1   = available from level 1
--    spell 99001   = the teleport spell above
--    spell_type 1  = activated (clickable)
--    recast_time   = 600 seconds (10 minutes)
--    prev_id -1    = no prerequisite rank
--    next_id -1    = no further ranks
-- =============================================================================

INSERT INTO aa_ranks
    (id, upper_hotkey_sid, lower_hotkey_sid, title_sid, desc_sid,
     cost, level_req, spell, spell_type, recast_time, expansion,
     prev_id, next_id)
VALUES
    (22200, -1, -1, -1, -1,
     0, 1, 99001, 1, 600, 0,
     -1, -1)
ON DUPLICATE KEY UPDATE
    spell      = VALUES(spell),
    level_req  = VALUES(level_req),
    cost       = VALUES(cost),
    recast_time = VALUES(recast_time);

-- =============================================================================
-- Verification queries (run manually to confirm):
--   SELECT id, name, teleport_zone, effectid1 FROM spells_new WHERE id = 99001;
--   SELECT id, name, classes, first_rank_id FROM aa_ability WHERE id = 2220;
--   SELECT id, level_req, spell, recast_time FROM aa_ranks WHERE id = 22200;
--   SELECT short_name, bypass_expansion_check FROM zone WHERE short_name = 'poknowledge';
-- =============================================================================
