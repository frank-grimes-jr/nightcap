-- Disable normal death EXP loss at every uint8 character level.
-- Run only after the runbook preflight and backup. Expect one changed row.
-- The operator owns the transaction and must check ROW_COUNT before COMMIT.
UPDATE rule_values
SET rule_value = '256'
WHERE ruleset_id = 1
  AND rule_name = 'Character:DeathExpLossLevel'
  AND rule_value = '10';
