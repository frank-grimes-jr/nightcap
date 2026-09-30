# Classic model defaults — September 30 candidate

Status: candidate only; not published or accepted in game.

## Ready-to-use local candidate

Open `E:/EQ_Local_Dev/artifacts/classic-models-20260930/qa/nightcap-launcher-qa.exe`.
It is already configured for its isolated `qa/client` copy and signed release
`2026093003`. Its adjacent launcher state is separate from the production
launcher. The copy is restored to classic defaults and all 46 managed files
are current. Keep the normal installation for production play.

[Verification record](verification.json) pins the final executable and manifest
hashes. Both classic and modern modes completed owned startup/stop checks with
all three feature masks equal to 16383. A missing classic archive was repaired
through the signed updater while the explicit INI opt-in remained byte-identical.
No authentication, rendered model inspection or gameplay acceptance was automated.

## Intended behavior

All Nightcap clients receiving this signed release default to classic player,
magician elemental, skeleton and spectre models. The catalog also covers 98
later remake race IDs, including wolves, bears, orcs, goblins, giants, vampires,
werewolves and other original counterparts. The full mapping and source hashes
are in `eq-client-dll/config/classic-models.json`.

Later-only creatures and playable races with no original counterpart retain
their available model. The owner has not chosen unrelated classic substitutes.
This is an outstanding part of the original request. [Coverage and replacement
choices](scope-audit.md) must be resolved before claiming all-old coverage.

Modern models require a deliberate edit to the game folder's `eqclient.ini`,
followed by a complete client restart:

```ini
[Nightcap]
UseModernModels=TRUE
```

That permits the native model choices. For modern player races and elementals,
also set the desired native preferences, for example:

```ini
[Defaults]
AllLuclinPcModelsOff=FALSE
UseLuclinHumanMale=TRUE
UseLuclinHumanFemale=TRUE
UseLuclinElementals=TRUE
```

Remove `UseModernModels` or set it to `FALSE` to restore classic defaults.
The launcher preserves the INI and the proxy never rewrites it.

## Automated evidence

- x86 proxy builds. Native runtime suite passes, including model preference
  scoping, buffer truncation, both modes, all remap targets, unsupported genders,
  exact native stack conventions at a relocated base, and refusal to patch
  unexpected instructions.
- Exact-client verifier and generated catalog agree on 48 sites.
- All 22 archives pass PFS unpack/repack checks. Inverting their WLD renames
  exactly restores original bytes, including geometry, animations and references.
- Every texture byte matches its original source or its explicit elemental
  palette. Skeleton and spectre imports and all four element assignments pass.
- Packager, preflight and manifest Go tests pass. Packager and proxy share
  generated asset hashes, so an inconsistent classic generation cannot publish.
- Full launcher Go suite and existing gameplay Python tests pass. Frontend and
  Wails QA launcher builds pass. Final signed installation, both startup modes,
  required-asset repair and INI preservation pass on the copied client.

These checks do not establish rendered appearance, animation or zone stability.
Generated artifacts are under
`E:/EQ_Local_Dev/artifacts/classic-models-20260930/`; source client remains read-only.

## Exact owner in-game acceptance

Use the isolated QA client for both modes. Record screenshots and its
`nightcap_dll_<pid>_<creation>.log`. Check `Model policy: classic defaults` and
proxy `0.7.0-dev`; required/enabled/applied masks must all be 16383.

1. **Inherited settings:** retain existing `UseLuclin*=TRUE`, remove only the
   Nightcap opt-in, launch, and inspect character selection and a Human/Iksar
   character in East Commonlands (`ecommons`). Both should use their original
   model, with armor, held weapons, movement and casting animations intact.
2. **Magician pets:** on a Magician or legal multiclass character summon the
   highest available earth, fire, water and air pets in turn. Expect the old
   elemental mesh with earth/brown, fire/orange, water/blue and air/cloud textures.
   Attack an appropriate test target; verify idle/run/attack/death animations,
   all three pet roster entries, selected/shared commands and worn pet gear.
3. **Skeletons:** inspect ordinary skeletons in Field of Bone (`fieldofbone`)
   and a Necromancer pet; inspect Iksar skeletons in Kurn's Tower (`kurn`). Use a
   disposable GM test character with temporary race illusions to cover races
   60, 161, 234, 349, 367, 484, 604 and 606. Race 604 should be the original
   skeletal dragon (122); 161/606 should be original Iksar skeletons; the other
   listed humanoid skeleton remakes should use the original skeleton (60).
4. **Spectres:** inspect the spectres in Oasis of Marr (`oasis`) and cover races
   85 and 485 on the disposable GM test character. Expect the original robed
   spectre with its original face, scythe and animations.
5. **Other remakes:** in East Commonlands inspect wolves, bears and orcs. In
   Blackburrow inspect gnolls; in Solusek's Eye inspect goblins. Check old-model
   skin variations, heads and equipment. Also spot-check remakes 479, 480, 482,
   458, 433 and 524 on the GM test character. No invisible actors, modern texture
   overlays, frozen poses or missing equipment are acceptable.
   Also cover 481 (original scaled wolf, race 42/gender 1), 566 (classic Human),
   624 (classic Ogre) and 678 (classic Erudite). Test both humanoid sexes, armor,
   held weapons and casting; modern opt-in must restore their native variants.
6. **Lifecycle:** zone between East Commonlands and Plane of Knowledge five
   times; camp and switch characters. Verify models and animations stay correct
   and the client does not crash. Check corpses and resurrected pets as well.
7. **Opt-in:** exit completely, add the Nightcap opt-in and enable the native
   preferences above. Repeat the four pets, skeleton and spectre checks. Expect
   stock RoF2 selection. Run launcher repair/update, confirm the INI edit remains,
   restart and repeat. Remove the opt-in and restart to recover classic defaults.
8. **Failure:** in the disposable QA installation only, rename one `ncm*_chr.s3d`
   file, launch and confirm required startup fails or launcher repairs it before
   Play. Never accept silent missing-model fallback. Restore through the updater.

Document NPC/race, gender, texture, zone, action, mode and screenshot for any
failure. Restore temporary GM illusions before leaving the test session.

## Promotion and rollback

AGENTS.md requires owner in-game sign-off before `test` → `main`. Do not infer
sign-off from automated checks. No server binary, database or quest deployment
is needed for this client-only policy.

Publish the matching proxy, configuration, catalog and full generated gameplay
set through the permanent signed patcher. Preserve user INIs. Do not edit the
original client or remove stock archives. Rollback republishes the previous
reviewed proxy/catalog/config and gameplay inventory under a higher signed game
release; preserve checkpoints and signature checks. New namespaced archives are
inert without the candidate's hooks/import list.
