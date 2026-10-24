-- Schema only; disabled until a paired, verified activation.
CREATE TABLE nightcap_ashen_state (
 id TINYINT UNSIGNED PRIMARY KEY, revision BIGINT UNSIGNED NOT NULL,
 enabled TINYINT UNSIGNED NOT NULL DEFAULT 0, CHECK(id=1 AND enabled IN (0,1))
) ENGINE=InnoDB;
INSERT INTO nightcap_ashen_state VALUES(1,2026102401,0);
CREATE TABLE nightcap_ashen_characters (
 character_id INT UNSIGNED PRIMARY KEY, progress INT UNSIGNED NOT NULL DEFAULT 0,
 accepted_at INT UNSIGNED NOT NULL, completed_at INT UNSIGNED NOT NULL DEFAULT 0,
 helmet_drop_id CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
 UNIQUE KEY helmet_receipt(helmet_drop_id), CHECK(progress<8192)
) ENGINE=InnoDB;
