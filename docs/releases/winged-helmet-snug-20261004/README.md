# Snug Classic winged helmet fit

October 4, 2026. Signed candidate **2026100405** is prepared against live
2026100404. Publication verification is pending. The owner authorized main and
server publication for live testing; this refinement continues that scope.

The latest owner screenshot confirms Camil's helmet renders with Classic
models. Its shell and cheek plates sit too far from his face. The old fit used
bare-head extents containing hair and ears, plus an oversized male High/Wood Elf
override. The new lateral fit measures the exposed HE0001 facial surface, keeps
8% width clearance, and caps this first reduction at 25%. High Elf male narrows
22.88%; all 24 fits narrow 5.7-25%. Wing roots move with the supporting shell.

The source silhouette, height, depth, original face/jaw geometry and textures
are retained. Six fits receive a small front/back position correction so the
narrowed elliptical crown still encloses the forehead. Camil moves forward
0.0297 native model units. No item, NPC, loot, spell, server binary or DB change
is required. Item 990500 and Camil 999521 remain configured as before.

## Verification

- 27 Python helmet/item/PFS/gameplay tests pass.
- Blender shows decoded native heads for all 24 fits, plus High Elf front,
  side and rear comparisons. The first narrow candidate exposed a forehead
  triangle; the final clearance correction removes it.
- Unity 6000.5.7f1 imports and renders all 24 decoded heads with 39 native
  texture materials in a separate inspection scene.
- Independent review verifies all 26 archive fits against 758 actual triangular
  crown planes, both before and after native vertex quantization. Upper facial
  surfaces remain inside the crown, including the brow band.
- Source textures, stock meshes, actor palette extensions and contiguous head
  registration are preserved. The material-90 visibility repairs remain intact.
- The signed package verifies against the public key shipped in launcher 0.3.1.
  Only global_chr.s3d and global4_chr.s3d differ from release 2026100404;
  the other 46 files retain the animation repair and existing client behavior.

[Final High Elf comparison](../../../assets/winged-helmet/camil-snug-comparison.png)
and [all 24 fits](../../../assets/winged-helmet/classic-24-snug-fits.png).
The preview uses default face textures; Camil retains his in-game face and tint.

Reproduce the independent geometry audit with `check_faceted_crown.py --repo
<checkout> --client <original-client> --candidate <generated-archive-directory>
--result <new-json-path>`. The candidate directory must contain helmet-audit.json
and both archives. Results are retained in faceted-crown-audit.json.

Local build/publication artifacts:
`E:/EQ_Local_Dev/artifacts/winged-helmet-snug-20261004/`.
The original source client is read-only throughout.

## Exact native retest

1. Exit EverQuest fully, then press Play in the normal Nightcap launcher after
   release 2026100405 is public. Keep Classic models enabled.
2. Inspect Camil Swiftwolf in East Commonlands from the front, both sides and
   behind. Expect the crown/cheeks closer to his head, with no forehead poke,
   eye obstruction or detached wing roots. Observe idle and turning animations.
3. On a Paladin-capable test character, equip item 990500 in the head slot;
   confirm its appearance, stats, removal and replacement with a normal helmet.
4. Check both genders of all 12 original races, including small/+X-facing races
   and broad Troll/Ogre heads. Later races remain excluded.

Only Camil's prior visibility is owner-confirmed. The refined fit, player
equip/unequip, animation clearance, all-race acceptance and reference fidelity
remain unconfirmed in the native game. These previews do not close those gates.

Recovery: retain the previous signed channel in the scoped server release
directory. If reverting after clients have observed this release, publish the
previous helmet archives with all current other assets in a higher generation;
never move the signed release counter backward.
