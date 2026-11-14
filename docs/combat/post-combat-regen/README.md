# Post-combat recovery

Build the matching world and zone and apply forward.sql to the target rules database before starting them. Save the two affected rule rows for each ruleset before applying the migration. To withdraw, restore those values and the prior binaries. No client assets change.

For test QA use a seated level-50 character with depleted HP and mana. End a regular fight in Lower Guk, then separately end a Lady Vox encounter in Permafrost. The rest indicator should clear on the last aggro loss, and the first eligible six-second tick should carry fast regen. With two enemies engaged, remove one and check that fast regen remains blocked. Repeat standing, with a rest-blocking detrimental buff, and after zoning with a previously saved countdown. At 6,000 maximum HP and 3,000 maximum mana in a 180-second zone, the fast floors are 218 HP and 106 mana. Record other bonuses separately. The shared rest state also opens endurance recovery immediately; its per-tick rate is unchanged.
