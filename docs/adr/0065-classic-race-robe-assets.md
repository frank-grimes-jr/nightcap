# 0065: Supply missing Classic robe bodies

Date: 2026-10-22. Status: candidate; native visual acceptance pending.

Classic model selection is intentional. A robe on a Half Elf, Wood Elf,
Barbarian, Dwarf, Troll, Ogre or Halfling previously recolored the ordinary
chest because the archive had no `CODE01_DMSPRITEDEF` robe body. The pinned
RoF2 wear-material routine already selects body 01 for these races. Held-class
equipment eligibility is a separate, existing server/client policy.

Generate the missing male/female bodies from native upper bodies and same-sex
Human/Gnome robe skirts, fitted in the native standing pose and mapped by
anatomical bone name. Retain target skeletons, animations, heads, hands and feet.
The torso and skirt must share all eight native waist edges with identical
bone-local coordinates and pelvis assignments. Pose-space overlap is insufficient:
owner QA exposed a gap on Barbarian and Half Elf. Match the opposite directed
rings and distribute their displacement around the waist and down to the hem;
rim-only snapping folds adjacent faces inward. Recompute skirt normals, retain
the torso's seam normals, and reject collapsed or reversed triangles.
After joining, group all vertices for each bone contiguously, moving positions,
UVs and normals together and remapping polygon indices. The native loader calls
ID3DXSkinInfo::SetBoneInfluence per WLD group; repeated groups replace prior
influences. Owner QA rejected2203 despite closed saved geometry. Real x86 DirectX
checks reproduce lost torso waist bindings and validate the grouped correction.
Offline per-run expansion alone is not a valid native skinning check.
Add bodies to native contiguous mesh registration and append cloth slots to the
shared first-mesh palette. Preserve all old fragments by inverse-reference byte
comparison, apart from the explicit palette extension. Both global archives
must be updated because `global4_chr.s3d` repeats the Barbarian actors.

Use the canonical helmet output as input so HE90 survives. Stage deterministic
PFS archives with original textures, not an executable patch or forced modern
models. The canonical gameplay asset builder applies helmets then robes.
NumPy is an asset-build dependency only. Original client files stay read-only.

Alternatives considered: forcing modern models changes the established visual
policy; changing class/race permissions does not provide geometry; custom new
skeletons or native hooks add unnecessary animation and compatibility risk.
Retargeted rigid Classic skirts can still clip during native animations, so
offline registration, previews and mapped native selection tests do not replace
owner visual QA. No item stats, power, eligibility or progression change.

See [candidate evidence and rollout](../releases/classic-robes-20261022/README.md).
