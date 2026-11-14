-- Existing ruleset overrides take precedence over compiled defaults.
START TRANSACTION;
UPDATE rule_values SET rule_value='0'
WHERE rule_name IN ('Character:RestRegenTimeToActivate','Character:RestRegenRaidTimeToActivate')
AND rule_value <> '0';
COMMIT;
