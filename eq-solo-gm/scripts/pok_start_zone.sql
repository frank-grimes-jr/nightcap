-- =============================================================================
-- PoK Start Zone + Expansion Bypass
--
-- 1. Ensures all new characters spawn in Plane of Knowledge regardless of race,
--    class, or deity. Uses the zone's own safe coordinates.
-- 2. Sets PoK's bypass_expansion_check so the zone is always accessible even
--    when the server is locked to Classic/Kunark/Velious/Luclin eras.
--
-- NOTE: This only affects NEW character creation. Existing characters keep
-- their current location. They reach PoK via the Ancient Attunement AA
-- (granted on login by global_player.lua).
--
-- Run against the `peq` database:
--   docker exec -i akk-stack-mariadb-1 mysql -ueqemu -peqemu peq < pok_start_zone.sql
-- =============================================================================

-- 1. Allow PoK entry regardless of server expansion setting.
--    PoK is expansion 4 (Planes of Power). Without this, the server blocks
--    entry when CurrentExpansion < 4.
--    This is also set in pok_attunement_setup.sql — safe to run both.
UPDATE zone
SET bypass_expansion_check = 1
WHERE short_name = 'poknowledge';

-- 2. Redirect all starting zones to PoK.
--    411 rows cover every race/class/deity combination. The safe coordinates
--    come from the zone table's own safe_x/safe_y/safe_z values for poknowledge.
--    bind_id = 202 and matching bind coords set the death-bind point to PoK
--    as well, so /home also returns to PoK.
UPDATE start_zones
SET
    start_zone = 202,
    zone_id    = 202,
    x          = -285,
    y          = -148,
    z          = -159,
    heading    = 0,
    bind_id    = 202,
    bind_x     = -285,
    bind_y     = -148,
    bind_z     = -159;

-- =============================================================================
-- Verification:
--   SELECT DISTINCT start_zone, zone_id, x, y, z FROM start_zones LIMIT 3;
--   -- should all show 202 / -285 / -148 / -159
--
--   SELECT short_name, bypass_expansion_check FROM zone WHERE short_name = 'poknowledge';
--   -- should show 1
-- =============================================================================
