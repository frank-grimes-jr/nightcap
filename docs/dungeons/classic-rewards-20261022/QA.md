# In-game acceptance — unique Classic raid rewards

Deployed for live testing on October22; results remain unconfirmed. Use non-GM
characters for click, reagent, level and restriction checks. The expansion's
`../classic-expansion-20261022/QA.md` still applies to all21 Keepers, run isolation,
tasks, credit, shared loot, Sky keys, deadlines and recovery.

1. In each dungeon listed in REWARDS.md, choose Raid at its Instance Keeper and
   defeat the documented final objective with valid encounter credit. Verify its
   new exclusive families match that dungeon, are Polished/Ascended, and supplement
   native loot and the separate personal completion reward. Across repeated runs,
   validate one/two/three distinct designs and the unchanged90/10 quality split.
   Originalseven finals retain their original named exclusives and IDs.
2. Inspect every new family in both qualities. Compare IDs, MAGIC, stats, recommended
   level, lore text and appropriate visible weapon type/slots with REWARDS.md.
   Inspect an old armor, accessory, bag and weapon: all MAGIC; all other old values
   unchanged. Test trade, relog persistence, merchant zero resale and rejected
   existing forging recipes without consuming inputs.
3. Fear: equip Visage of Unbroken Will at46 and click See Invisible. Confirm a
   10-second interruptible cast and native visibility behavior; both qualities and
   duplicate copies share the five-minute reuse even after relog.
4. Hate: equip Maestro's Unfinished Requiem at46 and click Invisibility. Confirm
   native invisibility and native actions that break it,10-second cast and shared
   ten-minute reuse. Check beneficial targeting behaves like the native spell.
5. Sky: equip Astrolabe of the Eighth Island at46. In a permitted outside zone,
   confirm missing Bat Wing prevents casting, then one Bat Wing is consumed by a
   successful Levitate cast. Verify native duration, shared15-minute reuse and
   relog persistence. In Sky (canlevitate=0), the normal restriction must reject it;
   normal island keys/tokens remain necessary. No GM bypass for this test.
6. Attempt each click from inventory, at level45 and while casting is restricted:
   no successful utility effect. Equip/cast successfully at46. Swapping Polished
   and Ascended never bypasses the family cooldown; unrelated clicks/AA/disciplines
   remain independent. Different planar families have separate clocks.
7. Resume a run and claim a reward recorded before this release: exactly the
   previously selected item/drop identity, no reroll, loss or duplicate claim.
   Repeat with an already generated final corpse before/after reconnect/restart.
8. Balance: compare representative melee, caster, healer, pet and mixed builds at
   each dungeon band with realistic legal AAs and earned gear. Record actual spent
   AA, equipment, clear time, deaths, damage, resources and utility impact. Test
   planes at46–50 with both qualities. Do not equate budget tests to encounter QA.
