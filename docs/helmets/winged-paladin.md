# Winged Paladin helmet

Status: QA candidate, October 4, 2026. The item exists in the live database;
the required item-cache refresh is awaiting explicit restart approval.
No native wear verification or Camil appearance change is claimed.

The owner's four classic character-window references are the visual authority:
silver domed shell, gold perimeter and face edging, dark open face, narrow nasal
guard, and two tall ivory/silver feathered wings. Model the front, side and rear;
retain editable Blender geometry and verify the exported mesh in Unity.

The new head-slot item is Paladin-only. Compare its stats to original Classic
raid helmets in the current database; no heroic stats, focus effects, haste,
regeneration or other later-era power. Quest acquisition is excluded.

The owner initially requested every Nightcap race, then explicitly excluded
later races because they will be disabled. Scope is now the 12 original races,
both genders, using Nightcap's default Classic models. Iksar, Vah Shir, Froglok
and Drakkin are excluded. The client candidate adds 24 HE90 head variants.
High Elf is HIM/HIF; ELM/ELF is Wood Elf. Camil is High Elf (race 5).

The source mesh is editable in Blender, exported to FBX and imported into a
separate visible Unity inspection scene. The reduced game mesh has 3,765
triangles. All metal uses the unchanged humch0301.bmp human plate bitmap.

Current candidate is client-candidate-05, installed only into E:/Nightcap_QA
as signed local QA release 2026100401. It preserves the verified public
2026100203 release's 46 existing files and adds the two global archives.
The public channel and E:/Nightcap remain unchanged. The native launcher
bootstrap passed; the client is open at its EULA/login flow.
All original Classic WLD fragments and archive textures
are retained byte-for-byte. Camil remains at head material 3.
The later-race native Hero's Forge experiment is superseded and is not part of
the deliverable; no changes to native armor tables are needed for this scope.

Acceptance requires a distinct wearable RoF2 appearance, correct head attachment
and equip/unequip behavior, preserved ordinary helmets, and Camil wearing it in
East Commonlands after the asset and item are verified. A Blender render or item
row alone does not establish in-game completion. Record every unverified race,
gender and model mode explicitly.

Implementation order: inspect existing classic-model/PFS tools and head selection;
build the source mesh in visible Blender; export and inspect in Unity; package a
bounded client asset change and test in a separate QA client; define guarded item
SQL and rollback; verify wearable behavior; equip the verified Camil NPC with
scoped saved-state handling. The original Client_RoF2_Dev directory is read-only.

Sources consulted:
- https://docs.eqemu.dev/client/guides/file-formats/wld-by-windcatcher/
- https://docs.eqemu.dev/client/misc/wld-editor-suite/
- https://github.com/nickgal/quail

The similarly named EQ2 Winged helm search result does not establish a matching
model or a usable source asset. Build from the supplied references unless a
verified matching source is discovered.

## Item and operational state

Item 990500, **Winged Helm of the Dawn**: head slot, Paladin mask 4,
original-race mask 4095, material 90, AC 18, HP 25, mana 25, STA 5, WIS 7,
MR 10, FR 5, CR 5. Weight 4.5, no trade, magic; no augment slots or effects.
This is a modest Classic raid reward above Valorium Helmet (AC 17, mana 15,
WIS 7, MR 13), exchanging three magic resistance for health, mana, stamina
and fire/cold resistance. It adds no later-era scaling multipliers.

The guarded migration clones all columns from item 4851 with a temporary table,
checks the exact template and vacant ID/name, then verifies the complete new
row. A full live backup was gzip-validated (444,489,968 bytes uncompressed),
and insertion was successfully rehearsed with rollback before creation.
Backup SHA-256: 8a63123584ac7e48ec820aee71c0deea7320130e7bd91af23c1b5a81afd089d8.
Remote evidence: /opt/nightcap/backups/winged-helmet-20261004/.
Local evidence: E:/EQ_Local_Dev/artifacts/winged-helmet-20261004/.

Automatic approval review rejected a live gateway stop/game restart because
the initial zone-log check did not establish that connected players would be
unaffected. No service was stopped. Explicit restart approval is pending.
The earlier unrelated player-record lookup was also rejected and omitted;
all subsequent content queries were restricted to Camil, the template and
the reserved item. Player selection/temporary grant awaits the owner's choice.

## In-game QA still required

1. Approve and perform the brief game-service restart. Verify identical native
   binaries, healthy login/world/zones, the new name in shared/items, and reopen
   the gateway. Do not treat the database row alone as loaded server content.
2. Owner logs into E:/Nightcap_QA and designates a test character. Preserve its
   existing head item. On a build with Paladin, summon 990500 and equip it.
   Verify displayed stats, head attachment, front/side/rear shape, animation,
   lighting, removal/re-equipping, zoning and reconnect. Reject on missing head,
   missing texture, face clipping or native errors. Compare stock plate afterward.
3. Check both genders of the twelve original races with authorized GM illusions
   or test characters. Verify Paladin secondary/tertiary-class eligibility and
   rejection on a character with no Paladin class. No later races are included.
   Current evidence is decoded-archive rendering for all 24, not native play.
4. Compare the four supplied reference images with the native render; obtain
   owner visual acceptance. Unity and Blender rendering are not substitutes.
5. Only after the wearable check, capture fresh Camil 999521 preimages, apply
   head material 90 while preserving face, body, tint, weapons and position.
   Refresh East Commonlands and preserve its saved state unless a fresh capture
   shows a specific equipment conflict. The October 4 Camil cache row 66432
   has no saved loot/equipped item instances, and the cache schema has no helmet
   appearance column; deletion is not presently justified. Recheck after the
   final zone shutdown. Prepared forward/rollback SQL is in the local evidence
   directory's camil-plan folder and has not been applied.
   Verify Camil in person at the current compact tunnel class area. No quest,
   loot source or acquisition mechanic is added.
6. Publish a signed production client release through the existing pipeline
   after acceptance; verify unchanged baseline files and reversible installation.

## Reproduction and known limits

Editable source: assets/winged-helmet/winged-paladin-source.blend (helmet scene
only, packed original metal texture). The FBX is the Unity inspection export;
helmet-game-mesh.json is the reduced native export. The archive builder pins
the two original source hashes and refuses source-client writes or an existing
output directory. The 24-fit sheet decodes candidate 04; candidate 05 has the
same geometry and adds source-hash enforcement/audit metadata.

Use tools/build_winged_helmet_blender.py in a clean Blender scene, then
tools/export_winged_helmet_blender.py. Build native files with
tools/build_winged_helmet_client.py --client <read-only-client> --mesh
assets/winged-helmet/helmet-game-mesh.json --output <new-directory>.
The original archives are intentionally excluded from version control.
Install through the signed launcher, not by modifying Client_RoF2_Dev.
Nightcap's existing native model policy forces Classic player models even
when older eqclient.ini preferences contain UseLuclin*=TRUE.

Validation: 12 helmet archive/item tests and three PFS block-format tests pass;
nightcap-package Go tests pass.
Reopening the packed Blender source in a separate headless process reproduces
the exact native mesh SHA-256 8d387f742f1f7ef571926abe3f0d9938cb04ee993a0a1c41d9df4354d3db909c.
The local evidence directory also contains camil-high-elf-packaged.png, a
three-quarter inspection of the decoded HIM head. This is a Blender preview
of packaged geometry, not an in-game screenshot or owner visual acceptance.
The packaged mesh stays below 4,096 triangles including the retained face for
each fit; all original fragments/strings survive, bone indices and material
dependencies validate, and malformed/colliding inputs fail closed.
