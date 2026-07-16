-- =============================================================================
-- Chronicler crew models, take 3 (ADR 0003)
--
-- LESSON (two failures deep): a race id "existing in the zone's spawn table" is
-- NOT enough — the client needs the exact race+gender+texture(+helmtexture)
-- combo to have a model, or it silently falls back to human. (Race 21 evil eye:
-- archive not loaded in PoK at all. Race 330 gender 2: Froglok has no neutral
-- model.) The only safe source is copying the exact appearance tuple from a
-- native PoK NPC the client provably renders. Every row below is such a copy
-- (source NPC noted); only size is freely chosen.
--
-- 999220 Chronicler   <- Haunted_Jack        (82/2/0/0)   spectral haunt, size 9
-- 999221 Arcane       <- Distribution_Facilitator_XCV (457/2/0/2) clockwork, size 5
-- 999222 Divine       <- Herald_of_Druzzil_Ro (495/2/3/3) herald, size 6
-- 999223 Martial      <- Elementalist_Somata  (14/2/1/255) werewolf, size 6
-- 999224 Stalwart     <- Mercia               (522/1/1/0)  drakkin, size 6
-- 999225 Packwell     <- a_gigglegibber_goblin (433/2/0/0) goblin, size 4
-- 999226 Forgemaster  <- A_Planar_Projection  (75/2/3/3)   elemental, size 7
--
-- Deploy: apply, then RESTART the PoK zone process (npc_types cached at boot).
-- =============================================================================

UPDATE npc_types SET race = 82,  gender = 2, texture = 0, helmtexture = 0,   size = 9 WHERE id = 999220;
UPDATE npc_types SET race = 457, gender = 2, texture = 0, helmtexture = 2,   size = 5 WHERE id = 999221;
UPDATE npc_types SET race = 495, gender = 2, texture = 3, helmtexture = 3,   size = 6 WHERE id = 999222;
UPDATE npc_types SET race = 14,  gender = 2, texture = 1, helmtexture = 255, size = 6 WHERE id = 999223;
UPDATE npc_types SET race = 522, gender = 1, texture = 1, helmtexture = 0,   size = 6 WHERE id = 999224;
UPDATE npc_types SET race = 433, gender = 2, texture = 0, helmtexture = 0,   size = 4 WHERE id = 999225;
UPDATE npc_types SET race = 75,  gender = 2, texture = 3, helmtexture = 3,   size = 7 WHERE id = 999226;

SELECT id, name, race, gender, texture, helmtexture, size FROM npc_types WHERE id BETWEEN 999220 AND 999226;
