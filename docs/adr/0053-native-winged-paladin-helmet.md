# ADR 0053: A numbered Classic head variant for the winged Paladin helmet

Date: 2026-10-04. Status: candidate; native gameplay acceptance pending.

The owner wants the classic artwork's tall winged Paladin helmet as a new
wearable item, with the original EQ visual language. No verified matching EQ2
model was located. Replacing existing plate heads would alter unrelated items.

Create editable Blender geometry, inspect FBX in Unity, then append HE90 native
WLD head meshes to the original global character archives. Retain the stock
face and animated jaw/neck bones, adapt the shell to each original race/gender,
and use the unchanged human plate bitmap. Item material 90 is below the native
240–255 Velious remapping range. Pin the source archives, retain their original
fragments/textures, and deliver both archives through the signed installer.

The owner excluded later races after initially requesting all Nightcap races.
This candidate therefore covers twelve races and two genders, under Nightcap's
default Classic-model policy. Optional modern player models are not validated.
High Elf is HIM/HIF, distinct from Wood Elf ELM/ELF; Camil uses HIM.

The game mesh is 3,765 triangles before the retained native face, under 4,096
total per fit. This is denser than stock Classic heads; crowded-zone performance
remains a native QA check. Material 90 availability and direct mesh lookup have
been inspected in the pinned client, but archive decoding alone cannot prove
successful equip behavior. The owner subsequently requested direct main and
live deployment to perform these checks on the server. Camil's appearance and
the production archives may be deployed under that release-specific exception;
native wearable and visual acceptance must remain explicitly open.

The item is a modest Classic raid reward using a guarded Valorium clone.
Paladin ownership is required through the existing Nightcap class handling;
no new multiclass rule, acquisition quest, merchant entry or loot source is
introduced. Camil's appearance uses the verified material after acceptance.

Alternatives: repurposing stock plate misses the defining silhouette; replacing
an existing head appearance changes unrelated gear; Hero's Forge requires a
different later-model attachment pipeline and is outside the revised scope.
