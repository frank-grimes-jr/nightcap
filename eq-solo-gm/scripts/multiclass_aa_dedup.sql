-- =============================================================================
-- Multiclass AA dedup: collapse duplicate-name General/Archetype AA families
--
-- Live EQ defines some abilities (Silent Casting, Combat Fury, ...) as SEPARATE
-- aa_ability rows per class group, with different rank chains. Single-class
-- characters only ever see one variant; a multiclass mask spanning groups sees
-- several -> duplicate entries in the General/Archetype tabs.
--
-- Strategy (per duplicate TRIM(name) family within type 1/2, enabled=1):
--   winner = variant with the LONGEST rank chain (tie: lowest id)
--   winner.classes = BIT_OR of the whole family (anyone who saw any variant
--                    sees the winner)
--   losers.enabled = 0 (rank chains left intact in aa_ranks for revert)
--   purchases (character_alternate_abilities keyed by first_rank_id) migrate
--   loser -> winner; if a character owns BOTH variants, keep the higher rank
--   (the ON DUPLICATE KEY here is deliberate merge semantics, not collision
--   masking; the only known case is one Armor of Wisdom overlap).
--
-- Revert data: aa_dedup_migration (permanent table) records every change.
-- Idempotent: after a run, losers are disabled -> no family has 2+ enabled
-- rows -> a second run selects nothing.
--
-- Apply: docker exec -i akk-stack-mariadb-1 mysql -ueqemu -peqemu peq < multiclass_aa_dedup.sql
-- Then restart all zones (aa_ability loads per-zone at boot).
-- =============================================================================

-- Rank chain lengths for all enabled General/Archetype abilities
DROP TABLE IF EXISTS scratch_aa_chain;
CREATE TABLE scratch_aa_chain AS
WITH RECURSIVE walk AS (
    SELECT a.id AS ab, a.first_rank_id AS rid, 1 AS d
    FROM aa_ability a
    WHERE a.enabled = 1 AND a.type IN (1,2)
    UNION ALL
    SELECT w.ab, r.next_id, w.d + 1
    FROM walk w JOIN aa_ranks r ON r.id = w.rid
    WHERE r.next_id > 0
)
SELECT ab, MAX(d) AS len FROM walk GROUP BY ab;

-- Duplicate families, ranked: rn=1 is the winner
DROP TABLE IF EXISTS scratch_aa_family;
CREATE TABLE scratch_aa_family AS
SELECT * FROM (
    SELECT TRIM(a.name) AS fam, a.id, a.first_rank_id, a.classes, c.len,
           ROW_NUMBER() OVER (PARTITION BY TRIM(a.name) ORDER BY c.len DESC, a.id ASC) AS rn,
           COUNT(*)     OVER (PARTITION BY TRIM(a.name)) AS fam_size
    FROM aa_ability a JOIN scratch_aa_chain c ON c.ab = a.id
    WHERE a.enabled = 1 AND a.type IN (1,2)
) x WHERE x.fam_size >= 2;

-- Permanent migration/revert log
CREATE TABLE IF NOT EXISTS aa_dedup_migration (
    applied_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    family            VARCHAR(128),
    loser_id          INT,
    loser_first_rank  INT,
    loser_classes     INT,
    winner_id         INT,
    winner_first_rank INT,
    winner_old_classes INT,
    winner_new_classes INT
);

INSERT INTO aa_dedup_migration
    (family, loser_id, loser_first_rank, loser_classes,
     winner_id, winner_first_rank, winner_old_classes, winner_new_classes)
SELECT l.fam, l.id, l.first_rank_id, l.classes,
       w.id, w.first_rank_id, w.classes, u.mask
FROM scratch_aa_family l
JOIN scratch_aa_family w ON w.fam = l.fam AND w.rn = 1
JOIN (SELECT fam, BIT_OR(classes) AS mask FROM scratch_aa_family GROUP BY fam) u ON u.fam = l.fam
WHERE l.rn > 1;

-- Winner absorbs the family's union class mask
UPDATE aa_ability a
JOIN scratch_aa_family w ON w.id = a.id AND w.rn = 1
JOIN (SELECT fam, BIT_OR(classes) AS mask FROM scratch_aa_family GROUP BY fam) u ON u.fam = w.fam
SET a.classes = u.mask;

-- Migrate purchases loser -> winner (deliberate merge: keep higher rank)
INSERT INTO character_alternate_abilities (id, aa_id, aa_value, charges)
SELECT caa.id, w.first_rank_id, caa.aa_value, caa.charges
FROM character_alternate_abilities caa
JOIN scratch_aa_family l ON l.first_rank_id = caa.aa_id AND l.rn > 1
JOIN scratch_aa_family w ON w.fam = l.fam AND w.rn = 1
ON DUPLICATE KEY UPDATE aa_value = GREATEST(character_alternate_abilities.aa_value, VALUES(aa_value));

DELETE caa FROM character_alternate_abilities caa
JOIN scratch_aa_family l ON l.first_rank_id = caa.aa_id AND l.rn > 1;

-- Disable losers (their aa_ranks chains stay in place for revert)
UPDATE aa_ability a JOIN scratch_aa_family l ON l.id = a.id AND l.rn > 1
SET a.enabled = 0;

DROP TABLE IF EXISTS scratch_aa_chain;
DROP TABLE IF EXISTS scratch_aa_family;

-- Verification: both must return 0 rows
SELECT 'dup_families_remaining' AS check_name, TRIM(name) n, COUNT(*) c
FROM aa_ability WHERE enabled = 1 AND type IN (1,2)
GROUP BY TRIM(name) HAVING c > 1;
SELECT 'orphaned_purchases' AS check_name, caa.id, caa.aa_id
FROM character_alternate_abilities caa
JOIN aa_ability a ON a.first_rank_id = caa.aa_id
WHERE a.enabled = 0;
