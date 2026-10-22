# Native robe acceptance

Pending: offline previews and mapped-native checks do not complete this gate.
Signed game release `2026102201` is available for live testing. Close EverQuest
completely, reopen the normal launcher and press Play. Keep the current matched
Nightcap proxy/catalog and default Classic models. Record both archive
hashes, race, gender, item ID/material, zone and screenshots for each result.
The wearer and observer must both load the update. Expected archive hashes are
in `candidate-package.json`; publication/recovery receipts are in `deployment/`.

1. In the East Commonlands tunnel (`ecommons`), use a test character holding a
   robe-eligible caster class such as Wizard. Repeat with caster in the second
   or third held slot and a noncaster primary. Existing class NPC flows remain
   unchanged; this feature introduces no NPC or command.
2. Cover both genders of Half Elf (race 7), Ogre (10), Troll (9), Barbarian (2),
   Halfling (11), Wood Elf (4) and Dwarf (8). Use race-matched test characters;
   illusions alone do not validate equipment eligibility.
3. Equip a legal robe: expect textured chest/sleeves and a full skirt, with
   recognizable native head/hands/feet and no bare tinted torso. Inspect all
   sides; female Halfling retains both feet. Check large-race belly/waist seams.
4. Cover robe materials 10–16 using independently identified items or disposable
   GM appearance fixtures. Record actual IDs/materials. Verify each pattern and
   two dye colors. Do not alter live item definitions merely to run QA.
5. Walk, run, turn, cast, attack, sit/stand, crouch, jump and die/resurrect on test
   characters. Check waist, hem, legs and sleeves for holes, spikes, misplaced
   triangles and severe clipping. Check another player's view, character
   selection, first person and third person.
6. Remove/re-equip, change to ordinary armor, zone to West Commonlands and back,
   relog and restart. Expected: correct robe/ordinary body and stable textures,
   with no crash or invisible body.
7. Test bare head, ordinary helmets and Winged Helm of the Dawn (HE90). Other
   armor slots must remain correct and all native feet must remain visible.
8. Regress original robe wearers: Human, Erudite, High Elf, Dark Elf and Gnome,
   both genders. Their original bodies/textures remain. The optional modern
   model setting retains prior behavior; it is not this change's target.
9. A character without a matching held class still cannot equip a restricted
   robe. Verify no damage, defense, mana, skill, item power or class access change.

The owner explicitly approved main promotion and live-QA publication on October
22 ("Approved. move into main."). This is a scoped exception before visual QA,
not acceptance of the scenarios above or standing release permission.
Record rejected races/poses and deliver any correction as a higher signed release.
