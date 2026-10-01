-- Retain all history, owned items and spell definitions. Reload tasks after applying.
START TRANSACTION;
UPDATE nightcap_epic05_control SET enabled=0 WHERE id=1;
UPDATE tasks SET enabled=0 WHERE id BETWEEN 9500 AND 9507;
COMMIT;
