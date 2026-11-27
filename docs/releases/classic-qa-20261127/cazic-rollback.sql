UPDATE npc_types
SET level = 70, hp = 451000, mindmg = 223, maxdmg = 603,
    attack_delay = 13, hp_regen_rate = 194, AC = 504, ATK = 100, Accuracy = 100
WHERE id = 72003 AND name = 'Cazic_Thule' AND class = 5
  AND npc_spells_id = 116 AND loottable_id = 291 AND hp_regen_per_second = 0
  AND level = 55 AND hp = 24000 AND mindmg = 85 AND maxdmg = 218
  AND attack_delay = 32 AND hp_regen_rate = 13 AND AC = 397 AND ATK = 0 AND Accuracy = 0;
