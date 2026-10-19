# Exact in-game AA QA — all-class candidate

Not run by the owner yet. Perform only after approved activation of the candidate
on a test server. Test data and GM point grants belong on spare test characters,
not ordinary player characters. Record actual spent points and ranks, not a
nominal unlimited-AA budget. Encounter balance is the next task.

## Catalog and progression

1. Launch with the repaired signed client/proxy catalog pair. In East Commonlands
   tunnel, confirm `#classes`, level cap50 and the existing starter weapon/robe.
   Open AA and turn Recommended AA **off** to see the complete legal catalog.
2. At levels1 and50, compare the relevant class section in CHANGELIST.md. Check
   titles/descriptions, next rank and its earned cost. Missing prerequisites must
   prevent buying, zero points must prevent paid purchases, and buying rank2
   directly must fail. Do not expect every THJ custom effect in this pass.
3. Test each class below as a held class, including as a secondary class on a
   melee-primary character. Its listed new line must appear; removing that class
   must remove effective access while preserving shared/earned ownership under
   the existing Chronicler transaction and canonical refund rules.

| Class | New line to locate/test | Existing depth to inspect |
|---|---|---|
| Warrior | Gut Punch | Tactical Mastery3→9 |
| Cleric | Ward of Purity | Celestial Regeneration3→9 |
| Paladin | Blessing of Light | Radiant Cure3→6 (family285) |
| Ranger | Ranged Finesse | Precision of the Pathfinder3→9 |
| Shadow Knight | Vicious Bite of Chaos | Touch of the Cursed3→6 |
| Druid | Spirit of the Black Wolf; Healing Boon | Healing Boon0→6 for Druid |
| Monk | Hastened Mend | Kick Mastery3→9 |
| Bard | Dance of Blades; Hastened Blades | Shield of Notes3→6 |
| Rogue | Envenomed Blades | Virulent Venom3→5 |
| Shaman | Turgur's Swarm | Spirit Call3→5 |
| Necromancer | Scent of Terris | Quickening of Death3→5 |
| Wizard | Destructive Fury397 | Improved Familiar3→4 |
| Magician | Companion of Necessity | Shared Health3→5 |
| Enchanter | Mental Contortion | Eldritch Rune3→8 |
| Beastlord | Bite of the Asp | Paragon of Spirit3→7 |
| Berserker | Frenzied Volley | Blur of Axes3→13 |

Use the generated list as authority if a prerequisite limits a displayed prefix.
Do not interpret a remaining excluded execute or custom ability as an accidental
omission; dispositions.json records the exact reason.

## Native behavior / persistence

- **Bard:** with earned Harmonious Attack5 and Dance of Blades, activate on a
  training target in a test instance. The buff expires at its finite native
  duration, not permanently. Base reuse36minutes; Hastened BladesIII yields
  24minutes. Reconnect and zone while reuse is active: the remaining deadline
  must not reset. Another AA family remains independent.
- **Wizard + Cleric/Druid:** compare Destructive Fury397 and398 alone and together
  with fixed gear/spell and critical chance. Native AA critical-damage handling
  takes the higher contribution, not the sum. Remove/re-add the extra class on
  spare characters and confirm stale bonuses do not remain.
- **Druid Healing Boon:** verify six purchasable ranks with normal prices. Cast
  an allowed heal-over-time on a damaged test character; the passive affects
  HoT critical chance, not a second instant heal. Cleric/Paladin/Shaman retain
  access and the last rank's native bonus is16 percentage points.
- **DRU/NEC/MAG:** browse all activated AAs, assign several new and old hotbuttons,
  activate unrelated families, zone and reconnect. This is the largest catalog
  at74 native cooldown slots; no button may alias another's cooldown.
- **Starter safeguards:** Harm Touch/Lay on Hands/Hunter's Attack Power free
  prefixes remain at their released three ranks; no points/ranks/autogrants
  appear merely on login. Existing pet/WPM ceilings remain unchanged.
- **Rollback rehearsal on test only:** buy a newly legal rank, save/relog,
  restore baseline policy and verify it becomes dormant without erasing saved
  ownership. Reapply candidate and confirm reactivation without repurchase or
  a free point grant. Preserve unrelated timers and existing purchases.

For balance measurements afterward, use equal earned investment and gear at
creation, mid-progression and50. Record damage, healing, mana use and pet share
in ordinary Commonlands fights, Unrest and Lower Guk; separate unlimited-AA
stress builds from achievable progression. No balance verdict is recorded here.
