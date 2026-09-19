-- Additive schema only. Back up PEQ before deployment. Do not drop this table
-- on rollback: its rows own real player items, which must first be reclaimed.
-- LIKE preserves the exact live inventory types, charset and item-instance
-- fields. Refuse an existing table rather than silently accepting an old schema.
CREATE TABLE character_pet_armor LIKE inventory;
ALTER TABLE character_pet_armor
  ADD COLUMN pet_class TINYINT UNSIGNED NOT NULL,
  DROP PRIMARY KEY,
  ADD PRIMARY KEY (character_id, pet_class, slot_id),
  ADD CONSTRAINT pet_armor_class CHECK (pet_class BETWEEN 1 AND 16),
  ADD CONSTRAINT pet_armor_slot CHECK (slot_id IN (2,17,7,9,12,18,19,20));
