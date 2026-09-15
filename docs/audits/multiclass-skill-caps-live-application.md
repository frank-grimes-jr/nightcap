# Epic #10 live skill-cap repair application

Date: 2026-07-28
Status: complete; rollback assets retained pending gameplay QA

## Safety assets

- Verified full backup:
  `backups/peq_20260728_193437_epic10_pre_migration.sql.gz`
- Backup size: 46,304,776 bytes
- Backup SHA-256:
  `a4db1ca65a18ebdd2049eda426805cd7cd1ec5ce313ea7d9bf7668170942352c`
- Exact removal evidence SHA-256:
  `8df2e24f7866e2ef6f49396212d31af57456403595ca1ec643106df85d331270`
- In-database rollback table: `skill_caps_epic10_removed`
- Retained rollback rows: 16,090

## Maintenance sequence

1. Final read-only preflight proved 74,449 live rows, 58,359 canonical rows,
   16,090 live-only rows, zero canonical-only rows, and zero cap mismatches.
2. Spire stopped world, loginserver, queryserv, UCS, and every zone process.
3. Live dry run deleted exactly 16,090 rows, reached 58,359 rows, rolled back,
   and reverified the original strict-superset state.
4. Live apply deleted and committed exactly 16,090 rows.
5. The migration's independent postcondition comparison proved an exact
   canonical match.
6. The launcher completed its shared-memory refresh and started a fresh process
   generation.

Two `character_data.ingame` flags were present before maintenance and remained
set after the forced process stop. They are not treated as authoritative active
session evidence and were not modified by this migration.

## Cache and process verification

The current `shared_memory` binary generates items and spells; it does not
generate the legacy `shared/skill_caps` file despite the stale README entry.
Current source loads `SkillCapsRepository::All()` directly in both
`world/main.cpp` and `zone/main.cpp`.

The fresh generation started at 19:38 local time:

- one world process;
- one loginserver process;
- one queryserv process;
- one UCS process;
- five static zone processes;
- three dynamic zone workers.

World and every zone worker logged `Loaded [58359] Skill Cap Entries`. A
five-second stability check found one world and eight zones still running, with
no recent `Error` or `Fatal` entry in `world.out` or `zone.out`.

## Final database proof

- Live rows: 58,359
- Canonical rows: 58,359
- Live-only rows: 0
- Canonical-only rows: 0
- Cap mismatches: 0
- Verdict: `exact_canonical_match`
- Rollback rows retained: 16,090

The baseline migration gate is complete. Keep the full backup and rollback table
until the next in-game skill QA checkpoint passes.
