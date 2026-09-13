-- #30: Vendors pay more for player loot (primary money faucet on a solo server).
-- BuyCostMod = fraction of items.price a merchant pays the player (default 0.95).
-- 2.5 ≈ 2.6x sell income; buy prices (SellCostMod) untouched so spells/bags still cost real money.
-- Requires: #reload rules (no restart).
-- ponytail: single global multiplier; per-era or per-item tuning only if 50s get rich too fast.
UPDATE rule_values SET rule_value = '2.5'
WHERE ruleset_id = 1 AND rule_name = 'Merchant:BuyCostMod';
