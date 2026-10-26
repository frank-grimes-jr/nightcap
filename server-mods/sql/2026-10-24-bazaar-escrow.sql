-- Additive candidate only. Run with gameplay stopped, after a fresh backup and
-- schema/preimage rehearsal. Repeated/partial installation deliberately fails.
-- Recovery preserves all owned escrow, credits and receipts; do not DROP these.
CREATE TABLE nightcap_bazaar_state (
 id TINYINT UNSIGNED NOT NULL PRIMARY KEY,
 version INT UNSIGNED NOT NULL,
 enabled TINYINT UNSIGNED NOT NULL DEFAULT 0,
 CHECK (id=1 AND version=1 AND enabled IN (0,1))
) ENGINE=InnoDB;
INSERT INTO nightcap_bazaar_state VALUES(1,1,0);
CREATE TABLE nightcap_bazaar_listings (
 id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
 seller_id INT UNSIGNED NOT NULL,
 unit_price INT UNSIGNED NOT NULL,
 quantity INT UNSIGNED NOT NULL,
 remaining INT UNSIGNED NOT NULL,
 stackable TINYINT UNSIGNED NOT NULL,
 status ENUM('active','sold','cancelled') NOT NULL DEFAULT 'active',
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 INDEX seller_status(seller_id,status,id),
 CHECK (seller_id>0 AND unit_price>0 AND quantity>0 AND remaining<=quantity),
 CHECK (stackable IN (0,1)),
 CHECK ((status='active' AND remaining>0) OR (status<>'active' AND remaining=0))
) ENGINE=InnoDB;
-- Preserve exactly the installed inventory field types. The native readiness
-- gate must authenticate the canonical 17-column inventory contract.
CREATE TABLE nightcap_bazaar_items LIKE inventory;
ALTER TABLE nightcap_bazaar_items DROP PRIMARY KEY,
 ADD COLUMN listing_id INT UNSIGNED NOT NULL FIRST,
 ADD PRIMARY KEY (listing_id,slot_id);
CREATE TABLE nightcap_bazaar_credits (
 character_id INT UNSIGNED NOT NULL PRIMARY KEY,
 copper BIGINT UNSIGNED NOT NULL DEFAULT 0,
 CHECK (copper<=9223372036854775807)
) ENGINE=InnoDB;
CREATE TABLE nightcap_bazaar_receipts (
 id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
 character_id INT UNSIGNED NOT NULL,
 listing_id INT UNSIGNED NOT NULL,
 operation TINYINT UNSIGNED NOT NULL,
 copper BIGINT UNSIGNED NOT NULL,
 created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
 INDEX character_history(character_id,id),
 INDEX listing_history(listing_id,id),
 CHECK (operation<=3)
) ENGINE=InnoDB;
