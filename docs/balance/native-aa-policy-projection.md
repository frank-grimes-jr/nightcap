# Native AA rank-policy projection

Date: 2026-09-13. Isolated database experiment; no live deployment.

The native loader can enforce the calculator's candidate rank lists through its
existing data model. Disable omitted `aa_ability` rows and set `aa_ranks.next_id`
to -1 at each retained family's final allowed rank. Higher disconnected rank rows
remain stored, but the loader does not assign them a usable base ability.
No global class mask, spell, cost, level requirement, expansion rule, C++ source
or live character record changes in this experiment.

## Measured results

| Candidate | Enabled families | Native rank IDs | Legal build readouts | Rejected purchase controls | Identical boss replays |
| --- | ---: | ---: | ---: | ---: | ---: |
| Launch core | 20 | 61 | 9 | 7 | 6 |
| Later core | 22 | 109 | 12 | 7 | 6 |

Both projections preserve all 23 previously disabled families. Launch changes
1,527 enabled flags and 16 chain ends; later changes 1,525 flags and 15 ends.
Each candidate is materialized from the original tables, never by extending an
already-truncated chain without its original data.

Every legal readout retains identical purchased ranks, point accounting, equipped
stats, derived bonuses and trained skill values. Exported native catalogs equal
the expected capped lists, including the terminated final next-rank link. The 21
readouts cover the three representative multiclass profiles and the candidate
budget allocations; shared zero-AA allocations appear in both candidates.

Each forbidden purchase first succeeds against the original database using the
same character, prerequisite purchases and sufficient budget. It then fails at
the native purchase gate after projection, with no success report produced:

- Combat Stability rank 4, native rank ID 454, is denied in the launch candidate
  after buying its first three ranks. Rank 7, ID 457, is denied in the later
  candidate after its first six. All three profiles are tested.
- Innate Strength rank 1, ID 2, is denied for all three profiles because it is
  outside these diagnostic cores. This is a control, not a judgment that the
  ability is overpowered or should be permanently removed.
- Improved Twincast rank 1, ID 12893, is denied for WAR/CLR/WIZ in each candidate.

At each pool's maximum, WAR/CLR/WIZ, WAR/CLR/MNK and MAG/NEC/SHM replay Vox 73057
and Nagafen 32040 with seed 1729, the original source-constrained gear and original
preparation/controller. All 12 complete native reports match the prior gear-source
evidence byte-for-byte. The original failures remain failures; enforcing a pool
does not resolve the pet build's Nagafen survival problem or certify final balance.

## Backup, rollback and isolation

`aa-projection-before.sql.gz` is a full data dump of the two affected tables from
`nightcap_balance_20260912`, captured before writes. Both tables use InnoDB. The
generated SQL is confined to that exact database, requires empty account,
character and AA-purchase tables, checks original table sizes and changed values,
and verifies affected-row counts inside a transaction. An exception rolls back
the transaction. The procedures are removed after use.

After each candidate, guarded restoration reproduces the full original dump
byte-for-byte. An additional deliberately stale rank-chain precondition fails
after the 1,527 ability-row updates; the rollback again reproduces the complete
original table dump. No partial enable/disable state remains. Captured SQL,
native reports, restoration hashes and the rejection result are retained.

The runtime binary is the existing pinned pet-resistance build with all four
earlier native combat candidates. There is no new build or fresh source/header
parity claim. `run_aa_projection.py` waits for each native process to finish and
attempts guarded restoration on failure; unexpected database state is reported
instead of overwritten blindly. It refuses an existing evidence destination.
The captured apply/restore SQL is for the empty diagnostic database only.

## What this establishes and what remains

This establishes a tested data-projection path for rank visibility and native
purchase enforcement while preserving the measured legal builds. It avoids
introducing a separate C++ cap calculation that could disagree with the loader.
It does not exercise forged activation packets or existing-owner login/save
reconciliation. Source activation checks reject ranks without a base ability,
but that source observation is not counted as an activation runtime test.

There is an additional ownership trap in the existing loader: resolving a saved
count beyond a truncated chain returns its last available rank, but `SetAA` rejects
the original count when it exceeds the new maximum. The loader currently writes
the profile AA array before calling `SetAA` and does not check its result. That
source behavior must not be mistaken for a valid downgrade or preservation plan.
The empty-ownership guard prevents this experiment from exercising that unsafe
transition on an existing character.

The two cores remain incomplete offerings. Review utility and class-specific
abilities, assign actual Nightcap expansion unlocks, preserve the original rank
data durably, and implement auditable handling of existing owned ranks before
integrating a projection with the declarative era installer. The live era, AA
tables, purchases and processes remain unchanged.

Before test promotion, use disposable level-50 characters in PoK for all three
profiles. Under the launch policy, buy Combat Stability ranks 1–3 and verify rank
4 is unavailable and rejected by the server; repeat at ranks 6/7 under the later
test policy. Verify retained class/multiclass visibility and an excluded active
AA. With the selected ownership-reconciliation policy installed, test an existing
above-cap owner through camp/relog, zoning, saving, purchasing and later unlocks;
earned ownership and points must match that policy without duplication or loss.
Repeat the pinned boss cases in soldungb and permafrost, recording exact gear,
AA ranks, preparation, resources, deaths and durations. Main requires owner QA
sign-off; this diagnostic is not a test/main promotion.

## Verification

All 290 balance tests pass, including 11 new projection and native-evidence tests.
Inputs and SQL regenerate, capped catalogs and purchase accounting are checked,
and native boss reports and restoration hashes match their original evidence.
The final isolated fixture has zero account, character, AA-purchase and inventory
rows after removing the two verified synthetic reagent rows. No temporary
projection procedures remain. `aa-projection-evidence-manifest.json` pins the
backup, captured SQL, input matrices, reports, tools and tests.
