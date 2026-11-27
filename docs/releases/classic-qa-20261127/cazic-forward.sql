UPDATE npc_types
SET level = 55, hp = 24000, mindmg = 85, maxdmg = 218,
    attack_delay = 32, hp_regen_rate = 13, AC = 397, ATK = 0, Accuracy = 0
WHERE id = 72003 AND name = 'Cazic_Thule' AND class = 5
  AND npc_spells_id = 116 AND loottable_id = 291 AND hp_regen_per_second = 0
  AND level = 70 AND hp = 451000 AND mindmg = 223 AND maxdmg = 603
  AND attack_delay = 13 AND hp_regen_rate = 194 AND AC = 504 AND ATK = 100 AND Accuracy = 100;
