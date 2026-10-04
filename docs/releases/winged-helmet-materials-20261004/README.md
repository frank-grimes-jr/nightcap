# Classic helmet shared-material repair

October 4, 2026. Prepared for the owner's authorized main/live deployment.
The owner tested 2026100402 and showed Camil's new face cutout without visible
helmet surfaces. Installed archive hashes match that release. The native
registration repair works, but rendered appearance still fails acceptance.

## Demonstrated cause

In the pinned EQGraphicsDX9.dll, 0x100bfc50..0x100bfc88 resolves the WLD 0x36
palette reference at raw offset 16 and stores it in the parsed mesh at +0x58.
The skeleton loader at 0x1001e6ff..0x1001e708 takes the first mesh's palette
only. Thus HE90's independent palette is not the actor's selected palette.

Camil's HIM stock palette has 26 entries, indices 0–25. HE90 uses the existing
face entries plus new metal entries 26, 27 and 28. Those metal entries existed
only in the private palette, outside the actor's selected palette. The exposed
face edge is visible because the stock face entries are valid. Winding checks
show all silver and gold triangles agree with stock winding, ruling out a
wholesale reversed-shell explanation.

Evidence: native-first-mesh-palette-proof.txt and
independent-palette-and-winding-checks.json in this directory.

## Repair

Append the three metal entries to each actor's original shared palette and
point HE90 to it. Preserve every existing slot and its index. Place new material
dependencies before the shared palette, keeping native backward references.
All scoped actors have separate palettes, so this does not extend another
actor's palette. Keep HE90 inside the contiguous native mesh block.

The added regression failed against the 2026100402 builder (ELM's head palette
17970 versus actor palette 17963), then passed with the fix. All original mesh
sections, animation data, textures, original palette slots and names are
preserved. Reference IDs relocate and palette counts gain three entries.
Independent review checked all 26 archive fits (24 original race/gender fits
plus the two Barbarian duplicates in global4), dependency closure/order,
original mesh preservation and native discovery range.

Prepared release 2026100403 changes only global_chr.s3d and global4_chr.s3d:

| Archive | SHA256 |
|---|---|
| global_chr.s3d | 52bd794548e12f90e147d17f4f16871286564fea9a38a907246adec71d1026af |
| global4_chr.s3d | 11952fc236d99e0e7e79a81a388da9e5d07e0ab4a48adcebe7946def6e4b413e |

## Native retest

Fully exit EverQuest, install the higher release through the normal Nightcap
launcher, and enter East Commonlands with Classic models forced. Camil should
show the silver/gold shell covering the cutout and both tall pale wings. Check
front, side, rear and head movement. Then test item 990500 equip/unequip on a
Paladin-bearing character, other original race/gender fits, and ordinary armor.
Native appearance, reference-image fidelity and wearable-item acceptance remain
pending until actually observed. Newer/Luclin models are not required.

No database write or server restart is needed: material 90 and item 990500 are
already active. Roll back client assets only through a new higher signed
release. Operation artifacts are in
E:/EQ_Local_Dev/artifacts/winged-helmet-materials-20261004/.
