# Live AA client-title audit — 2026-09-15

Issue #16 remains open. The live audit completed; blanket disablement is unsafe.

## Result

- 1,570 ability rows, 6,655 rank rows, 66 distinct saved first-rank IDs.
- 6,643 ranks reachable from ability roots; 775 positive next-rank references
  end at absent rows. The native loader truncates these chains deliberately.
- 2,470 nonempty RoF2 type-1 title strings.
- 194 families reference missing titles; 192 are enabled, two already disabled.
- 19 saved ownership rows intersect enabled affected families:

| Ability | First rank | Meaning | Saved rows |
|---|---|---|---|
| 1019 | 17248 | `[PAL] Unknown AA 17248`; listed rank cost 24, expansion 21 | 2 |
| 2220 | 22200 | Ancient Attunement; system AA, type 0, title -1, cost 0 | 17 |

Saved ownership is not proof that points were paid. No character identifiers or
wallet values are published. A missing title is not itself proof that a system
AA is displayed as a broken entry. Ancient Attunement must not be disabled just
to remove a raw missing-title match. The old zero-purchase note is superseded.

## Audit correction and proof

The first live run failed because the audit rejected ability ID 0. Inspection
also found missing positive next-rank references. The engine loader accepts
ability ID 0 and sets `next_id=-1` when the next lookup returns no rank.
The corrected audit follows those semantics and explicitly reports truncated
tails. It still rejects negative ability IDs, nonpositive rank IDs, missing first
ranks, cycles, shared ranks, duplicate rows, incomplete exports and unmapped
saved ownership. Two new behavior tests failed before the correction; all 13
unit/CLI tests pass afterward.

Source: `Zone::LoadAlternateAdvancement`,
`ZoneDatabase::LoadAlternateAdvancementAbilities`, and
`Mob::CanUseAlternateAdvancementRank` in `server-mods/code/zone/aa.cpp` on this
branch, checked against active source in `akk-stack/code/zone/aa.cpp`.

The SQL ran against local PEQ in a read-only consistent snapshot. The three
queried AA tables are InnoDB. Two captures after database startup produced the
same byte hash. [report.json](report.json) retains complete findings and hashes;
the local aggregate input is
`artifacts/issue-review-20260915/aa-snapshot-final.tsv` in the main workspace.
Snapshot SHA256: `a1017071c82a74b68315ce933ecbec2bcc18c3f3ff1ac3564c9c6e995a5aa93e`.
Report capture: 2026-09-15 11:59 UTC. This is historical evidence, not a promise
about subsequent purchases or catalog changes.

## Safe next step

Preserve owned ranks and system AAs. Review the unnamed Paladin ability's effects
and how its two ownership rows were acquired before choosing either supported
client strings or an explicit refund/removal plan. Any unowned-family disablement
must also check prerequisite dependents and the legal release pool, retain exact
flag preimages and a verified backup, and revalidate ownership at application.
Neither whole-family removal nor a blanket post-RoF cutoff is authorized by this
audit. In-game AA window, point-counter, zone and reconnect QA remain required.

Docker had stopped again. Startup reproduced the documented stale
`sailor-ingest.sock` failure. The failed Docker processes and its WSL distribution
were stopped, both runtime directories preserved under `*-stale-20260915-075238`,
then Docker was relaunched. MariaDB readiness was verified before the snapshot.
No game-client files, AA flags, ownership, wallets or live server binary changed.
