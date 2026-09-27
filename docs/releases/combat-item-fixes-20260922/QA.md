# In-game acceptance: combat and tier items

Run only after the candidate is installed in the agreed test environment. Record
server, client release, character level, class slots, race, skill values and gear.
Do not alter the owner's character or production items merely to set up tests.

1. In East Commonlands, compare two level-2 Human test characters: Monk primary
   and Wizard/Monk. Remove weapons, gloves and damage buffs; match Hand-to-Hand
   and Offense. Fight separate level-1 a decaying skeleton spawns. Record a combat
   log, not one lucky hit. The candidate's base fist damage is 4 for both; actual
   hits still depend on skill, accuracy, mitigation and damage rolls. Repeat with
   Monk tertiary. An ordinary Wizard remains on caster fists (base damage 2).
2. Start a Wizard/Monk with seeded Dual Wield at 1; fight eligible non-gray NPCs.
   Confirm it can improve and produce empty offhand swings. It must stop at the
   native Monk cap for the level. Repeat Hand-to-Hand and Offense advancement;
   a shield/two-handed weapon must still block the empty-offhand case. Release
   Monk on a disposable test character, relog and verify native caster limits.
3. At level 30, compare Monk primary/secondary/tertiary against the same GM-created
   magic-only training target in the arena. Bare fists should pass the same
   immunity check; level 29 without magical gloves should not. Keep target stats,
   buffs and skills identical. This requires a test NPC fixture, not live content
   mutation. Repeat a high-level unarmed parse to cover damage table/bonus gates.
4. In the East Commonlands tunnel, inspect then equip base Cloth Cap 1001 and
   Ascended Cloth Cap 601001, plus Ascended Cloak of Flames 611621. Camp/zone to
   clear stale client item data. Expect Ascended cloth spell/heal 0/0 and cloak
   10/10 if the target base item still matches the captured source. Compare spell
   and healing output at matched buffs, AA and all other gear. Check Polished and
   Exalted versions too. Bags and unrelated item columns must be unchanged.
5. Compare fixed WAR/CLR/WIZ, WAR/CLR/MNK and MAG/NEC/SHM level-50 loadouts with
   the historical classic-v2 fixture. Record actual allowed AA spend and item
   spell/heal totals, DPS, healing, mana use, survival and fight duration. Earlier
   projections are not encounter acceptance; marginal pet encounters need special
   attention. Do not compensate with unrelated NPC/rule changes in this release.
6. Casting diagnosis is still open: in the East Commonlands tunnel, cast a
   non-instant self buff out of combat, then the same spell while autoattacking a
   test target. Record client release, spell name, observed bar motion and finish
   time. The owner already confirms the bar freezes in both cases while spells
   finish. A casting fix must demonstrate a moving bar in both, correct cancel /
   interrupt behavior, and continuing melee before this issue is closed.
