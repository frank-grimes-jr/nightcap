-- Verification for the SpellDmg/HealAmt scaling slice. Run AFTER applying both
-- scripts and regenerating tiers. Checks 1-2 confirm rules/caps; checks 3-5 prove
-- the STAMP by joining each tier copy to its base item (id - offset), so a
-- pre-existing offense-multiply coincidence cannot satisfy them. The Ascended
-- band (offset 600000) is the representative check.
SELECT 'rules_true (expect 5)' AS check_name, COUNT(*) AS result
FROM rule_values
WHERE rule_name IN ('Spells:ItemExtraSpellAmtCalcAsPercent','Spells:FlatItemExtraSpellAmt',
                    'Spells:IgnoreSpellDmgLvlRestriction','Spells:DOTsScaleWithSpellDmg',
                    'Spells:HOTsScaleWithHealAmt')
  AND rule_value='true';
SELECT 'caps_present (expect 2, both 250)' AS check_name,
       GROUP_CONCAT(CONCAT(rule_name,'=',rule_value) ORDER BY rule_name) AS result
FROM rule_values WHERE rule_name IN ('Character:ItemSpellDmgCap','Character:ItemHealAmtCap');
-- Causation: Ascended copies of base-ZERO worn items must be exactly 20/20.
-- Before the stamp these are 0 (count 0); after, thousands. Expect > 1000.
SELECT 'ascended_base0_stamped_20 (expect > 1000)' AS check_name, COUNT(*) AS result
FROM items a JOIN items b ON b.id = a.id - 600000
WHERE a.id BETWEEN 600001 AND 799999 AND a.slots > 0
  AND b.spelldmg = 0 AND b.healamt = 0
  AND a.spelldmg = 20 AND a.healamt = 20;
-- Completeness: NO base-zero worn Ascended copy may remain unstamped.
-- Before the stamp this equals every base-0 worn item (huge); after, expect 0.
SELECT 'ascended_base0_unstamped (expect 0)' AS check_name, COUNT(*) AS result
FROM items a JOIN items b ON b.id = a.id - 600000
WHERE a.id BETWEEN 600001 AND 799999 AND a.slots > 0
  AND b.spelldmg = 0 AND b.healamt = 0
  AND NOT (a.spelldmg = 20 AND a.healamt = 20);
-- Bags never received the stamp: a bag tier copy's stats must equal its base's.
-- Expect 0 changed (the stamp is guarded slots>0).
SELECT 'bags_stat_changed (expect 0)' AS check_name, COUNT(*) AS result
FROM items a JOIN items b ON b.id = a.id - 600000
WHERE a.id BETWEEN 600001 AND 799999 AND a.bagslots > 0 AND a.slots = 0
  AND (a.spelldmg <> b.spelldmg OR a.healamt <> b.healamt);
