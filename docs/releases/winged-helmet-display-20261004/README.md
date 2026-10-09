# Classic winged helmet registration repair

October 4, 2026. Source cc78f96 is on main and signed release 2026100402 is public
under the owner's already-authorized main/live deployment.
The owner reported Camil Swiftwolf bareheaded in East Commonlands with Classic
models forced. Newer/Luclin models are not required for this asset.

## Cause and evidence

Both installed clients matched signed release 2026100401. The running process
was E:/Nightcap/eqgame.exe. Camil NPC 999521's live content row was race 5,
gender 0, helmtexture 90, texture 3, herosforgemodel 0. The owner's screenshot
showed the Classic High Elf bare head. This is a confirmed failed native test,
not completed visual acceptance.

The pinned EQGraphicsDX9.dll (SHA256
ade556b68e98f6f39c5578f70431e11c0b9babcc15b8571eb22cf1e2b654417e)
loads skeleton alternate meshes at 0x1001e538. At 0x1001e5f8..0x1001e669 it
scans consecutive 0x36 fragments around the skeleton's first referenced mesh.
The original HIM mesh block was fragments 11243..11248; appended HE90 was
20351, separated by non-mesh records. Thus the native actor never registered it.
The head-name classifier accepts material 90; enabling modern models is not a fix.
The read-only disassembly is retained in native-contiguous-head-registration-proof.txt.

## Repair and verification

Insert HE90 at the end of each existing Classic mesh block. Put its material
dependencies before the block. Relocate all typed references with strict
coverage of the pinned archives' fragment kinds. Preserve original geometry,
animation, strings, materials and textures; only fragment IDs move.

Tests reproduce the old append-only failure despite the named mesh existing,
discover all 24 new heads through their skeletons, and recover every original
fragment byte after inverse relocation. Independent review also verified all
new material dependencies precede their consumers and every HE90 is within the
native scan range. Canonical generation changes only the two global archives.

Published release 2026100402:

| Archive | SHA256 |
|---|---|
| global_chr.s3d | 931ecab1081aa93c9d3b55fed275624dcec2f042d07b61c8e2a36f0b0404f3f4 |
| global4_chr.s3d | 6bd94c366fd4613583258459b2d1329d17a39573f549dee02f996cd5a972b548 |

All 24 Python tests passed. Independent signature/hash verification covers the
48-file release against the key shipped in launcher 0.3.1. Public channel SHA256:
6d4acb96980ba7f1292c6f11c6ebfdc5c7cb0ae3efaf6a6ad27a15678dada867.
Publication preserved all service identities/start times; game and DB are
healthy, and gateway/web/tunnel are running. Database content, server binaries,
desktop launcher and the other 46 client files are unchanged.

## Exact native QA still required

1. Exit EverQuest fully and use the normal Nightcap launcher to install the
   higher game release. Keep Classic models forced.
2. Enter East Commonlands and inspect Camil Swiftwolf: silver/gold shell and
   both tall pale wings must replace the bare head, follow his head, and remain
   visible from front, side and rear.
3. On a character with Paladin, equip item 990500 in the head slot, then remove
   it. Check appearance changes, head attachment during movement, and the
   recorded Classic stats. Check secondary/tertiary Paladin eligibility and
   rejection without Paladin.
4. Check the remaining original races/genders, ordinary head variants, zone
   changes and crowded-scene performance. Reference-image fidelity is still open.

No game restart or database change is required for this archive repair. Camil's
material 90 and the item are already loaded. Recover by publishing reviewed
archive bytes under another higher signed release, never by decreasing the
channel release number. Operation scripts/evidence live in
E:/EQ_Local_Dev/artifacts/winged-helmet-display-20261004/.
