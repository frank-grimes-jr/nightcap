# THJ behavior and gear candidate

Not deployed. This changes the existing all-class release; it does not unlock a new era.
Classic 50, level-one earned AA access, starter grants, pet/WPM systems and ownership remain.
The legal catalog is **1,845 ranks / 489 families**, compared with 1,836 / 483.

## Added to the legal catalog

| Class | AA | Ranks | Candidate behavior |
|---|---|---:|---|
| Warrior | Warlord's Fury | 1 | +100% all-skill physical damage, up to 12 s; reuse 60 s |
| Wizard | Mana Burn / Mana Blast / Mana Blaze / Volatile Mana Blaze | 1 each | Consume 10/20/30/40% maximum mana; retained 4 HP damage per mana |
| Wizard | Hastened Manaburn | 6 | Six-minute reduction per rank for all four burns; full reuse 15 min |
| Wizard | Dimensional Shielding | 1 | Separate new family 30201, rank/spell 43220; protects casting from hits, movement/channel checks and hostile interruption |

## Removed and refunded

Spell Casting Subtlety's three currently legal ranks are removed. Canonical owned
ranks in families 25,252,8300 (including disabled duplicates) and obsolete Silent
Casting modifiers 3521,3522,758 refund their recorded cumulative cost once on login.
Only 25 was in the immediately preceding legal catalog; the others may have dormant
historical ownership. Definitions stay present so ownership remains resolvable.
Wallet and earned rows commit through the existing locked transaction; a failure
blocks the projection instead of publishing a partial refund. No character SQL.

## Changed existing behaviors

| Class | AA / spell | Change |
|---|---|---|
| All casting classes | Silent Casting |12-class mask;1 h,60 s reuse,suspendable. Retain rank hate reduction 20/40/60/80/100% |
| Warrior | Gut Punch |1 opening damage; +50% physical damage taken for up to 12 s; native 45 s reuse |
| Warrior | Press the Attack |1 opening damage; AC−50 for up to 12 s; native 30 s reuse |
| Warrior / Monk | Grappling Strike |1 opening damage; evasion−50 for up to 12 s; native 30 s reuse |
| Paladin | Act of Valor |50% max mana paid once; group heal 2 HP per mana; full-cost requirement; no outgoing crit/HA; incoming healing modifiers remain |
| Wizard | Harvest |Activated 40% max-mana restore; native cast/reuse/cost retained |
| Wizard | Pyromancy / Cryomancy |35% proc; initial damage plusDoT; opposite-element resist debuff; coexist with other buffs, no duplicate-rank stacking |
| Magician | Heart of Flame / Fire Core |Absolute 100% /150% Improved Damage, excluded from generic 10× |
| Bard | Songs |3 s base cast becomes 2.5 s; songs receive no focuses/twincast. Outgoing DD-focus songs keep random ranges and multiply 10×; outgoing DoT-focus songs retain their prior range |

Other class lines retain the previous all-class catalog. No additional automatic
grants, free ranks, purchase-cost reductions or pet/weapon-proc rewrites.
Existing independent AA cooldown identities remain. Failed/blocked burns do not
spend mana or start cooldown; existing saved deadlines are not shortened on login.

## Focus changes

Players/permanent pets use strongest endpoints for Improved Damage/2, Improved
Healing, Mana Preservation, Reagent Conservation and Hate Adjustment. Damage
focuses multiply 10× except the explicit Mage and Bard-DoT cases. Supported AoE
targets bypass single-target/AoE exclusions for damage focuses only; school,
level, mana, duration, spell, class and other limits remain. Temporary pets and
ordinary NPCs keep prior focus behavior. The client displays the same projection;
server data keeps base values to prevent double multiplication.

## Gear

All 131 observed Normal IDs/names and their full 285-column rows match the pinned
stock ProjectEQ dump. That is an emulator approximation of standard EverQuest,
not Daybreak or THJ database access. Exact 131 Ascended observations stay authoritative.
Two observed augments and three quest epics retain their prior exact treatment.

47,809 eligible ordinary families produce 143,332 changed tier definitions.
Normal,209 starter families, custom Hunt/dungeon gear, ordinary augment/bag
families and quest-only epics are not regenerated.3,563 candidate families exceed
native field bounds and are excluded; unmatched/missing families are excluded.
Source: stock archive 2026-10-17, manifest and field evidence alongside this file.

- Ascended doubles positive AC/HP/mana/primary/resists/damage/HP and mana regeneration.
- Haste:1.5× rounded half-up. SD when stockSD=0:max(2×positiveINT,positiveWIS).
- HA when stockHA=0:2×positiveWIS. Accuracy when stockAccuracy=0:ceil(positiveDEX/2).
- New heroics:quarter of the final matching stat, rounded half-up; Ascended only.
- Positive native SD/HA/Accuracy/heroics are retained unless exact evidence overrides.
- Attack and sparse utility fields retain stock values absent exact observations.
- Polished/Exalted:one-third/two-thirds of the increase from stock Normal to top,
  rounded half-up. Negative penalties remain unless an exact observation differs.
- Effects, procs, clicks, focus/worn data, sockets, delay/range, equip gates, loot,
  recipes, prices and owned item state remain. Exact 131 values can override numeric
  sparse fields where specifically evidenced.

## Evidence versus calibration

ReleasedMay 7 post 2845 takes priority over Apr 20 post 2671, May 1 test post 2761,
and archived builders. Exact released numbers include 100% Warlord,50% Gut,
40% Harvest,50% Valor mana/2 HP ratio,10/20/30/40% burns,15 min fully-hastened reuse,
1 h/60 s Silent Casting,35% mancy,100/150% Mage cores and Bard 2.5 s/10×.

Calibrations:strongest endpoint; five-type static-focus scope from test notes;
10× interpretation of “increased by 1000%”; supported AoE target broadening;
1 HP/50 AC/50 evasion debuffs; native 4:1 burns,60 s immunity and 51 min base to meet
released 15 min after existing haste; full-mana requirement/rounding; native 72 min
Valor reuse and 100-unit radius; Dimensional 12 AA/120 s/30 min and stun exclusion;
mancy retained damage magnitudes and added damage/DoT allocation. Cryomancy's
old snare trigger is removed. Existing level 60/minmana/cast limits remain, so
ordinary Classic spells do not automatically gain those procs. Intermediate gear
interpolation and general weapon 2× (five observed weapons) are extrapolations.
