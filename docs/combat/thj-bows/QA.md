# Normal bows and heroic DEX

The June 12 THJ update describes heroic DEX increasing bow damage. Its heroic-stat guide gives a percentage curve and a separate flat ranged bonus. Nightcap already awards the flat component. For the new percentage, the test uses 0.25 percentage points per point through 100 heroic DEX, 0.09 through 200, then 0.06 thereafter. This gives 25%, 34%, 37% and 40% at 100, 200, 250 and 300. Continuing the last slope beyond 300 is a Nightcap calibration. Integer hit damage rounds down. Percentage examples are multipliers on the eligible damage portion, not a prediction of a player's total DPS. [THJ combat update](https://www.reddit.com/r/TheHeroesJourney/comments/1lamtdc/) · [THJ heroic-stat guide](https://github.com/P1xt/thj-wiki/blob/main/classes-and-abilities/heroic-stats.md).

For a qualifying physical bow hit, the server applies the percentage before Archery Mastery and the existing Ranger stationary-target bonus. The stock flat ranged component and the flat Bow Mastery effect keep their original positions. A successful Headshot replaces the boosted ordinary damage. No bow, arrow or AA definition changes.

## Measured ordinary hits

Each configuration used 8,192 physical arrows; the fixed level-50 target registered 4,740 hits in each normal condition. At 100 heroic DEX with no archery damage AAs, average damage per landed arrow rose from 29.65 to 34.21. With Archery Mastery III and Bow Mastery I together (20 earned points), it rose from 69.30 to 78.41. Zero-heroic-DEX controls stayed at 19.65 and 59.30 respectively. A separate level-51 comparison found that the stationary-target bonus was missing for a Ranger in a secondary or tertiary class slot. Holding Ranger now gets the same eligible bonus as primary Ranger. [Paired inputs and results](after.json) · [Original behavior](before.json).

## In-game validation

1. Use the same level-50 character, bow, arrows, target, skill, positioning and weapon buffs between runs. Use a stationary high-HP NPC in a private test instance, then repeat on a moving or rooted NPC to isolate the Ranger bonus. Keep the target stationary and away from its enrage threshold. Record effective DEX and heroic DEX separately; changing heroic gear can also affect ordinary DEX, skill, ATK, crits and accuracy. Keep the other stats matched or capture them for comparison.
2. From normal ranged autoattack logs, separate landed noncritical hits, critical hits, misses, special kills, procs and skill attacks. Compare damage per landed ordinary arrow with heroic DEX at 0, 10, 100, 200 and 300 if available. Use the same legal AA loadout for each comparison. 100 heroic DEX gives +25% on the qualifying portion of the hit, in addition to the existing flat ranged bonus.
3. Repeat with earned Archery Mastery, with Bow Mastery alone, and with both. Compare like-for-like hits to identify duplicate or missing contributions. Trick Shot and Endless Quiver affect arrow count and ammo use independently of this per-hit check. Include a lower-level control and both sides of the Ranger level gate. Keep attack rate and accuracy separate from landed-hit damage.
4. Test immediate and delayed arrows on otherwise identical setups. Include a miss, a successful Headshot, a thrown weapon and an activated archery skill as controls. Record the actual item IDs and AA ranks, zone/target, and player class slots. Effects on custom items or database loot are outside this change.

Owner graphical and encounter acceptance should be recorded separately from simulated combat and server health.
