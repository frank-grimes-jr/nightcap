# Cairnwright creation experiment

Feature worktree based on main `cca7e6dfcb312dd30528609c1483d2382de35226`. Local QA only.

## Observed

- The QA and protected reference copies of `EQUI_CharacterCreate.xml` have SHA-256 `2da0ea6ecf7eb04a1ca4bd2ec3ba15c8062160df86540ab3ce9809c11398249a`. Their class screen defines 16 radio buttons and 16 overlays.
- The generated layout adds one Cairnwright radio button, references it from the actual class screen, and moves the decorative heading left. The check compares all other XML elements with the original and checks the button bounds against every sibling. Output SHA-256 is `2fd07b45636b3060db13149f7f4d481fcc7894700e90576947354eeec70d1cdf`.
- An isolated QA copy launched RoF2 executable `2a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e` with the generated default layout and localhost login configuration. The process displayed the startup warning and EULA. These screens precede character creation.
- Read-only local PEQ queries returned 16 distinct classes in `char_create_combinations`, zero class-17 combinations, zero `classes17` columns in `spells_new`, and zero spells named Strike Cairn or Sound the Seam. No character or multiclass row in this local database held class 17.
- Wiki impact review found no public gameplay change. The current wiki refresh check reports historical drift from its October 24 reviewed revision. Leave the review ledger and publication alone for this isolated experiment.

## Integration gaps

The XML describes a radio button. There is no Cairnwright selection handler in the reviewed Nightcap client source. A visible or depressed button alone cannot establish which class the client submits or renders upon return. Pre-world creation and post-login spell access require separate client integration.

* `server-mods/code/world/client.cpp` rejects name approval outside Warrior through Berserker. The RoF2 creation path separately checks the race, class, deity, zone and allocation combination. Both checks must agree with the client.
* `common/classes.h` in the local EQEmu source has a 16-class count and a 16-bit all-class mask. The shared spell class catalog has 16 levels per spell. `eq-client-dll/src/spell_access.h` enumerates 1 through 16. Widening only the creation gate would leave the new class without a consistent authorization or display path.
* `server-mods/plugins/multiclass.pl` maps 16 names and constructs a spell-class column for preview. The East Commonlands Chronicler accepts adoption confirmations through popup 316. Native `ReleaseMulticlassSlot` owns release persistence and refunds.

## Reproduce the asset check

From the feature worktree, pass the original and a **new** output path. Generate into a QA directory. The generator refuses to overwrite an existing file.

```powershell
python tools/cairnwright_creation_ui.py $stockXml $qaXml
python tools/tests/check_cairnwright_creation_ui.py $stockXml $qaXml
```

## Playable acceptance still required

1. On the local world, choose a Dwarf Cairnwright with all 16 original choices still present where race-eligible. Record the displayed class, name approval, completed creation and the saved primary class (`character_data.class = 17`) for that character. Use a separately created stock Dwarf as the control.
2. Camp, close the QA client, restart, select the saved character and enter the world. Verify the same character ID, displayed class and saved primary class.
3. At level one, memorize Strike Cairn and Sound the Seam. Place a stone, move, pulse an engaged target on the line, and check a target off the line. Record spell IDs, mana, recast and combat results. Repeat after relog.
4. On a separate eligible stock-primary character, hail the Ancient Chronicler in East Commonlands. Preview and confirm Cairnwright, check the persisted secondary slot, reconnect and cast both spells. Release via the NPC, reconnect and confirm both spells are unusable, existing class capabilities survive and a planted stone is gone. Repeat in slot three with slot two already occupied. Verify repeated release and an attempt to adopt one's birth discipline leave the original build intact.

No paired client, world, zone or spell catalog implementing class 17 has been deployed. This experiment does not establish any of the four playable acceptance steps.
