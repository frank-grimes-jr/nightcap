-- Operational rollback: Combine leaves ingredients intact after this gate closes.
-- Retain box/tier definitions, player items, NPC, saved state and receipts.
UPDATE nightcap_item_upgrade_state SET enabled=0 WHERE id=1 AND revision=2026101201;
SELECT id,revision,enabled FROM nightcap_item_upgrade_state;
