-- =============================================================================
-- Multiclass AA cleanup — restore aa_ability to pristine classes + names
--
-- WHY: the old Ancient Chronicler script mutated the GLOBAL aa_ability table on
-- every class selection (OR-ing the base-class bit into secondary AAs, and
-- prefixing names) and revoke undid none of it. This accumulated cruft: AAs
-- over-OR'd with class bits they shouldn't have (e.g. 416 non-Paladin AAs falsely
-- became Paladin-usable), and stale/duplicate [XXX] name prefixes.
--
-- FIX: restore each STOCK AA's `classes` and `name` from the pristine PEQ dump,
-- joined on aa_ability.id. Custom AAs (not in the dump, e.g. PoK attunement) are
-- left untouched. Only `classes` and `name` are restored — `first_rank_id` is NOT
-- touched, so the aa_ability<->aa_ranks linkage (and players' purchased AAs, which
-- reference first_rank_id) stay intact.
--
-- Access to secondary-class AAs now comes purely from the per-character multiclass
-- mask (m_multiclass_mask), NOT from mutating this table. The reworked Chronicler
-- no longer OR's classes; it only adds/removes the [ABBR] label, reversibly.
--
-- RUN (from the eqemu-server container, which has the dump file + DB access):
--   mysql -uroot -p<root> -h mariadb -e "DROP DATABASE IF EXISTS aa_clean; CREATE DATABASE aa_clean;"
--   mysql -uroot -p<root> -h mariadb aa_clean < /home/eqemu/code/utils/sql/peq_aa_tables_post_rework.sql
--   mysql -uroot -p<root> -h mariadb < THIS_FILE
--   mysql -uroot -p<root> -h mariadb -e "DROP DATABASE aa_clean;"
-- Then restart zones (aa_ability is loaded per-zone from the DB at boot).
--
-- IMPORTANT: verify id-space alignment first — the de-prefixed live name must equal
-- the dump name for stock AAs (it does for this server's install). If a future
-- install uses a different AA dataset, re-verify before running.
-- =============================================================================

UPDATE peq.aa_ability a
JOIN aa_clean.aa_ability c ON a.id = c.id
SET a.classes = c.classes,
    a.name    = c.name;

-- Sanity checks (expect: 0 prefixed, custom AAs preserved):
-- SELECT COUNT(*) FROM peq.aa_ability WHERE name LIKE '[%] %';                 -- expect 0
-- SELECT COUNT(*) FROM peq.aa_ability p LEFT JOIN aa_clean.aa_ability c
--   ON p.id=c.id WHERE c.id IS NULL;                                          -- custom AAs (untouched)
