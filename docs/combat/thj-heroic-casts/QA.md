# Heroic INT and WIS on direct spell effects

The June 12 THJ update makes spell gem casts and activated AA spells eligible. A proc firing during another cast uses its own source. Nightcap already calculates 0.1% per heroic INT on eligible direct damage and per heroic WIS on eligible direct healing. [June 12 combat notes](https://www.reddit.com/r/TheHeroesJourney/comments/1lamtdc/).

## Player verification on test

1. Record the caster level, held classes, purchased AA ranks, heroic INT and WIS, effective Spell Damage and Healing Amount. Use one target, a private instance, the same buffs and a consistent range. Use a wounded target with enough missing HP to measure each full heal.
2. Compare otherwise identical loadouts at 0 and 100 heroic INT, then at 0 and 100 heroic WIS. Keep effective item bonuses fixed. Record spell IDs, misses, resists, criticals and final values separately.
3. Cast a memorized direct damage spell and a direct heal. Repeat with an eligible activated damage AA and an activated heal AA. At 100 heroic points, an eligible unmodified value of 1,000 becomes 1,100 before caps. Vary the opposite heroic independently.
4. Repeat with a weapon or buff proc, both while idle and while casting a long spell. Compare the proc itself to its baseline. Its direct heroic multiplier should remain zero. Record the parent spell separately.
5. Repeat with a combat skill, including a skill that delivers a spell effect, then try an item click. Check neither gains the direct heroic multiplier. Confirm ordinary DoT and HoT ticks still use their existing formulas.
6. Repeat with a group heal hitting multiple injured characters and a delayed bolt. Check each recipient and the eventual bolt impact. Record actual character logs and timing alongside native fixture results.
