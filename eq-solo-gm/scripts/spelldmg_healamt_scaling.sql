-- =============================================================================
-- SpellDmg / HealAmt master output scaling — rules + dials
-- Run:  docker exec -i akk-stack-mariadb-1 mysql -ueqemu -peqemu peq < spelldmg_healamt_scaling.sql
-- Then: apply tiered_loot_setup.sql, regenerate shared memory, restart zones.
-- Spec: docs/superpowers/specs/2026-09-08-spelldmg-healamt-scaling-design.md
--
-- Turns SpellDmg/HealAmt into uncapped percent-of-base multipliers on spells,
-- heals, DoTs and HoTs, and pins the item-stat caps as the primary "cap-as-dial"
-- soloability knob. Reverse by setting the five Spells rules back to 'false'.
-- =============================================================================
INSERT INTO rule_values (ruleset_id, rule_name, rule_value, notes) VALUES
 (1,'Spells:ItemExtraSpellAmtCalcAsPercent','true','SpellDmg/HealAmt applied as percent of base spell value'),
 (1,'Spells:FlatItemExtraSpellAmt','true','Bypass cast-time proportion and the +50%-of-base cap'),
 (1,'Spells:IgnoreSpellDmgLvlRestriction','true','Scale spells regardless of the 5-level spread'),
 (1,'Spells:DOTsScaleWithSpellDmg','true','DoT ticks scale with SpellDmg'),
 (1,'Spells:HOTsScaleWithHealAmt','true','HoT ticks scale with HealAmt'),
 (1,'Character:ItemSpellDmgCap','250','PRIMARY DIAL: ceiling on summed item SpellDmg (= percent at cap)'),
 (1,'Character:ItemHealAmtCap','250','PRIMARY DIAL: ceiling on summed item HealAmt (= percent at cap)')
ON DUPLICATE KEY UPDATE rule_value=VALUES(rule_value), notes=VALUES(notes);
