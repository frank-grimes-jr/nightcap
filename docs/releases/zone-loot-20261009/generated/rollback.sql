-- Safe after player activity: retain definitions, sockets, ownership and forge receipts.
UPDATE nightcap_zone_hunt_state SET enabled=0 WHERE id=1;
-- Reload zones with the current receipt-capable binary. Never restore old player rows.
