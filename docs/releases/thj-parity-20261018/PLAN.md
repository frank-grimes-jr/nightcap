# THJ item and spell parity candidate

Owner request: implement the researched item/spell targets, coordinate pet/WPM,
preserve starter progression and prepare one combined candidate for testing.
No production installation, main promotion, or gameplay acceptance is claimed.

1. `config/thj-item-parity.json`, `tools/thj_item_parity.py` and its tests: exact
   per-item numeric overrides with source rows/cells/screenshots and full guarded
   preimages. Exclude augmented, ambiguous and unlabelled evidence. Keep unknown
   fields, item identities, gates, effects and sockets. Clamp intermediate numeric
   values only when a verified top-tier reduction otherwise reverses progression.
   Unobserved ordinary families retain the existing policy; no inferred multiplier.
2. `zone/effects.cpp`, `zone/mob.h`, `common/ruletypes.h` and native tests: separately
   switchable additive direct damage/procs; half effective SD per DoT tick, with
   native critical ratio applied to that contribution. Critical ordering is an
   explicit calibration until stronger evidence exists. Preserve healing/HoT
   coefficients. Add 0.1% per heroic INT/WIS to direct damage/healing respectively,
   after existing focus/item/critical calculation and before final damage caps.
   No conversion into capped SD/HA; no heroic multiplier on DoTs/HoTs. Bard rune
   songs retain instrument scaling but do not gain the new HA rune bonus.
3. Compose the pet/WPM candidate first, parity overrides second. Keep its 750 caps,
   half-owner inheritance capped at375, melee/AA/proc logic and paired client.
   Preserve the separate fixed starter policy and dungeon progression; merge its
   source candidate and prepare guarded item afterimages. Hunt headroom remains
   an explicit Nightcap extension. Catalogs remain gated by their original eras.
4. Verify source-method arithmetic, migration idempotence/drift/rollback, item
   ordering, paired world/zone/shared-memory build, and reproducible native
   encounters. Review the final candidate and document exact in-game QA across
   WPM class orders, caster/DoT and pet controls, Classic and staged later eras.
5. Update CHANGES, status, all-wiki impact and installed skill knowledge. Candidate
   labels remain until the owner tests the combined release.

The riskiest step is composing new damage coefficients with WPM proc sustain and
pet inheritance. Tests must cover Throw Stone once, item opt-outs, hostile NPCs,
critical damage, focus/duration behavior, healing/HoT preservation and Bard runes.
Use isolated database/build paths and pinned source hashes; never modify an active
worktree or use historical content fixtures as a future live activation preflight.
