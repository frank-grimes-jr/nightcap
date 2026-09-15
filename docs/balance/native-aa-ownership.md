# Native owned-AA consistency and expansion transition evidence

Captured 2026-09-13 in `nightcap_balance_20260912`. No live data, binary, era rule
or process was changed. This checkpoint verifies a loader fix and an offline
ownership model; it does not complete expansion AA availability or server balance.

## Native loader correction

LoadAlternateAdvancement cleared the native AA map but left the profile array
populated. It also wrote a profile entry before checking whether SetAA accepted
the saved rank count. A rank chain shortened by expansion policy could therefore
leave a profile entry that disagreed with effective native ownership.

The candidate clears the profile array at reload and writes each profile entry
only after both native eligibility and SetAA succeed. Rejected database rows are
retained. The explicit common/types.h include supports standalone candidate
compilation without the original build's precompiled header.

| Native fixture | Before | After |
|---|---|---|
| Valid Natural Durability count 2 | Map/profile agree | Identical report and raw hash |
| Invalid count 7, native maximum 6 | Map empty, profile count 7 | Map/profile empty; saved count 7 retained |
| Count 2 removed from DB before reload | Map empty, stale profile count 2 | Map/profile empty |
| Saved count 6 above projected cap 3 | Map empty, profile count 6 | Map/profile empty; saved count 6 retained |
| Materialized count 3 under cap 3 | Map/profile agree | Identical report and raw hash |

All five controls preserve the synthetic unspent wallet of 17. These call native
load/save methods with synthetic persisted AA rows; they are not full login,
relog, wallet-persistence or refund tests.

The before/after manifests differ only in the AA object, its link entry,
candidate metadata and resulting binary hash. The exact compiled candidate is
archived as aa-ownership-candidate.cpp.gz; the tracked mirror differs only by
normalizing its original mixed line endings to LF. Harness, runtime, adapters and the
four earlier combat candidates are identical. This is still an isolated link
against pinned existing objects, not a fresh complete source/header parity build.

## Earned ownership model

`aa_ownership.py` retains canonical earned rows and produces active rows capped by
the chosen candidate. It calculates active and suspended nominal purchase costs
from the preserved original rank chains. It makes no database or wallet writes.

| Candidate | Earned rows | Active rows | Suspended family/character rows | Active nominal cost | Suspended nominal cost |
|---|---:|---:|---:|---:|---:|
| Launch core | 196 | 33 | 169 | 72 | 3,083 |
| Later core | 196 | 33 | 167 | 132 | 3,023 |
| Launch again | 196 | 33 | 169 | 72 | 3,083 |

The same 196 earned rows and nominal total 3,155 survive each transition. Active
and suspended rows can overlap when only higher ranks are locked. The candidate
cores omit many utilities and are not a final removal list or expansion schedule.

An additional native control materializes Natural Durability 3 from an earned
count of 6, then restores count 6 under the later candidate. Native load/save/load
accepts all six ranks, preserves the 17-point wallet, and reports nominal spent
cost 24 after saving. This proves that particular restoration path using the
original catalog, not all ownership lifecycle paths.

The model rejects ambiguous/invalid ownership, source changes without rebasing,
unexplained decreases/disappearance, purchases beyond prior caps, and suspension
of charged abilities. A production ledger must account for purchases, resets,
refunds, class release and consumed charges transactionally. It must preserve
suspended cost alongside active cost and existing expended-AA accounting.

The captured clone has AA:ModernAAScalingEnabled=false. exp.cpp uses spent plus
unspent points when that rule is enabled. The accounting requirement therefore
covers correct totals and future compatibility; this evidence does not establish
an active AA experience acceleration bug.

## Regression and restoration

Twenty-four seed-1729 Vox/Nagafen reports match the earlier complete reports and
raw hashes: 12 legacy-gear cases against gear-source-regression.json.gz and 12
source-constrained cases against gear-source.json.gz. These cover zero and launch
maximum allocations across WAR/CLR/WIZ, WAR/CLR/MNK and MAG/NEC/SHM. They establish
no combat regression in those controls, not general balance certification.

The complete original AA-table dump is restored exactly. The final account,
character, owned-AA and inventory tables contain zero rows; only the two verified
synthetic reagent rows were removed. No temporary AA procedures remain.

Reproduce offline checks from tools/balance with:

```text
python -m unittest tests.test_aa_ownership tests.test_aa_ownership_evidence
python -m unittest discover -s tests
```

Inputs, before/after build manifests, native reports, transition plans, final
cleanup checks and file hashes are captured as aa-ownership-* evidence.

## Required test promotion QA

Before promotion, complete ownership integration and a fresh source build. On the
test server, using a disposable level-50 WAR/CLR/WIZ in Plane of Knowledge:

1. Earn Natural Durability through six ranks and record wallet, spent total and
   effective HP. Apply the launch policy through the declarative era path; relog
   and zone. Expect exactly three effective ranks, preserved earned six-rank
   ownership, and the intended complete spent total with no automatic refund.
2. Attempt the next forbidden rank and an excluded ability. Expect rejection and
   no currency change. Inspect the AA window for stale entries after reload.
3. Apply the later policy through the same path. Relog and zone. Expect all six
   earned ranks to return without repurchase or wallet deduction.
4. Exercise reset/refund, class release and a charged AA using their completed
   lifecycle implementations. Confirm no duplicated points, resurrected refunded
   purchases, lost earned ranks or replenished charges.
5. Run matched fights against Lord Nagafen (32040, soldungb) and Lady Vox (73057,
   permafrost), at zero and allowed maximum AAs with fixed gear/preparation.
   Record resource use, duration, deaths, AA activation and pet behavior. Compare
   with the corresponding native case, allowing measured gameplay variability.

No promotion or live restart is part of this checkpoint. Test-to-main still needs
the owner's in-game sign-off.
