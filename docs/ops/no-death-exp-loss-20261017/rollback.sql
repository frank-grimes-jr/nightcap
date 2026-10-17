-- Restore the captured policy for future deaths; never restore player snapshots.
-- The operator owns the transaction and must check ROW_COUNT before COMMIT.
UPDATE rule_values
SET rule_value = '10'
WHERE ruleset_id = 1
  AND rule_name = 'Character:DeathExpLossLevel'
  AND rule_value = '256';
