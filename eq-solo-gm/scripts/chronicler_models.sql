-- =============================================================================
-- Chronicler crew models (ADR 0003)
--
-- Constraint discovered the hard way: PoK only renders races whose model
-- archives are globally loaded (client Resources/GlobalLoad.txt) or shipped in
-- the zone's own files. Race 21 (evil eye) is neither -> silent human fallback,
-- which is why The Chronicler never showed as the eye. Every race below is
-- verified to render in poknowledge (existing spawn2 NPCs use it).
--
-- 999220 Chronicler   -> 330 PoK library guardian construct (the giant animated
--                        statues of the Great Library itself), size 9
-- 999221 Arcane       -> 457 clockwork (a ticking arcane engine), size 5
-- 999222 Divine       -> 495 Herald of Druzzil Ro (goddess of magic's own), size 6
-- 999223 Martial      -> 14  werewolf (feral discipline), size 6
-- 999224 Stalwart     -> 522 Drakkin (dragonblood armored), size 6
-- 999225 Packwell     -> 433 Gigglegibber goblin (a merchant goblin!), size 4
-- 999226 Forgemaster  -> 75  elemental (texture 1 = fire; adjust via #texture
--                        live if this build maps elements differently), size 7
--
-- Deploy: apply, then RESTART the PoK zone process (npc_types is cached at
-- boot; #repop is not enough).
-- =============================================================================

UPDATE npc_types SET race = 330, gender = 2, texture = 0, size = 9   WHERE id = 999220;
UPDATE npc_types SET race = 457, gender = 2, texture = 0, size = 5   WHERE id = 999221;
UPDATE npc_types SET race = 495, gender = 2, texture = 0, size = 6   WHERE id = 999222;
UPDATE npc_types SET race = 14,  gender = 2, texture = 0, size = 6   WHERE id = 999223;
UPDATE npc_types SET race = 522, gender = 0, texture = 3, size = 6   WHERE id = 999224;
UPDATE npc_types SET race = 433, gender = 2, texture = 0, size = 4   WHERE id = 999225;
UPDATE npc_types SET race = 75,  gender = 2, texture = 1, size = 7   WHERE id = 999226;

SELECT id, name, race, gender, texture, size FROM npc_types WHERE id BETWEEN 999220 AND 999226;
