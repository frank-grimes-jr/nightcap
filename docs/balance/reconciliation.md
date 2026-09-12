# Baseline reconciliation evidence

Date: 2026-09-12
Branch: `feature/baseline-reconciliation`

## History reconciled

The main-checkout onboarding assessment did not account for unmerged local feature
history. The nine substantive mirror differences came from newer `dev` work, and
the live +5/+12/+20 item stamps came from `feature/spelldmg-healamt-scaling`.
Both histories are now integrated in this isolated feature branch, together with
the accepted main mana-gauge records. No active source was overwritten to achieve
parity. The active skill policy is native unlock at value 1 and normal training.

The previously unmirrored active loot hook and RoF2 packet encoding/definitions
are now captured under `server-mods/code/`. The separate held-Monk patch retains
its existing exact source/patched SHA check. This does not claim that every file
in the upstream engine has been audited for custom modifications.

## Automated results

- 43 mirrored files match active content after CRLF normalization.
- The held-Monk integration/patch hash check passes against active source.
- Existing plugin skill policy, lifecycle, trainer, release, and login-banner
  checks pass. These are static integration guards, distinct from runtime tests.
- Exact-client RoF2 patch-site verification passes (read-only client inspection).
- `cmake --build . --target tests -j2` succeeds in the active container build tree.
- All 87 C++ tests pass from `/home/eqemu/server`.
- Eight new Python tests pass for drift detection, missing rules, and C++ result
  validation. The initial RED run failed because the checker was not implemented.
- All 184,920 existing worn tier/epic rows match their expected spell/healing stamp
  formula: 61,635 per ordinary tier and 15 epic variants, zero mismatches.

The first C++ invocation from the wrong working directory failed four IPC tests
because the shared-memory/config paths were unavailable. The executable still
exited zero. The new checker rejects a missing, empty, non-100%, or nonzero-exit
suite result. Re-running in the documented server directory resolved the failure;
no IPC implementation was changed.

Reports: [before](baseline-before.json), [after](baseline-after.json).
These reports cover stored database settings and the listed checks; `passed` does
not certify running-zone rule memory, end-to-end gameplay, or unmirrored engine code.

## AA rule repair

The precondition query proved `Character:AAExpMinLevel` absent from ruleset 1.
Applied the existing `eq-solo-gm/scripts/aa_exp_min_level.sql` unchanged using its
plain INSERT, then verified exactly the intended row at value `1`. No character
data was modified and no spell/healing cap was changed.

Verified full backup: `E:/EQ_Local_Dev/backups/peq_baseline_20260912.sql.gz`
(46,317,106 bytes; gzip integrity passed).
SHA-256: `2C6B7648B37CA4672B688D6B97B0C3749DCFCCC736EA3210995DD94A7F859F91`.

Rollback is removal of only the inserted row, after confirming it still has value
`1` and note `Nightcap: AA XP allowed from level 1 (#37)`; reload rules afterward.
Do not restore the whole database merely to undo this one INSERT.

**Runtime reload pending:** one character was marked in-game, so zones have not
been restarted. The owner has been asked whether to restart now or defer while
calculator development continues. AA behavior in already-running zones remains
unverified until reload and the focused QA below.

## Focused in-game QA for test promotion

1. After rule reload/restart, use a disposable level-1 character in PoK. Run
   `#aaexp 50`; expect a 50% allocation response. Zone to East Commonlands and kill
   level-appropriate bats/snakes; allocation must remain 50% after an XP award.
   The small XP amount need not immediately award an AA point.
2. Run `#aaexp off`, kill another eligible mob, and verify allocation remains off.
3. On a disposable level-50 multiclass character, set `#aaexp 100`, kill an
   XP-awarding mob in Lower Guk, and verify AA experience increases. Camp/relog and
   verify the allocation persists. Do not modify Done or existing characters for QA.
4. On a melee-base caster multiclass control, verify spellbook/gems, mana gauge,
   casting, and zoning; repeat on a stock caster. This is regression QA only; the
   July 28 accepted milestone remains accepted.

The calculator and remaining backlog are still in progress. No test/main promotion
or final balance conclusion is claimed by this baseline report.
