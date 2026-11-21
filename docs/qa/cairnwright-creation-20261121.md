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

## Level-one candidate

The separate `feature/cairnwright-level-one` branch starts at main `ec3b22fe`. The zone and signed-client source share class 17 spell eligibility through `common/cairnwright.h` and the generated spell catalog. Stock spell files retain their 16 level columns. The client extension accepts CRW in all three Nightcap class slots. This concerns the in-zone display and spellbook.

| Spell | ID | Candidate behavior |
|---|---:|---|
| Strike Cairn | 44381 | Four mana, one-second cast, four-second reuse. Sets one character-local stone for 90 seconds. |
| Sound the Seam | 44382 | Five mana, one-second cast, six-second reuse. A clear line of sight up to 60 units long can hit two engaged, attackable NPCs within four units of its axis. |
| Seam Fracture | 44383 | Internal single-target magic-resisted hit, base five damage. Players cannot learn it. |

The Perl spell hooks run after a self-target cast and check the caster and held discipline. The zone grants the two learned spells in empty spellbook slots during class reconciliation. The East Commonlands and PoK Chroniclers offer 17 and call the native compare-and-update adoption path. Release uses the existing atomic transaction and clears the cairn after commit. The candidate uses a Shaman base-stat curve through Classic 50.

**Evidence.** MSVC built the x86 extension. A compiled test consumed primary, secondary and tertiary CRW snapshots, a release snapshot, and spell access for every stock class. Both Chronicler scripts passed the popup and slot-lifecycle harness, including both release slots. Linux Perl passed 11 effect checks using fixture actors. Local PEQ temporary tables accepted the three rows and exact replay and rejected an altered mana value. The base-stat rehearsal produced 50 rows on first application and replay. The generated 237-field spell file preserved the original bytes and passed field, collision and template-drift checks. These tests used a local database session, test objects, or candidate assets. None logged a player into a zone.

**Build and rollout boundary.** The local Linux build uses the retained November 21 equipment/ornament shipping inputs, freshly compiles the affected zone sources and Perl unity archive, and links a separate candidate binary. Player use requires matching world, zone, spell cache, quest/plugin content and signed client assets. World creation, class-specific creation data and the RoF2 pre-world class selection and relog representation still need integration. The class has no public release. The player wiki stays on its existing release labels. Its refresh check still reports historical source drift.

The tested x86 extension SHA-256 is `a528d84fcdc90717609aa1630f3f2762053e430581dd42f855677707529b6aff`. The Linux zone candidate SHA-256 is `9d75a2c106ff30b94e5e068f45e22ab861058f8e1b69f696823d25fd058bb0ab`. The candidate spell file SHA-256 is `d67df84974b4bad55f0f4e18f37c12abcc61f1cf14e23f1725cb5a8f8f83feeb`. The retained local build helper is `docs/qa/cairnwright-level-one/compile_candidate.py`; supply the server source diff against base main as `zone.patch` and the new `cairnwright.h` beside it in a dedicated local Docker build directory. It builds a test artifact without installing it.

The owner requires selection inside RoF2 and the existing workspace as the source boundary. The retained RoF2 interface header in `artifacts/advloot-20260930/reference/UI.h` declares `CCharacterCreation::SelectedClassButton`, `GetClassButtonIndex` and `FinalizeNewPCAndSendToWorld`. The checked client source provides no implementation of the stock selector or registration interface for adding a logical choice. This is the outstanding creation integration. A statically valid radio button, a server row alone, or an in-zone class snapshot does not test it. The current world advertises its creation combinations to connected clients; public activation requires testing compatibility for players on older clients as well.
