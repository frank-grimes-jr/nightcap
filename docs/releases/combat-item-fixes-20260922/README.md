# Combat and tier-item repair candidate

Updated September 27, 2026. Branch `feature/combat-item-fixes-20260922`.
**Not deployed; casting-bar diagnosis and gameplay acceptance remain open.**

## Report and implemented scope

The owner reported a frozen personal casting bar, weak fists on a level-2
Wizard with Monk secondary (reported character Monkdots), and +20 spell/heal
on poor Ascended items. Follow-up confirms every non-instant spell completes
normally while its bar stays frozen, including outside combat. This excludes
melee as a necessary trigger. There is no casting-bar patch in this candidate.

Unarmed combat now resolves Monk/Beastlord membership in every class slot for
fist damage/delay, magical fists, empty offhand eligibility and unarmed damage
tables/bonuses. Equipped weapons and NPC identity retain their existing paths.
The one-argument skill cap now takes the maximum native cap across held classes:
newly seeded Dual Wield can improve instead of stopping at the Wizard's zero
cap. The September 27 local cap data at level 2 is Monk H2H 20 / Dual Wield 19 /
Offense 10 versus Wizard 6 / 0 / 8. The skill regression uses captured native
level-1, level-2 and level-50 caps, including Beastlord's later Dual Wield unlock.
Learned values are not raised automatically; specialization and explicit
class-specific cap queries retain their existing rules.

Tier spell/heal additions use the unscaled base item's strength instead of a
flat stamp. See [the policy decision](../../adr/0047-base-item-spell-heal-scaling.md).
An Ascended Cloth Cap (601001; base 1001, AC 2) changes from 20/20 to 0/0.
The Ascended Cloak of Flames (611621; base HP 50) receives 10/10 of added
spell/heal; strong items may retain 20/20. Existing positive spell/heal is still
scaled by the tier multiplier. Negative native values remain drawbacks.

## Verification

- Ten focused Python/native-method tests and nine balance-audit tests pass, including a red/green reproduction
  of the primary-only skill cap. The compiled fixture uses real fist formulas,
  both weapon damage overloads, empty-hand dual wield, damage tables, cap resolver
  and AddSkill; boundary services/data are controlled fixtures.
- Existing skill lifecycle and Monk special-attack integration checks pass.
- Isolated MariaDB rehearsal changed 93,615 items. All four formula checks passed;
  every other item column was preserved; stale spell/heal preimages and replay
  failed without writes; rollback restored the entire items table exactly.
- Base formula/target identity drift and stale rollback were rejected. A trigger
  forced an after-UPDATE validation failure; both changed rows rolled back exactly.
- Full world/zone build passed. All 335 objects are newer than source restaging;
  56 older objects were explicitly rebuilt before accepting the final binaries.
  All 2,790 source hashes stayed stable and all 56 overlay files match this branch.
  [Native build receipt](evidence/native-build.json).
- Independent review found and resolved offhand, damage-table/bonus and practical
  skill progression gates. Item review accepted the documented guard scope and
  requested additional fault tests. External cross-model review was declined.

Private/local evidence: `artifacts/combat-item-fixes-20260922/` outside this
worktree. Rehearsal schema: `nightcap_spell_rehearsal_20260927` (items only).
The original snapshot SHA-256 is
`bf7008da8dba0338648db1163918902ef969c97218ba8cc2d64cc451d9e9b354`.
The complete restored table fingerprint is
`1a1829e3681965a7f2961230c3e01226df34b122acc379d96269cd8097cc2388`.
The September 27 read-only hosted capture of the same item fields has exactly
the same SHA-256 and the same 93,615-row plan. No hosted migration occurred.
Full-table preservation/rollback evidence is from the isolated local clone. A
final integrity read checked all 308,928 restored rows: every row produced a
valid digest, and the complete table hash still matches the initial preimage.
Target-captured forward/rollback SQL is prepared under
`artifacts/combat-item-fixes-20260922/production-plan-20260927/`; it is not applied.

The read-only balance checker supports `--item-policy base-strength` for a
migrated candidate. Its default remains `legacy-flat`; every report records the
selected expectation. Historical evidence remains unchanged.

## Deployment boundary and rollback

Do not run `tiered_loot_setup.sql` on an existing server: it is a destructive
bootstrap. Capture the intended target read-only with `tier_spell_scaling.py`,
review the generated plan and rehearse forward/rollback on its clone. The CLI
currently captures local Docker peq; a hosted target needs its own capture using
the same SELECT, never reuse local preimages for hosted deployment. Only
`spelldmg` and `healamt` are updated. No rules, inventory ownership or item IDs
are changed. Forward/rollback require an InnoDB items table and fail closed on
missing captured rows or drift in names, formula inputs or the two stat values.
Other metadata (for example class masks, required level and heroic stats) is
preserved, but deliberately not part of the drift fingerprint.

A failed CALL leaves its named procedure behind; investigate the error and
remove only that procedure in the intended target before retrying a newly
reviewed plan. Do not use `--force` or rerun the whole bootstrap. Keep the exact
preimage and rollback generated for the target. Run shared_memory and restart
all zones after an authorized item update. Deploy native binaries only after
the build passes. Main/production promotion needs owner sign-off.

[Exact in-game QA](QA.md) remains required. The balance findings are a candidate,
not proof that every encounter or multiclass build is balanced.

## Casting display diagnostic

The installed default CastingWindow XML matches the pinned RoF2 reference.
Native normal-spell gauge code uses the deadline at local player +0x444,
spell ID at +0x448, clock at +0x154 from the native clock object, and raw spell
cast duration. No reviewed hook directly writes those fields. The earlier
hypothesis about melee animation is not a confirmed cause.

`tools/capture_cast_bar.py` takes an explicit PID, checks its executable path and
pinned executable SHA-256, and opens the process with query/read permission only.
It records the three timer fields for 5-60 seconds while the owner casts. The
file-duration-derived gauge is a reference, not a read of in-memory spell data.
Run against the affected Nightcap process only; other eqgame versions are rejected.
A constant deadline and advancing clock separate timer behavior from a stale
rendered gauge. Live capture and visual confirmation are still required.
