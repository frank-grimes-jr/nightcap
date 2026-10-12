-- Only after matching native binaries/quest are installed and verified.
UPDATE nightcap_item_upgrade_state SET enabled=1 WHERE id=1 AND revision=2026101201;
SELECT id,revision,enabled FROM nightcap_item_upgrade_state;
