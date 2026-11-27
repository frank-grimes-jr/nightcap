-- The release operator verifies the preimage, affected row count and afterimage.
UPDATE aa_ability
SET classes = 131071
WHERE id = 2220 AND first_rank_id = 22200 AND name = 'Ancient Attunement'
  AND type = 1 AND enabled = 1 AND classes = 65535;
