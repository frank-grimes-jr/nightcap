# Classic race robe visibility — October 22, 2026

Status: original PR276/game 2026102201 added robe bodies. Owner QA rejected
both the original waist and the shared-seam correction in game 2026102203.
The gap persisted while standing and moving with the correct installed archives.
PR291/main `42603ee` and signed game **2026102204** now correct the native bone
assignment loss. All 140 hosted client files, signature and current DLL/catalog
pair verify. Native visual acceptance remains open. The protected reference and
installed player client remain read only. See [native binding correction and
exact recheck](native-skinning/README.md). Earlier evidence retains its historical
scope; publication alone does not establish that the visible gap is resolved.

## Result and boundaries

Adds male/female robe bodies for Barbarian, Wood Elf, Half Elf, Dwarf, Troll,
Ogre and Halfling: 14 actors in `global_chr.s3d`, plus the duplicate Barbarian
pair in `global4_chr.s3d`. These actors previously had no body 01. The exact
native wear-material routine already selects body 01 for all 12 Classic races;
held-class equipment permissions are a separate, existing policy.

Skirts use native Human/Gnome geometry fitted in P01 standing space and mapped
to target bones by anatomical name. Upper-body UVs, hands, feet, heads,
skeletons, animation tracks and HE90 helmets remain. Generation follows the
canonical helmet transform. All original fragments survive inverse-reference
byte comparison except the five appended shared palette slots. Existing texture
bytes are unchanged; materials 10–16 use the original CLK04–10 families.

No server binary, quest, SQL, character data, eligibility, stats, spell power or
progression changes. Scope is the default Classic model path; modern or other
race models are not introduced. Architecture: [ADR 0065](../../adr/0065-classic-race-robe-assets.md).

## Reproduce

Use Python 3.14 with NumPy 2.4.0 (`tools/classic-robes-requirements.txt`) in the
asset-build environment. From the checkout root, choose a new output directory:

```powershell
python -B tools/build_classic_robes.py --client E:/EQ_Local_Dev/Client_RoF2_Dev/everquest_rof2 --helmet-mesh assets/winged-helmet/helmet-game-mesh.json --output E:/EQ_Local_Dev/artifacts/classic-robes-20261022/candidate-new
python -B -m unittest discover -s tools/tests -p test_classic_robes.py -v
python -B -m unittest discover -s tools/tests -p test_winged_helmet.py -v
```

The normal `tools/client_gameplay_assets.py` builder applies the same transform
and records `robe_archives` in its audit. Generating assets does not activate them.
For previews, run Blender in background with `--python tools/preview_classic_robes.py
-- CANDIDATE NEW_OUTPUT`; optional `--pose L01 --frame 3 --angle 65` inspects movement.

Build the mapped-native fixture in a disposable directory from an x86 Visual
Studio developer prompt:

```bat
cl /nologo /EHsc /std:c++17 /Fe:classic-robes-native.exe /Fo:classic-robes-native.obj CHECKOUT/eq-client-dll/tests/classic-robes-native.cpp /link user32.lib advapi32.lib
classic-robes-native.exe E:/EQ_Local_Dev/Client_RoF2_Dev/everquest_rof2/eqgame.exe
```

It verifies the pinned executable hash, executes original wear-material RVA
0x99f0 and normalization RVA 0x9770, and checks 336 equip/remove cases across
12 races, both genders and seven robe materials. The actor-name and graphics
callbacks are mocked; the entry point and renderer never run. Pattern calls
must occur exactly once on equip with `material - 6`, and never on removal.
This proves native selection and normalization, not visual or dye acceptance.

The animation-family resolver was separately executed at RVA 0x6a60. Human,
Barbarian and Half Elf use same-sex Wood Elf; Halfling/Gnome use same-sex Dwarf;
Troll/Ogre use OGF. Actor-specific tracks take priority. Transform decoding was
cross-checked against the primary [Lantern extractor](https://raw.githubusercontent.com/LanternEQ/LanternExtractor/master/LanternExtractor/EQ/Wld/Fragments/TrackDefFragment.cs).

## Evidence and limits

Regression coverage checks all 16 native registrations, deterministic output,
every original fragment/texture, material dependency order/shared palettes,
existing body/HE90 registration, target bones, feet and invalid application.
The original archives fail all 16 missing-body cases. Foot regression failed
`0 != 46` for female Halfling before its combined FT0001 foot material was
retained. Normal transport now uses the full fitting Jacobian inverse transpose;
numerically differentiated tangents verify perpendicularity under waist shear.

Independent archive review found no layout/preservation issue. Geometry review
identified and prompted correction of female Halfling feet, waist normals and
the native fixture's weak pattern assertion. The owner declined optional
second-model review. Exact results/hashes belong in `evidence.json`.

Blender inspections read actual staged meshes/textures and exported normals.
Front/back P01 and angled L01 frame 3 check silhouette, waist/hem and movement.
They do not execute native animation interpolation or material changes. Large
race waist seams, deep bends, clipping, dyes and first-person behavior remain
native acceptance gates. The preview uses UV V directly; flipping V inverted
faces only in the inspection, without changing game UVs.

## Activation and recovery

The owner approved this main promotion and live-QA publication on October 22:
"Approved. move into main." This is a scoped exception before native acceptance,
not standing permission for future releases. Follow [exact QA](QA.md). Close
EverQuest completely, reopen the normal launcher and press Play to install
signed game `2026102201`. Never modify `Client_RoF2_Dev`.

The publication retains all 136 other signed manifest assets and their URLs,
including the matching DLL/catalog, and replaces only the two archives. Full client
exit/update/relaunch is required; server quest/cache reloads cannot load client
archives. No server restart is needed. Observers need the same asset update.

Rollback both archives together to their exact prior signed pair (including
HE90); if already public, use a fresh signed recovery release and relaunch.
Do not restore player settings or any database state.

## Wiki and milestone assessment

All 21 maintained articles and generated item/zone guidance were assessed.
Equipment, Multiclass, Features, Launcher, home, In development and Recent
changes receive explicit live-testing notices. Commands, catalog values, reward
templates, stats and released mechanics stay unchanged. Existing Keeper source
drift retains its separate evidence; the global ledger is not blindly advanced.
See the initial `wiki-review.json` and current `deployment/wiki-review.json`;
the latter's publication and HTTPS receipts distinguish delivery from native QA.

Built: missing Classic robe assets, canonical packaging, regression/native
fixtures and reproducible previews. Cut: unnecessary native hooks, permission
changes, forced modern models and new skeletons. Open: actual native rendering,
full animation acceptance. Signed delivery is recorded separately; no claim of
owner QA completion.
