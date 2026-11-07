START TRANSACTION;
UPDATE tasks SET enabled=1 WHERE id BETWEEN 9500 AND 9515;
UPDATE nightcap_epic05_control SET enabled=1 WHERE id=1 AND native_contract=1 AND catalog_version=1;
UPDATE nightcap_lantern_control SET enabled=1 WHERE id=1 AND revision=2026110701;
COMMIT;
