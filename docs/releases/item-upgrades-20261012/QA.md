# In-game acceptance: Reforging Box

Pending. The matched release is live for owner-approved QA. Use disposable QA
items/characters; keep disable/failure-injection tests on an isolated server.
Record client/server versions, character, item IDs, before/after inventory and
receipt IDs. Automated evidence is not acceptance.

1. Find Artisan Veyra, Reforging Boxes, in the East Commonlands tunnel workshop
   beside the Epic Forgemaster: `/loc` Y=-1818, X=-385, Z=3.75. Confirm appearance,
   Find listing, clear approach and no overlap. Hail and click the box link.
   Expect one free Reforging Box (900620); another request awards no duplicate.
2. Put the box in a main inventory slot. Confirm four slots and a Combine button.
   Four Polished Cloth Caps (201001) produce exactly one Exalted Cloth Cap
   (401001) inside. The inputs disappear and box remains, with no fee or roll.
3. Four Exalted Cloth Caps (401001) produce one Ascended Cloth Cap (601001).
   Test zone rewards separately: four 940025 -> one 940026, and four 940026 ->
   one 940027. Check names and stats against the target catalog.
4. Fill all other inventory slots and repeat. Output uses a consumed box slot.
   Close/reopen, zone and relog: output/box persist, inputs do not return.
   Verify exactly one receipt per successful combine.
5. Bind an eligible input, combine, and verify the output remains bound after
   relog. Test unbound ingredients separately for normal output binding.
6. Three inputs, mixed IDs, base/top-tier items, augmented, dyed, ornamented or
   customized inputs, and output lore conflicts must reject with every item
   unchanged and no receipt. Fix the condition and retry in the same box.
7. If a catalog-eligible stackable family exists, four units across one or more
   slots yield exactly one upgraded unit; three/five reject. Record a reason
   if this case cannot be tested against the target catalog.
8. Attempts during combat, casting or trading reject intact. Rapid repeated
   clicks consume only one valid recipe; reconnect and check exactly one output.
   Hand an unrelated item to Veyra and verify its ordinary return.
9. Use the box in another zone. Confirm bags cannot be inserted and dialogue
   explains the restriction. Ordinary tradeskill containers behave as before.
10. `#zoneforge` quotes and consumes three base copies, four Polished copies or
    four Exalted copies. Three higher-tier copies cannot bypass the new price.
11. On the isolated test server, rollback.sql disables a valid combine without
    changing contents. Activate the exact revision and retry successfully.
    Failure injection belongs in the fixture; never disrupt the live database.
12. Play representative solo builds through this progression and record whether
    four copies remains a worthwhile earned upgrade without trivial encounters.

Owner acceptance must identify skipped steps and blockers. Main/live deployment
was approved October 12 and completed; that approval does not record in-game
acceptance of these steps. See deployment.json for operational verification.
