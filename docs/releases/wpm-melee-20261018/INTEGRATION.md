# Shared scaling integration handoff

The completed WPM/pet candidate remains an uncommitted working tree on
`feature/thj-pet-scaling`, base `a8e0a91382c23e52a0ffb2b79fb3f2c0c131f76a`, in
`C:/Users/verre/Documents/Codex/2026-10-18/goa/work/thj-pet-scaling`.
No main promotion, deployment, signing or publication occurred. The paired
native manifest pins118 overlay files and2826 retained source files. Build and
test readiness is recorded in README.md, COMPARISON.md and evidence/.

The separately requested item/spell parity work should integrate this exact
candidate, preserving the following boundaries:

- WPM owns held-class melee, heroic STR, shield/sustain mechanics, the earned AA
  policy and named melee item effects. Pet work owns full equipment instances,
  independent augments, own SD/HA plus capped half-owner inheritance and caster
  AA transfer. These paths are implemented and verified together here.
- `zone/effects.cpp`, `zone/mob.cpp`, `zone/attack.cpp`, `zone/spell_effects.cpp`
  and `common/ruletypes.h` are shared integration surfaces. The current candidate
  retains percentage SD/HA and percentage HA runes. Additive spell damage,
  per-tick DoT behavior and scoped heroic INT/WIS belong to the separate parity
  change. Its tests must recompute inheritance, pet effects and WPM sustain;
  the current comparison numbers are not valid evidence for a changed formula.
- Pet content currently uses floors for33 gear rows; the separate exact
  Legendary-to-Ascended item override work must reconcile those rows explicitly.
  Preserve existing weapon ratios, augment/cosmetic sockets, proc identities,
  owner receipts and starter gear unless a reviewed new specification changes
  them. Do not run independent full-row migrations over each other's afterimages.
- The content generators retain dated preimages. Assemble a combined reviewed
  row transition before activation. Pet Seru drop988610 and WPM drop988622 already
  compose safely in either retry order; preserve both links and original loot.
- Keep the narrow RoF2 approved-rank compatibility change in `zone/aa.cpp`.
  It is required for Companion's Fury IV under the actual native expansion mask.
  Do not widen profile masks or remove native/policy/class/prerequisite gates.
- Rebuild world, zone and cache loader, regenerate paired item/spell caches and
  the client spell/dbstr delta after integration. Repeat both WPM and pet native
  scenarios plus content/AA regressions. Current 134 tests and26 scenarios apply
  only to the hashes recorded here. Signed client assembly must retain the then
  current signed base, including unrelated October18 travel repairs.

The native results exercise individual mechanics and one captured boss. They do
not approve final pack/raid balance or replace owner RoF2 acceptance. The release
gate and receipt-preserving recovery remain in ACTIVATION.md.
