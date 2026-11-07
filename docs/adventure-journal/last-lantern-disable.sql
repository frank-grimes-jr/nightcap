-- Forward recovery: retain the personal-item native policy and all player state.
START TRANSACTION;
UPDATE nightcap_lantern_control SET enabled=0 WHERE id=1;
UPDATE nightcap_epic05_control SET enabled=0 WHERE id=1;
UPDATE tasks SET enabled=0 WHERE id BETWEEN 9500 AND 9515;
COMMIT;
