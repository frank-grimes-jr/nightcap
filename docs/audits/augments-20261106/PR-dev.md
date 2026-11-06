Guard kills and other unlisted enemies currently miss zone augments despite the 1.5% family chance. This candidate grants any unowned killable NPC the augment roll, corrects High Keep cleanup/Hate identity, adds bounded secondary specialties and replaces every default/glove icon with visually checked stock gems.

The integration supersedes the older October29 static-only candidate while retaining existing capacity configuration and preview sources exactly. Native and quest contents match the linked main-based candidate. This source promotion does not activate SQL, native binaries, worker capacity or the public wiki.

Validation: 29 integration checks pass, two historical opt-in MariaDB checks skip; 22 wiki checks pass. The release-base candidate separately passes 52 focused checks, four full native compiles, authenticated 144-input link/baseline reproduction and complete disposable SQL forward/inverse/drift tests.

Main/OVH and player acceptance remain gated. Any later augment-only release must use the main-based candidate, not promote unrelated capacity configuration from all of test.

Exact in-game QA spike:


1. In public High Keep, kill native goblins and killable guards; in Qeynos Hills
   kill a low-level non-allowlisted animal and a named/quest enemy. Each receives
   the same 1.5% augment chance; equipment keeps its old restrictions. Random
   absence is not proof of exclusion. Use a controlled QA-only forced RNG to
   prove single-corpse delivery, then a separately labeled normal-rate sample.
2. Run Osargen's managed High Keep rescue and kill scripted prison-break guards.
   Check the augment survives cleanup and the existing rescue/alarm/wave rewards
   and zero unintended coin/gear behavior remain. Check an unowned encounter add.
3. Kill a lootable merchant in an enabled QA zone. A client/player-owned pet kill
   can award the augment and leave a normal owned corpse. City merchants and
   protected services remain unchanged. Kill a charmed pet after charm fade and
   a merc/swarm pet: no augment. Keep access/service NPC safety intact.
4. In Kithicor, test daytime ordinary enemies and nighttime undead. In Classic
   public/private Cazic-Thule test guards/named. In new managed Hate B verify
   Blackspire Prism, while old Hate runs give Spiteglass. Wearable families remain
   inherited appropriately. Six excluded/access-check pools still cannot drop.
5. In Chapterhouse and Ashen Compact, test ordinary, named and unowned dynamic
   enemies at 1.5%; verify static-only 35% miniboss relic eligibility is unchanged.
   Suspend/reboot a saved live NPC and restore an existing corpse: original corpse
   loot persists exactly once. Exercise native failed death-staging recovery.
6. Socket the three shield-block families in each of the six allowed armor slots.
   One/six top copies give +2 Hunt block total, not +12. Remove the shield, use an
   ineligible/under-level shield or move armor into training slot21: no benefit.
   Pair with Paladin grip block, legal AAs and buffs; verify caps/eligibility and
   front/rear, strikethrough and ordinary shield-block behavior.
7. Compare six avoidance/mitigation/accuracy/damage/heal copies against mixed
   builds. Test level1/20/40/50 progression and strongest legal level50 multiclass
   gear/AAs/pets; measure kill time, incoming damage and mana sustain. No claim of
   encounter acceptance from isolated arithmetic alone.
8. Test duplicate dodge/focus items against stronger gear/AAs/buffs, stock spell
   limits (short casts/Bard/excluded spells/level limits), Faerune breathing,
   vision and invisibility. Check primary stats and item-XP training remain.
9. Inspect Understone Heart in The Hole and both expedition augments in inventory,
   corpse, advanced loot and item links. All qualities use their reviewed exotic
   icon. Test full bags, loot filters, one-for-one receipt transfer, forging 3/4/4,
   trade, relog and saved corpse recovery; no gloves/armor icons or lost augments.
