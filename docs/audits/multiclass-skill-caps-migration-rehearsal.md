# Epic #10 skill-cap repair rehearsal

Date: 2026-07-28
Status: passed; live application completed and independently recorded

## Inputs and isolation

- Live snapshot:
  `backups/peq_20260728_193437_epic10_pre_migration.sql.gz`
- Snapshot size: 46,304,776 bytes
- Snapshot SHA-256:
  `a4db1ca65a18ebdd2049eda426805cd7cd1ec5ce313ea7d9bf7668170942352c`
- Snapshot gzip integrity: passed before restore
- Rehearsal container: `nightcap-peq-rehearsal`
- Isolation: no published host port and a separate anonymous MariaDB volume
- Canonical container: `nightcap-peq-baseline`
- Canonical evidence:
  `docs/audits/skill-caps-diff/live-only.csv`
- Canonical evidence SHA-256:
  `8df2e24f7866e2ef6f49396212d31af57456403595ca1ec643106df85d331270`

The restored copy contained 236 tables and 74,449 `skill_caps` rows, matching
the live pre-migration state.

## Repair contract

`tools/repair-multiclass-skill-caps.ps1`:

- refuses the live container unless `-AllowLiveTarget` is explicit;
- validates all container, database, credential, and SQL identifier arguments;
- pins and validates the complete removal CSV by SHA-256 and row count;
- compares the target to the isolated canonical table before and after work;
- requires exactly 16,090 live-only rows, zero canonical-only rows, and zero cap
  mismatches before repair;
- retains the complete original rows, including IDs and `class_`, in
  `skill_caps_epic10_removed`;
- validates that rollback snapshot against the original target before deletion;
- performs deletion, validation, and commit or dry-run rollback in one
  transaction;
- validates rollback keys and collision absence before restoration.

## Integration sequence and result

`tools/tests/test-repair-multiclass-skill-caps.ps1` ran the following sequence
against the restored copy:

1. Supply an incorrect expected target count: rejected with 74,449 rows intact.
2. Dry run: 16,090 rows deleted and transaction rolled back; 74,449 remain.
3. Apply: exactly 16,090 rows committed; 58,359 remain.
4. Exact comparison: zero live-only rows, zero canonical-only rows, and zero cap
   mismatches (`exact_canonical_match`).
5. Rollback: all 16,090 retained rows restored; 74,449 remain.
6. Reapply: exactly 16,090 rows committed again; 58,359 remain.

Final result: pass. The rehearsal copy is left in the repaired canonical state.
No live database row was changed during rehearsal.

## Live gate

Before live application:

1. Stop gameplay processes so the table and shared-memory generation are
   quiescent.
2. Rerun the exact canonical relationship assertion.
3. Apply with the explicit live-target override.
4. Confirm 58,359 rows and an exact canonical comparison.
5. Regenerate shared memory, restart every zone, and verify process timestamps.
6. Retain both the full database backup and `skill_caps_epic10_removed` until
   post-restart QA passes.

All six steps completed on 2026-07-28. See
`docs/audits/multiclass-skill-caps-live-application.md`.
