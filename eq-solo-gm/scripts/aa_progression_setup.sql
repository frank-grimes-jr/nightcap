-- =============================================================================
-- AA Progression Setup — Level 1 Access + Calibrated XP Rate
--
-- Goals:
--   1. All AA ranks purchasable from level 1 (level_req gating removed)
--   2. AA:ExpPerPoint tuned so level 30 LGuk grinding feels productive
--      (~20–33 kills per AA with the server's 0.65 XP multipliers)
--
-- Calibration notes:
--   • Character:ExpMultiplier = 0.65, Character:AAExpMultiplier = 0.65
--   • Level 30 red mobs in LGuk: ~1,500–2,500 XP per kill
--   • AA:ExpPerPoint = 50,000 → ~20–33 kills per AA at level 30
--   • Level 1 mobs (~15 XP/kill) → ~3,300 kills per AA (intentionally slow)
--   • Adjust AA:ExpPerPoint via GM Tool > Server Tweaks after in-game testing
--     Lower = faster AA grinding; 20,000 is fast, 100,000 is grindy
--
-- Run against the `peq` database:
--   docker exec -i akk-stack-mariadb-1 mysql -ueqemu -peqemu peq < aa_progression_setup.sql
-- =============================================================================

-- 1. Tune AA XP cost to match low-level play.
--    Default live-EQ value (23,976,503) is designed for level 65+ characters
--    earning hundreds of thousands of XP per kill in Planes of Power.
--    50,000 makes level 30 LGuk a practical grind spot.
UPDATE rule_values
SET rule_value = '50000'
WHERE rule_name = 'AA:ExpPerPoint'
  AND ruleset_id = 1;

-- 2. Remove level gates on all AA ranks.
--    The original level_req values (0–105) restrict when ranks can be purchased.
--    Setting all to 1 lets characters spend earned AA points on any rank from
--    level 1. The AA point cost per rank (aa_ranks.cost) still provides
--    progression gating, and aa_ability.classes still controls which AAs
--    appear per character class.
UPDATE aa_ranks SET level_req = 1;

-- =============================================================================
-- Verification queries (run manually to confirm):
--   SELECT rule_name, rule_value FROM rule_values
--     WHERE rule_name IN ('AA:ExpPerPoint','Character:AAExpMultiplier');
--   SELECT COUNT(*) as total, MIN(level_req) as min_req, MAX(level_req) as max_req
--     FROM aa_ranks;  -- should show min=1, max=1
-- =============================================================================
