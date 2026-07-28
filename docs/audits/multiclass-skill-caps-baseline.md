# Multiclass `skill_caps` Baseline Audit

Date: 2026-07-28
Epic: #10
Status: migration blocked pending an authoritative clean PEQ baseline

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
- Every local PEQ backup currently retained is dated after the original widening.
  None is accepted as a clean native baseline.
- The canonical PEQ bootstrap source is identified by
  `akk-stack/code/utils/scripts/build/source-db-build.sh` as
  `http://db.projecteq.net/api/v1/dump/latest`. DNS resolution for that host was
  unavailable from the dev environment during this audit.
- GitHub code search did not locate an authoritative ProjectEQ `skill_caps`
  dataset. Unrelated emulator forks are not safe migration sources.

## Safety decision

Do not delete, rewrite, or rebuild live `skill_caps` from heuristics. A row that
looks unusual may still be a legitimate PEQ era/race/class rule, and the current
table has insufficient provenance to distinguish native rows from widened rows.

`tools/audit-multiclass-skill-caps.ps1` is intentionally read-only:

- without a canonical table, it reports table coverage and known heuristic
  contamination controls;
- with `-CanonicalTable`, it performs an exact live-vs-canonical row comparison;
- it never imports the canonical dump and never mutates either table.

## Required migration gate

All of the following must be complete before live repair SQL is written or run:

1. Take a fresh manual backup with `tools/backup-peq.ps1` and verify the archive.
2. Acquire the PEQ dump matching the intended Nightcap source/era from an
   authoritative ProjectEQ source.
3. Record its source URL, retrieval time, size, and SHA-256.
4. Import only its native `skill_caps` data into a separately named comparison
   table in the dev database. Never overwrite live `skill_caps` during import.
5. Run the audit tool with `-CanonicalTable` and retain all three exact diffs:
   live-only rows, canonical-only rows, and cap mismatches.
6. Review the diff for intentional Nightcap overrides and encode any accepted
   overrides declaratively in version control.
7. Prepare a transaction-scoped, reversible migration and test it against a
   restored copy of the backup first.
8. After approval, apply the migration, regenerate shared memory, restart every
   zone process, and rerun native/held-class skill tests plus stock controls.

Until this gate is satisfied, code must not treat a positive live `skill_caps`
row as proof that a base class natively owns a skill.
