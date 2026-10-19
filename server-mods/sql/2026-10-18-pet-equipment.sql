-- Candidate only. Apply in stopped maintenance after backup and schema preflight.
-- All existing slot IDs and complete inventory-compatible rows remain untouched.
ALTER TABLE character_pet_armor
  DROP CONSTRAINT pet_armor_slot,
  ADD CONSTRAINT pet_armor_slot CHECK (slot_id BETWEEN 0 AND 21);
-- Capacity and two-hand exclusions are validated under per-class row/range locks
-- by the paired zone. Do not start the old binary while new locations are owned.
