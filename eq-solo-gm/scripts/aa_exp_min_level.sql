-- #37: Allow AA experience from level 1 (stock EQ gates it at 51).
-- New rule Character:AAExpMinLevel (compiled default 51). This row overrides it to 1
-- on ruleset 1 so the AA-XP gates in exp.cpp permit AA accrual at any level.
-- New rule => not yet present in rule_values, so INSERT (plain, per repo convention).
-- Requires: #reload rules (no restart). Zone binary must already carry the new rule.
INSERT INTO rule_values (ruleset_id, rule_name, rule_value, notes)
VALUES (1, 'Character:AAExpMinLevel', '1', 'Nightcap: AA XP allowed from level 1 (#37)');
