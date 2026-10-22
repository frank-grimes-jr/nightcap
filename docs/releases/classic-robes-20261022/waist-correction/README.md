# Classic robe waist correction — October 22, 2026

The owner supplied a native screenshot showing a hole between the Barbarian
torso and robe skirt and confirmed the same defect on Half Elf. This rejects
waist acceptance of the original game2026102201 assets, also retained by the
waypoint update2026102202. Other races were suspected by the owner; source
inspection found the same unjoined topology on all fourteen added models.

Status: source PR286 merged at `b3cda309c06f79670b95cd3c31995d125ea34bd5`;
signed game **2026102203** publishes corrected `waist-fix-02` for live testing.
Native visual/animation acceptance remains pending. No protected reference or
installed player client was modified. All140 public client files verify; the138
other descriptors and current waypoint assets with matching proxy/catalog0.11.1
are retained.

## Correction and proof

`tools/classic_robe_geometry.py` now joins each skirt's eight-edge boundary to
the native chest's waist using identical bone-local coordinates and pelvis bone.
Separate UV copies retain their existing coordinates; topology and bone arrays
remain unchanged. The same rigid transform therefore preserves the shared seam
through animation instead of relying on overlap in one fitting pose.

The first candidate snapped only the rim. Independent review found inverted
neighboring triangles. The final correction interpolates rim displacement around
the waist and linearly from hem to rim, retaining all original bone assignments.
It recomputes skirt normals, matches native torso normals at the seam, and rejects
collapsed or reversed faces. Preview framing supports a small actor set.

The exported regression failed `0 != 8` on all sixteen original registrations,
then rejected twelve registrations of the rim-only candidate for inward faces.
Final checks: twelve robe tests, sixteen helmet tests and three PFS tests pass.
Independent inspection of the actual final archives found eight oppositely
directed shared edges, no collapsed/reversed skirt faces, outward seam triangles
and consistent normals for all sixteen registrations. Decoded UVs, bones and
polygon arrays match the prior candidate. Front P02 and rear-angled L01 frame3
previews cover the reported races and all fourteen actors. These are not native
visual acceptance. Existing original-fragment/texture/helmet/foot checks pass.

## Native recheck and recovery

To install corrected game2026102203, fully close EverQuest, reopen
the normal launcher and press Play. The observer also needs the update. In East
Commonlands, start with Barbarian and Half Elf, both genders: equip a legal robe,
inspect the waist front/back/sides, hold weapons, turn, walk/run, cast, sit and
crouch. Expect continuous fabric with no background visible through the waist.
Repeat for Wood Elf, Dwarf, Troll, Ogre and Halfling; test armor swaps, zoning,
relog, robe patterns/dyes, feet and HE90. Broader [original QA](../QA.md) remains.

Recovery uses a higher signed counter and a complete current manifest. Reverting
to the prior two robe archives restores the known waist defect; it is only an
emergency regression fallback. Retain the current waypoint assets/DLL/catalog
and player settings. No server restart, quest reload or database change is needed.

`deployment/` records signed bytes, preservation, tests and publication separately
from owner visual acceptance. Wiki impact covers all21 guides/432 generated routes;
seven robe notices describe the correction, preserving current waypoint and
Keeper guidance, commands, item stats and catalog values. Current main class-armor
notices remain explicitly Not released. Wiki20261022-classic-robes-waist-v1
verifies all465 HTTPS files/headers and five private-route denials;16 Linux
recovery tests and actual pointer rollback rehearsal pass. No Nginx reload.
See [delivery evidence](deployment/README.md).
