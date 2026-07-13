-- =============================================================================
-- Multiclass AA static labels — bake [ABBR] class tags into aa_ability.name ONCE.
--
-- WHY: AA names are cached in zone memory at boot, so per-selection labelling only
-- showed up after `#reload aa` — not viable for non-GM players. Instead we label
-- every SINGLE-CLASS AA once with its class tag. The tags are then permanent and
-- global; any player sees their class's AAs already tagged (the per-character mask
-- decides which AAs they see — CanUse). The Chronicler no longer touches names at
-- all (pure mask-based access => clean revoke).
--
-- Only AAs usable by exactly ONE class are tagged (classes == a single class bit).
-- Shared / general AAs (multi-class) stay untagged.
--
-- Idempotent: strips any existing [ABBR] prefix first.
-- Run once, then restart zones (or `#reload aa`).
-- =============================================================================

-- 1. strip any existing [ABBR] prefixes (from the old per-selection labelling)
UPDATE aa_ability
SET name = REGEXP_REPLACE(name, '^\\[[A-Z]{3}\\] ', '')
WHERE name REGEXP '^\\[[A-Z]{3}\\] ';

-- 2. tag single-class AAs (classes == one class bit). bit = 1 << (class_id - 1).
UPDATE aa_ability SET name = CONCAT('[WAR] ', name) WHERE classes = 1;
UPDATE aa_ability SET name = CONCAT('[CLR] ', name) WHERE classes = 2;
UPDATE aa_ability SET name = CONCAT('[PAL] ', name) WHERE classes = 4;
UPDATE aa_ability SET name = CONCAT('[RNG] ', name) WHERE classes = 8;
UPDATE aa_ability SET name = CONCAT('[SHD] ', name) WHERE classes = 16;
UPDATE aa_ability SET name = CONCAT('[DRU] ', name) WHERE classes = 32;
UPDATE aa_ability SET name = CONCAT('[MNK] ', name) WHERE classes = 64;
UPDATE aa_ability SET name = CONCAT('[BRD] ', name) WHERE classes = 128;
UPDATE aa_ability SET name = CONCAT('[ROG] ', name) WHERE classes = 256;
UPDATE aa_ability SET name = CONCAT('[SHM] ', name) WHERE classes = 512;
UPDATE aa_ability SET name = CONCAT('[NEC] ', name) WHERE classes = 1024;
UPDATE aa_ability SET name = CONCAT('[WIZ] ', name) WHERE classes = 2048;
UPDATE aa_ability SET name = CONCAT('[MAG] ', name) WHERE classes = 4096;
UPDATE aa_ability SET name = CONCAT('[ENC] ', name) WHERE classes = 8192;
UPDATE aa_ability SET name = CONCAT('[BST] ', name) WHERE classes = 16384;
UPDATE aa_ability SET name = CONCAT('[BER] ', name) WHERE classes = 32768;

-- check: tagged single-class vs untagged shared
-- SELECT (SELECT COUNT(*) FROM aa_ability WHERE name LIKE '[%] %') AS tagged,
--        (SELECT COUNT(*) FROM aa_ability WHERE name NOT LIKE '[%] %') AS untagged;
