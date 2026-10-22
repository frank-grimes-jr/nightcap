# Phase 67 — Classic robe bodies

Date: 2026-10-22. Status: main PR276; signed game2026102201 published for live
testing with owner approval. Owner QA subsequently confirmed waist holes on
Barbarian and Half Elf. PR286/game2026102203 publishes the correction across
all seven races/both genders; native recheck remains pending.

Built missing male/female robe bodies for Half Elf, Wood Elf, Barbarian, Dwarf,
Troll, Ogre and Halfling. Both global archives now retain canonical helmets and
add the missing body through native mesh registration. The standard asset builder,
deterministic/preservation tests, exact native selection fixture and exported-normal
previews support reproduction. Review corrections preserve female Halfling feet
and transport normals through the fitted waist, including its upper boundary.

Cut unnecessary binary hooks, permission changes, forced modern models and new
skeletons. There is no gameplay/balance change. Open risks are native renderer
appearance, pattern/dye behavior, clipping in deep bends, first-person views and
complete animation coverage. No player acceptance is claimed; signed delivery
and recovery are recorded in the release's deployment receipts.

[Evidence, rollback and exact QA](../releases/classic-robes-20261022/README.md)
separate tested source from delivery and native visual acceptance. Whole-wiki
live-testing guidance and installed development knowledge are maintained with it.

The correction replaces pose-dependent overlap with identical native bone-local
waist edges, distributing deformation to avoid inverted faces. Twelve robe,
sixteen helmet and three PFS tests plus independent serialized-archive review
pass. All140 public client files and465 wiki files verify. Current waypoint
assets and matching DLL/catalog remain. [Follow-up evidence](../releases/classic-robes-20261022/waist-correction/README.md).
