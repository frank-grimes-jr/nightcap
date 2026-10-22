# Native robe waist binding — October 22, 2026

The owner rejected game2026102203: the gap remains both standing and moving.
Read-only inspection confirms the installed archives and active launcher release
match2203. This is a native loading defect, not a missing launcher update.

Status: PR291 merged to main at `42603ee6b9ef8928698d2c6aac0cc7605196229b`.
Signed game **2026102204** publishes `native-waist-01` for live testing.
All 140 hosted client files and the shipped-key signature verify.
Native visible standing, movement, dye and observer acceptance remains open.

## Proven cause and correction

The generated skirt appends another pelvis vertex group after the torso. The
pinned EQGraphicsDX9 mesh builder calls ID3DXSkinInfo::SetBoneInfluence once per
WLD group. That setter replaces the bone's earlier vertex list. Actual x86
d3dx9_30 execution on the decoded2203 groups loses432 influences across all16
registrations, including181 torso waist copies. All168 decodable stock meshes
in the two reference archives have one group per bone.

`group_vertices_by_bone` now places each bone's vertices in one contiguous group.
It permutes positions, UVs and normals together and remaps polygon indices.
Every ordered triangle's physical attributes, materials and bone assignments
remain exact; all other fragments/textures remain unchanged. Both global archives
ship together. No DLL, permission, quest, server, SQL or player-state change.

The earlier Python/Blender preview expands every group independently and therefore
kept assignments that DirectX discarded. The native wear-selection fixture mocks
graphics callbacks. Neither verified the skinning loader. The shared waist seam
remains necessary, but matching saved coordinates alone was insufficient.

## Verification and exact native recheck

The one-group regression fails all16 old registrations and passes the correction.
Thirteen robe regressions pass. Direct execution of32 old/new influence fixtures
reproduces the old losses and retains every corrected vertex. The durable suite
also runs the real x86 library against all16 generated models plus a failing
split-bone negative control. Set `NIGHTCAP_X86_PYTHON` if the default Python38-32
path is unavailable. `tools/tests/classic_robes_skinning_native.py` uses only
the standard library and does not launch the game or GPU renderer.

`native-loader-disassembly.txt`, `native-checks.json`, `preservation.json` and
`evidence.json` distinguish native-library proof from complete rendered acceptance.
The fixture uses identity vertex remapping; native loader disassembly shows the
same setter after its mesh optimizer's remapping. No full native render is claimed.

To install game 2026102204, fully exit EverQuest, reopen the normal launcher and
press Play. Both wearer and observer update. In East Commonlands, first inspect
Barbarian and Half Elf, both genders, standing still and while turning, walking,
running, casting, sitting and crouching. Expect a continuous waist with no missing
band. Repeat Wood Elf, Dwarf, Troll, Ogre and Halfling; check dyes/patterns, feet,
HE90, ordinary armor swaps, zoning and relog. The original QA checklist still applies.

Recovery uses a higher signed counter and the current complete inventory/pair.
The prior2203 archives preserve the known gap and are emergency fallback only.
No server reload can replace local archives. The protected reference and installed
player folders remain read only. Delivery and whole-wiki review live in `deployment/`.
