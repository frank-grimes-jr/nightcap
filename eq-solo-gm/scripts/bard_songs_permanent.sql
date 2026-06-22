-- =============================================================================
-- Bard Songs — Permanent Duration
--
-- Makes all beneficial bard buff spells permanent (no expiry).
-- Targets only spells the bard class can use (classes8 > 0 and < 255),
-- with a buff duration, that are beneficial — skips DDs, debuffs, charm, mez.
--
-- Run against the `peq` database:
--   docker exec -i akk-stack-mariadb-1 mysql -ueqemu -peqemu peq < bard_songs_permanent.sql
--
-- Safe to re-run (idempotent — already-permanent spells are excluded).
-- =============================================================================

UPDATE spells_new
SET buffdurationformula = 50, buffduration = 0
WHERE classes8 > 0 AND classes8 < 255
  AND buffdurationformula != 0
  AND buffdurationformula != 50
  AND goodEffect = 1;
