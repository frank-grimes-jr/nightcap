# Normal-player title QA

Status: OPEN. Use an ordinary account with status0/GM off in the test environment.
Synthetic counter/skill rows belong only in isolated QA data, never a live player
database. Record character, zone, build/hash, exact before/after and client result.

1. Enable the reviewed candidate in the isolated environment. Open the native
   Titles picker and run `#titles`, then `#titles 2`. Six goals per command page;
   invalid, zero, negative and excessive page values must fail safely. Existing
   AA/database titles and an already selected prefix/suffix remain unchanged.
2. In Blackburrow17, kill natural non-gray gnolls solo. One increment per finalized
   death. At99→100 total kills, Hunter appears once. Reselect, clear and reselect
   it; zone, camp and relog. The unlock and last equipped title persist.
3. In Unrest63, kill non-gray undead; both total and undead counters advance once.
   With a native party, test alive members at199 and201 units, a dead member,
   disconnected member and another instance. Only eligible nearby members count.
   Repeat with a pet and swarm pet. Gray enemies, charmed victims, merchants,
   owned pets, transient actors and GM accounts must not advance counters.
4. Defeat Nagafen in SolB32 and Vox in Permafrost73. Flamebreaker/Frostbreaker
   and then Dragonslayer appear. A copied name or matching NPC in another zone
   must not qualify. Historic personal Keeper boss credit should recover the
   matching named title without granting a slayer total or dragon rank.
5. Complete every required boss of Befallen36 in Raid: Bane of Befallen and
   Dungeon Delver. A second character who misses an objective gets no full-clear
   title. Grind, joining after missed bosses and killing only Gynok cannot satisfy
   the Raid title. A partial run remains partial after restart.
6. Complete the 21 Classic Keeper Raid checklist from `titles.html`. Omit Sky71:
   Conqueror of Classic stays locked20/21 even if Chapterhouse760 and Kael113
   are complete. Clear Sky: unlock once. Historical Hate76 and current186 count
   as one; Fear72/Hate186/Sky71 together unlock Planar Conqueror.
7. At49, maxing a currently available skill never gives its mastery title. At50,
   a raw skill one below the highest legal held-class cap stays locked even if
   equipment raises its effective value. Save the last point: unlock once. Test
   a cap0 skill and a secondary class with a higher cap than the base class.
   Release that class after earning: the award remains. Seven general crafts at
   legal caps together unlock Master Artisan; six do not. No new crafting or AA
   advancement permission is granted by titles.
8. Reach50; refresh to earn Seasoned Adventurer. Complete the final Last Lantern
   task9515 and refresh to unlock suffix “the Last Lantern”. An active/partial
   task or individual activity completion is insufficient. Test prefix and suffix
   together, change one without clearing the other, and inspect another client.
9. Disable the control row: no new counting/grants or earned-title selection.
   Existing database titles remain available and saved counters/awards remain.
   Re-enable and relog: awards return without a duplicate announcement. Exercise
   storage failure and a reserved-ID collision in isolation; title calls fail
   closed, while combat, XP, loot and unrelated native titles continue normally.

Native rendered picker behavior, title/nameplate length, packet encoding, relog,
party range, encounter difficulty and all visible acceptance remain manual gates.
Automated policy/DB/compile checks are recorded separately in README.md.
