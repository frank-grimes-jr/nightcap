# Paladin grip balance review — October 27, 2026

Verdict: reject the current numerical table pending retuning and comparative
validation. Fresh independent reviewer: paladin_progression_review. Review used
the retained October27 production reference and October23 AA/spell/rule capture;
no new production access, gameplay changes or deployment occurred. The primary
agent checked the arithmetic and separately executed the actual DoDamageCaps
function to reproduce the low-level diagnostic failure.

1. **P1 — Wrong balance criterion; SoulFire 1H is not competitive.**
   Ascended SoulFire15/30 has raw ratio0.5000 versus Ascended Ghoulbane30/34,
   ratio0.8824:43.33% lower. Shield Specialist benefits both. The existing test
   asserts only1H<2H, so arbitrarily weakening1H still passes. At level50 in its
   own fixed2x model, SoulFire/Ghoulbane indices are12.667/20 without the shield
   modifier and22.667/37.647 with it. These are not measured DPS. Ghoulbane also
   has an undead proc; SoulFire has none. Complete attributes/resists/proc-level
   fields were not captured, so strict whole-item dominance is not established.
   Source: common/paladin_weapon_grip.h:26; tools/paladin_grip_balance.py:54–67.

2. **P1 — New quest progression reversal is unvalidated.**
   Newly awarded Ascended Avenger66/44 (1H22/30) is consumed for Normal Defender
   35/40 (1H13/30):41.67% lower raw2H ratio and40.91% lower raw1H ratio. Previously,
   Normal Avenger33/44 to Normal Defender35/40 improved ratio16.67%. This newly
   introduced hand-in transition is distinct from the older Ascended-to-Ascended
   anomaly. Defender has15AC/70HP/30mana and Holy Shock versus Ascended Avenger's
   0AC/50HP/50mana and Flame Shock, so it is not proven dominated. Test the exact
   transition on living/undead and stun-immune targets while retaining the user's
   required separate epic forge. Source: header:30–31; Inte_Akera.lua:50 and the
   captured fearplane/Irak_Altil.lua:36–38.

3. **P2 — Low-level comparison omits active native damage caps.**
   Captured LevelToStopDamageCaps=0 enables native caps. At level20, Paladin base
   damage caps at30 before Shield Specialist. For Ascended SoulFire, the fixed2x
   1H/2H indices with100% shield modifier become20/13.333, rather than the test's
   20/20.444. At level1 without AAs they become6.667/4.444, rather than10/20.444.
   Both corrected examples give1H a50% lead. Actual DoDamageCaps execution
   reproduces these numbers; they still are diagnostic indices, not combat DPS.
   Source: zone/attack.cpp:1415–1527,1705–1708; diagnostic:59–67.

Required next validation: compare all proposed1H profiles to appropriate same-tier
1HS weapons and exact quest predecessor/successor items, applying shared AAs,
complete item stats and proc restrictions, native damage caps and representative
class combinations. Then measure combat output and survival. Do not choose another
replacement table solely to force2H to win. Preserve Fiery Defender's separate
upgrade and the tested quest/client mechanics. No replacement values are approved
by this review. Full native build/encounter testing remains unavailable while the
local Docker startup fault persists.
