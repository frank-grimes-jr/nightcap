-- Candidate only: back up PEQ and confirm all three names are unused before applying.
-- Fail on an existing table instead of silently adopting an unknown schema.
-- No loot, inventory, drop-rate, character-power or era changes.
CREATE TABLE character_advloot_settings (
    character_id INT UNSIGNED NOT NULL,
    settings INT UNSIGNED NOT NULL DEFAULT 7,
    PRIMARY KEY (character_id),
    CONSTRAINT advloot_settings_bits CHECK (settings <= 63)
) ENGINE=InnoDB;

CREATE TABLE character_advloot_filters (
    character_id INT UNSIGNED NOT NULL,
    item_id INT UNSIGNED NOT NULL,
    filter TINYINT UNSIGNED NOT NULL,
    PRIMARY KEY (character_id, item_id),
    CONSTRAINT advloot_filter_value CHECK (filter BETWEEN 0 AND 4),
    CONSTRAINT advloot_filter_item CHECK (item_id > 0)
) ENGINE=InnoDB;

-- A physical drop's receipt is committed together with its inventory rows.
-- Retain receipts: saved corpse state may outlive the process that awarded it.
CREATE TABLE character_advloot_claims (
    drop_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    character_id INT UNSIGNED NOT NULL,
    item_id INT UNSIGNED NOT NULL,
    charges INT NOT NULL,
    inventory_after MEDIUMTEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (drop_id),
    KEY character_receipts (character_id, created_at)
) ENGINE=InnoDB;

-- Behavior rollback: disable advanced loot while retaining a receipt-aware
-- server. Keep these tables and player preferences. A previous server that
-- ignores receipt IDs must not load an unreconciled NPC saved-state checkpoint;
-- otherwise already awarded items could reappear. Older-binary rollback needs
-- a separately reviewed saved-state reconciliation, not just a binary swap.
