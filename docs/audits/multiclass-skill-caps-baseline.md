# Multiclass `skill_caps` Baseline Audit

Date: 2026-07-28
Epic: #10
Status: canonical baseline acquired; exact migration rehearsal pending

## Purpose

Epic #10 needs native per-class skill unlock levels and caps to remain the source
of truth. The live `skill_caps` table cannot currently serve that purpose because
an older multiclass implementation widened it globally. This audit records what
is known, what is not yet safe to infer, and the gate for repairing the table.

## Hard evidence

- The 2026-06-22 multiclass implementation expanded `skill_caps` while adopting a
  class. `CHANGES.md` records that behavior.
- The 2026-07-16 implementation removed future global widening from
  `plugins/multiclass.pl` and changed runtime authorization to consult each held
  class's native rows.
- Legacy widened rows remain in the live PEQ database. On 2026-07-28, all six
  spell-school skills existed for Warrior (`class_id = 1`) through level 100:

  | Skill | ID | First row | Last row | Rows |
  |---|---:|---:|---:|---:|
  | Abjuration | 4 | 1 | 100 | 100 |
  | Alteration | 5 | 1 | 100 | 100 |
  | Channeling | 13 | 1 | 100 | 100 |
  | Conjuration | 14 | 1 | 100 | 100 |
  | Divination | 18 | 1 | 100 | 100 |
  | Evocation | 24 | 1 | 100 | 100 |

  These are strong contamination controls, not a complete reconstruction of all
  widened rows.
- Every local PEQ backup retained before this audit was dated after the original
  widening and was correctly rejected as a clean native baseline.
- Akk Stack's current `init-peq-database` target references the official PEQ
  package at
  `https://gitlab.com/TheGrandLibrary/db.projecteq.net-dumps/-/package_files/232952944/download`.
  The archive is 32,150,987 bytes with SHA-256
  `ac8649f23d2c3aea2cade138dfe10d46d1b21ad1a80d08ca95f5434fab7f218d`.
  Its files are dated 2025-09-28.
- The dump was imported into the isolated `nightcap-peq-baseline` container,
  which publishes no host ports and shares no volume with live PEQ.
- Exact read-only comparison found 74,449 live rows, 58,359 canonical rows,
  16,090 live-only rows, zero canonical-only rows, and zero cap mismatches.
  Live is therefore a strict superset of the canonical native table.

## Safety decision

Do not delete, rewrite, or rebuild live `skill_caps` from heuristics. A row that
looks unusual may still be a legitimate PEQ era/race/class rule, and the current
table has insufficient provenance to distinguish native rows from widened rows.

`tools/audit-multiclass-skill-caps.ps1` and
`tools/compare-multiclass-skill-caps.ps1` are intentionally read-only:

- without a canonical table, it reports table coverage and known heuristic
  contamination controls;
- with `-CanonicalTable`, it performs an exact live-vs-canonical row comparison;
- the cross-container comparator retains complete CSV diffs without creating a
  comparison table in live PEQ;
- it never imports the canonical dump and never mutates either table.

## Required migration gate

All of the following must be complete before live repair SQL is written or run:

1. Take a fresh manual backup with `tools/backup-peq.ps1` and verify the archive.
2. Acquire and verify the authoritative PEQ dump. **Complete.**
3. Record its source URL, size, and SHA-256. **Complete.**
4. Import it into an isolated no-host-port comparison container. **Complete.**
5. Retain all three exact diffs: live-only rows, canonical-only rows, and cap
   mismatches. **Complete in `docs/audits/skill-caps-diff/`.**
6. Review the diff for intentional Nightcap overrides and encode any accepted
   overrides declaratively in version control.
7. Prepare a transaction-scoped, reversible migration and test it against a
   restored copy of the backup first.
8. After approval, apply the migration, regenerate shared memory, restart every
   zone process, and rerun native/held-class skill tests plus stock controls.

Until this gate is satisfied, code must not treat a positive live `skill_caps`
row as proof that a base class natively owns a skill.
