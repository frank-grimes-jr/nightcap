-- Verification for the SpellDmg/HealAmt scaling slice. Run AFTER applying both
-- scripts and regenerating tiers. All four expectations must hold.
SELECT 'rules_true (expect 5)' AS check_name,
       COUNT(*) AS result
FROM rule_values
WHERE rule_name IN ('Spells:ItemExtraSpellAmtCalcAsPercent','Spells:FlatItemExtraSpellAmt',
                    'Spells:IgnoreSpellDmgLvlRestriction','Spells:DOTsScaleWithSpellDmg',
                    'Spells:HOTsScaleWithHealAmt')
  AND rule_value='true';
SELECT 'caps_present (expect 2, both 250)' AS check_name,
       GROUP_CONCAT(CONCAT(rule_name,'=',rule_value)) AS result
FROM rule_values WHERE rule_name IN ('Character:ItemSpellDmgCap','Character:ItemHealAmtCap');
SELECT 'ascended_worn_stamped (expect > 0)' AS check_name,
       COUNT(*) AS result
FROM items WHERE id BETWEEN 600001 AND 799999 AND slots>0 AND spelldmg=20 AND healamt=20;
SELECT 'bags_untouched (expect 0)' AS check_name,
       COUNT(*) AS result
FROM items WHERE id BETWEEN 200001 AND 799999 AND bagslots>0 AND slots=0 AND (spelldmg<>0 OR healamt<>0);
