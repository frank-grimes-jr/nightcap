-- #16: one consistent, read-only snapshot; no character identifiers exported.
START TRANSACTION WITH CONSISTENT SNAPSHOT, READ ONLY;
SELECT 'abilities', JSON_OBJECT('id', id, 'first_rank_id', first_rank_id,
    'enabled', enabled) FROM aa_ability ORDER BY id;
SELECT 'ranks', JSON_OBJECT('id', id, 'title_sid', title_sid,
    'next_id', next_id) FROM aa_ranks ORDER BY id;
-- Saved aa_id is a FIRST RANK ID, not aa_ability.id. Count all saved rows,
-- including grants/zero-charge rows, rather than assuming every row was paid.
SELECT 'ownership', JSON_OBJECT('aa_id', aa_id, 'saved_rows', COUNT(*))
    FROM character_alternate_abilities GROUP BY aa_id ORDER BY aa_id;
SELECT 'summary', JSON_OBJECT('abilities', (SELECT COUNT(*) FROM aa_ability),
    'ranks', (SELECT COUNT(*) FROM aa_ranks),
    'ownership', (SELECT COUNT(DISTINCT aa_id) FROM character_alternate_abilities));
COMMIT;
