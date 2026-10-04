-- REVIEW ONLY: apply this change set through NPC Admin for drift checks, backup and atomic rollback.

-- These statements are documentation, not a standalone deployment script.

UPDATE `spawn2` SET `x` = -180 WHERE `id` <=> 6897 AND `spawngroupID` <=> 712 AND `zone` <=> CONVERT(X'65636f6d6d6f6e73' USING utf8mb4) AND `version` <=> 0 AND `x` <=> -141 AND `y` <=> -1677 AND `z` <=> 3.75 AND `heading` <=> 208 AND `respawntime` <=> 640 AND `variance` <=> 0 AND `pathgrid` <=> 0 AND `path_when_zone_idle` <=> 0 AND `_condition` <=> 0 AND `cond_value` <=> 1 AND `animation` <=> 0 AND `min_expansion` <=> -1 AND `max_expansion` <=> -1 AND `content_flags` <=> NULL AND `content_flags_disabled` <=> NULL;
