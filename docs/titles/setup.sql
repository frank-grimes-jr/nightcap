-- Additive, disabled candidate. Run on an isolated DB first; no player backfill.
-- Reapplication preserves existing settings, awards and counters.
CREATE TABLE IF NOT EXISTS nightcap_title_settings (
  id TINYINT UNSIGNED NOT NULL PRIMARY KEY,
  catalog_version INT UNSIGNED NOT NULL,
  enabled TINYINT UNSIGNED NOT NULL DEFAULT 0
) ENGINE=InnoDB;
INSERT IGNORE INTO nightcap_title_settings(id,catalog_version,enabled) VALUES (1,1,0);

CREATE TABLE IF NOT EXISTS nightcap_title_counters (
  character_id INT UNSIGNED NOT NULL,
  counter_id INT UNSIGNED NOT NULL,
  value BIGINT UNSIGNED NOT NULL DEFAULT 0,
  PRIMARY KEY(character_id,counter_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS nightcap_title_awards (
  character_id INT UNSIGNED NOT NULL,
  title_id INT UNSIGNED NOT NULL,
  earned_at BIGINT UNSIGNED NOT NULL,
  PRIMARY KEY(character_id,title_id)
) ENGINE=InnoDB;
