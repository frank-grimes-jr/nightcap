-- Additive candidate. Apply to the game/content database with the game stopped.
-- Plain CREATE intentionally refuses an unknown pre-existing schema. On retry,
-- inspect/reconcile the exact schema; do not drop tables containing run state.
CREATE TABLE nightcap_highkeep_state (
  id TINYINT UNSIGNED NOT NULL PRIMARY KEY,
  revision BIGINT UNSIGNED NOT NULL,
  enabled TINYINT UNSIGNED NOT NULL DEFAULT 0,
  CONSTRAINT highkeep_state_id CHECK (id=1),
  CONSTRAINT highkeep_state_enabled CHECK (enabled IN (0,1))
) ENGINE=InnoDB;
CREATE TABLE nightcap_highkeep_runs (
  run_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL PRIMARY KEY,
  alarm TINYINT UNSIGNED NOT NULL DEFAULT 0,
  rescued_at BIGINT UNSIGNED NOT NULL DEFAULT 0,
  CONSTRAINT highkeep_alarm CHECK (alarm IN (0,1))
) ENGINE=InnoDB;
INSERT INTO nightcap_highkeep_state(id,revision,enabled) VALUES (1,2026102401,0);
-- Activation after paired deployment/verification is a separate authorized step:
-- UPDATE nightcap_highkeep_state SET enabled=1 WHERE id=1 AND revision=2026102401 AND enabled=0;
-- Pause new rescue runs: set enabled=0. Existing enrolled runs continue safely.
-- Retain both tables, all earned member state and inventory receipts on rollback.
