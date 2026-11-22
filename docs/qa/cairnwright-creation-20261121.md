# Cairnwright creation experiment

Feature worktree based on main `cca7e6dfcb312dd30528609c1483d2382de35226`. Local QA only.

## Subsequent deployment

The world, zone, quest scripts and content described here are now on OVH. The signed client pair and creation button remain pending. The sections below record the earlier local experiments. [Live server and player guides](../releases/cairnwright-20261121/README.md)

## November 22 LocalDev character creation

The owner selected Dwarf Warrior in the QA client, then clicked the Cairnwright radio button. MacroQuest's local log at 09:30:08 Eastern showed Warrior checked and Cairnwright clear. At 09:30:32 the same two controls reported Warrior clear and Cairnwright checked. At 09:44 Eastern, world logged Warrior at name approval, received class 1 at creation and admitted the resulting character to East Commonlands. A separate read of `character_data` confirmed primary class 1, race 8, level 1 and zone 22. This reproduces a client defect before name approval. A checked button alone is insufficient evidence for class selection.

After the test, the reviewed creation migration passed first application and replay against LocalDev PEQ. The class 17 combination is Dwarf (8), Brell (202), Kaladim (67), allocation 14, expansion mask 0. Its start and bind are East Commonlands (22). The signed-client release is independent of these rows. The retained server archive passed its content rehearsal, and a local read verified one combination, one start, 50 stat rows, two starter items and three spell records. At inspection the running post-combat-recovery world and zone were `4985c51d` and `b9256b94`. The matching Cairnwright builds are `a641bef7` and `771122fc`. World reads the combinations on boot. Native class-17 name approval, creation and relog remain pending in LocalDev.

The owner subsequently approved the LocalDev restart. The world process now runs `a641bef7`, and eight zone workers run `771122fc`. The world mapped the verified item cache (`d9123f0d`), and every zone mapped that cache and the spell cache (`e8b738dc`). Loginserver, UCS and queryserv were running, admissions were open, and the new world logged loading character-creation data. The local Chroniclers used the same script before the cutover and both now use the matching Cairnwright version. Both spell handlers and the multiclass plugin were verified on disk. The Dwarf Warrior and Cleric test characters retained their original class, race and level.

The first switch rolled back when the service user could not preserve cache ownership. The retry installed the verified files with the required ownership. The pre-switch local PEQ backup passed gzip integrity verification; SHA-256 `60f4c3bb131501dca02d08f3f44b027490e0879b439443a1f1dd7bf398c24fd6`. On startup the new world added eight defaults to ruleset 1: `AA:LevelBasedPointsPerLevel=0`, `AA:PassiveExpPercent=1`, `Items:FreeTrade=true`, and false values for `Items:PowerSourceItemXP`, `Combat:NightcapHeroicMeleeScaling`, `Spells:NightcapHeroicSpellScaling`, `Spells:NightcapTHJBehaviors` and `Spells:NightcapTHJDamageScaling`. All preexisting rule rows kept their values.

Wiki impact: this local QA result leaves the published player guide's 16 starting choices accurate.

## Observed

- The QA and protected reference copies of `EQUI_CharacterCreate.xml` have SHA-256 `2da0ea6ecf7eb04a1ca4bd2ec3ba15c8062160df86540ab3ce9809c11398249a`. Their class screen defines 16 radio buttons and 16 overlays.
- The generated layout adds one Cairnwright radio button, references it from the actual class screen, and moves the decorative heading left. The check compares all other XML elements with the original and checks the button bounds against every sibling. Output SHA-256 is `2fd07b45636b3060db13149f7f4d481fcc7894700e90576947354eeec70d1cdf`.
- An isolated QA copy launched RoF2 executable `2a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e` with the generated default layout and localhost login configuration. The process displayed the startup warning and EULA. These screens precede character creation.
- Read-only local PEQ queries returned 16 distinct classes in `char_create_combinations`, zero class-17 combinations, zero `classes17` columns in `spells_new`, and zero spells named Strike Cairn or Sound the Seam. No character or multiclass row in this local database held class 17.
- Wiki impact review found no public gameplay change. The current wiki refresh check reports historical drift from its October 24 reviewed revision. Leave the review ledger and publication alone for this isolated experiment.

## Initial integration gaps (layout experiment)

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

The layout experiment established the asset shape. The native world evidence below covers the server portion of character creation and character select.

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

## Native world creation and fresh-process character select

A synthetic account supplied application messages to the candidate world's ordinary `Client::Process` entry point. The in-process RoF2 stream delivered name approval followed by character creation. World validated the Dwarf/Brell/Kaladim combination using allocation 14, resolved the Nightcap East Commonlands bind, loaded its starter item cache and granted its normal 100-platinum wallet. The scratch database began with empty character, inventory, and wallet tables. A second invocation started a fresh process, opened a new database connection and used `SendCharInfo` to read the saved character. Both invocations checked the entry sent to the character list and independently queried the stored class and equipped slots.

```text
CREATED id=21 class=17 level=1 zone=22 kit=998616,998636
RELOADED id=21 class=17 level=1 zone=22 kit=998616,998636
```

The name was Cairnproof. The two creation-only items are a 10 AC, 5 WIS robe and a 6 damage, 30 delay one-handed hammer. The ordinary stock creation-combination packet was byte-for-byte identical with and without the class 17 server row. The world validator rejected unrelated race, deity, city and overspent stats. The two content migrations passed exact replay against local PEQ structures and the location migration rejected a changed bind. The world starter-grant test passed for all 17 classes. The spell effect-level test exercised all 256 class byte values and the level boundary for learned spells and the unlearnable child hit.

World SHA-256 `a641bef73c39fcc37192685bb077f1f5e9acf77dd4d79e7998ae899912eff521` follows a reproduction of retained shipping world `9726ce1cca92ffb29b198f15428688b44f243e9513623d8e4b02a700e7dfb32d`. Zone SHA-256 `771122fc9f8b208eb9338f82df3c614288582a8ae9f5bd19ed7ed4c1b5665989` includes the bounded spell level lookups. The x86 extension build was `ba6f5a24eb93e81c449a131656387f4bd8dae94e6f943cb8919d46f2b998613c`.

The headless driver and build helpers are in `docs/qa/cairnwright-level-one/`. Run `compile_world.py`, then `build_world_probe.py` with `world_creation_probe.cpp` beside it. Use `run_world_probe.py <temporary Docker build directory> seed`, then `create` and `list`, against an empty disposable MariaDB container as described in the runner. For a component test, run `test_world_creation.py <EQEmu source> --cxx cl` inside a Visual Studio developer shell. The database in these tests was separate from local PEQ and production.

RoF2 has yet to submit the Cairnwright button choice or render this character on relog. The QA copy's `testeqgame.exe` hashes identically to `eqgame.exe`. The stock SIDL Button schema exposes a screen identifier and radio group. The separate HTML window has an embedded web component, but its start URI provides no authenticated world-creation callback. The broad armor eligibility change follows gameplay validation. This prototype has no public gameplay or wiki release.

## Native zone casts and Chronicler persistence

The isolated zone linked the candidate zone objects and Perl archive. It loaded East Commonlands geometry, the candidate spell cache, both spell hooks and the Ancient Chronicler quest. Character 21 entered with 21 mana. Strike Cairn planted the stone and spent four mana. With the caster moved eight units from the stone, Sound the Seam spent five mana. Both skeletons had the caster on their native hate lists. The skeleton halfway along the seam lost five HP. The skeleton twelve units to its side lost zero. A fresh process loaded the same character and both saved spell gems and repeated those results.

The stock-primary controls were Warriors. Character 22 adopted Cairnwright in slot two. Character 23 already held Cleric in slot two and adopted Cairnwright in slot three. The test dispatched the NPC's ordinary say and confirmation events, started a fresh zone for each release, cast both spells while the discipline was held, and checked that the release cleared the planted stone. A third process confirmed class 17 membership was gone and both spells had lost cast eligibility. Character 23 retained Cleric.

The driver supplies a local client object and already-engaged NPCs. Spell timing, mana, target selection, native child spell damage, database writes and quest dispatch run in the zone. Player-visible character selection, camp and reconnect still require the RoF2 client. The workspace MQ distribution contains binaries and macros. Its archive and unpacked copy contain no C++ SDK or class registration implementation.

For reproduction, build `build_zone_probe.py` with `zone_spell_probe.cpp` beside it after the candidate zone build. Run the world probe's `seed`, `create` and `list` actions in a fresh scratch database before using the zone runner. Use the same temporary Docker build path for all calls.

```powershell
$actions = 'seed', 'first', 'relog', 'adopt2', 'release2', 'released2', 'adopt3', 'release3', 'released3'
foreach ($action in $actions) {
    python docs/qa/cairnwright-level-one/run_zone_probe.py $buildDirectory $action
    if ($LASTEXITCODE -ne 0) { throw "Zone test failed at $action" }
}
```
