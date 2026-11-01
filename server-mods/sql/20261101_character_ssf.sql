-- Solo self-found (ADR 0074). A row means the character is SSF; deleting it
-- (GM only) restores normal play after the character zones.
-- Fail on an existing table instead of silently adopting an unknown schema.
-- No inventory, loot, rule or era changes.
CREATE TABLE character_ssf (
    character_id INT UNSIGNED NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (character_id)
) ENGINE=InnoDB;
