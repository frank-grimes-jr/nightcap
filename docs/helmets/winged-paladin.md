# Winged Paladin helmet

Status: deployed to main and OVH for live QA, October 4, 2026. Item 990500
is loaded in the live shared-memory cache, Camil uses head material 90, and
the owner confirms the helmet is visible with Classic models. The shell was too
wide. A narrower fit is prepared as signed release 2026100405, retaining the
current 2026100404 animation proxy. High Elf male is 22.9% narrower; the other
fits are tailored to their exposed face widths. Publication verification and
native fit/player wear QA remain open.
[Snug-fit evidence and exact QA](../releases/winged-helmet-snug-20261004/README.md).

The 2026100402 retest shows the new face cutout but invisible metal. Native
actors use their first mesh's material palette; HE90's separate new palette
was ignored. The shared-palette extension is published in 2026100403.
[Material repair and retest](../releases/winged-helmet-materials-20261004/README.md).

Live QA found Camil bareheaded: the appended HE90 meshes were outside the
Classic loader's contiguous alternate-head blocks. The layout repair for
2026100402 is published; Classic models remain supported and required for this
scope. [Repair evidence and retest](../releases/winged-helmet-display-20261004/README.md).

The owner's latest instruction is to deploy to main and the live server for
testing. This supersedes the earlier requirement to finish the isolated native
wear test first. Promotion, client publication and Camil's appearance update
were completed; native appearance/equip acceptance remains open.
[Deployment and recovery evidence](../releases/winged-helmet-20261004/README.md).

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

Published geometry is client-candidate-05, with the corrected native mesh-block
layout and shared-palette extension in production release 2026100403. This
supersedes the native registration/material failures in 2026100401/02 and
preserves the other 46 client files.
The normal launcher downloads those archives before Play. The original
Client_RoF2_Dev installation remains unchanged.
The repair retains all original Classic WLD data except relocated fragment IDs
and three appended shared-palette entries per actor;
archive textures remain byte-identical. Camil uses head material 90.
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

The owner subsequently approved the restart and explicitly authorized main
promotion and server publication once Codex confirms the result. The graceful
game-service restart completed: world and all twelve zones have new process
start times, all three native binary hashes are unchanged, game health passed,
the new helmet name is present in shared/items, and the gateway reopened.
Local and remote refresh.json record this verification. This supersedes the
earlier automatic-review restart rejection; no further restart approval is
pending. The unrelated player-record query that review rejected was omitted.
Player selection/temporary grant has not occurred. The owner elected to test
on the live server instead of continuing the isolated login workflow.

Production release 2026100401 is signed and published on play.nightcapgame.org.
Independent verification against the public key shipped in launcher 0.3.1
passed over public HTTPS for all 48 files (160,550,091 bytes). The 46 prior files have identical
sizes and SHA-256 hashes; only global_chr.s3d and global4_chr.s3d are added.
Channel SHA-256: b08a777d02cba20d9daec640d839b22e81caa518597857ff78845779a5c129bc.
The signature expires November 3, 2026 at 14:54:51 UTC. Publication preserved
the desktop launcher, starter ZIP and guide. A subsequent controlled refresh
activated Camil's guarded helmtexture 3-to-90 change, preserved his one saved
state row, and verified healthy game/database and running gateway/web/tunnel.
Fresh backup: /opt/nightcap/backups/winged-helmet-20261004/camil-live/peq-before.sql.gz.
SHA-256: 14f910dc73b67a2c6fd0caa1f6fd57facbea39baebb88e16d7e4b2b117e3d5a0.

## In-game QA still required

1. Completed: approved game-service restart, unchanged native binaries, healthy
   game service, all new zone processes, the helmet name in shared/items, and
   reopened gateway. This proves cache loading, not native client wear.
2. After patching through the normal launcher, the owner logs into the live
   server with a test character. Preserve its
   existing head item. On a build with Paladin, summon 990500 and equip it.
   Verify displayed stats, head attachment, front/side/rear shape, animation,
   lighting, removal/re-equipping, zoning and reconnect. Reject on missing head,
   missing texture, face clipping or native errors. Compare stock plate afterward.
3. Check both genders of the twelve original races with authorized GM illusions
   or test characters. Verify Paladin secondary/tertiary-class eligibility and
   rejection on a character with no Paladin class. No later races are included.
   Current evidence is decoded-archive rendering for all 24, not native play.
4. Compare the four supplied reference images with the native render. The owner
   explicitly requested live deployment before this test. Unity and Blender
   rendering are not substitutes for native wearable verification.
5. Camil's deployment is complete: fresh stopped-server capture, full backup,
   rolled-back rehearsal, and exact afterimage prove only helmtexture changed.
   His saved state had no loot/equipped instances and was retained. Verify his
   rendered head in person at the compact East Commonlands tunnel class area.
   No quest, loot source or acquisition mechanic is added.
6. Publication is complete and all public file hashes verify. Confirm the normal
   launcher displays release 2026100401 and applies the update before Play.

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
The canonical tools/client_gameplay_assets.py generator calls the same native
helmet builder before writing its audit. A fresh generation reproduced all
44 gameplay files byte-for-byte from the prepared release, including the two
globals; future releases do not require manual archive/audit composition.
Nightcap's existing native model policy forces Classic player models even
when older eqclient.ini preferences contain UseLuclin*=TRUE.

Validation: 13 helmet archive/item tests, five gameplay-generator tests and
three PFS block-format tests pass; nightcap-package Go tests pass. Independent
code review found the missing canonical-generator integration; it is fixed
and verified by a fresh full asset generation. The source export currently
assumes the supplied object transforms: apply object rotation/scale before
future edits because the exporter emits local corner normals with world-space
positions. The reviewed source round-trip is unaffected.
Reopening the packed Blender source in a separate headless process reproduces
the exact native mesh SHA-256 8d387f742f1f7ef571926abe3f0d9938cb04ee993a0a1c41d9df4354d3db909c.
The local evidence directory also contains camil-high-elf-packaged.png, a
three-quarter inspection of the decoded HIM head. This is a Blender preview
of packaged geometry, not an in-game screenshot or native visual acceptance.
The packaged mesh stays below 4,096 triangles including the retained face for
each fit; all original fragments/strings survive, bone indices and material
dependencies validate, and malformed/colliding inputs fail closed.
