# AA policy and existing-purchase preflight

Date: 2026-09-13. Read-only PEQ capture and offline compilation; no live AA change.

The calculator's shared candidate caps now compile into explicit native rank IDs
against the full stored AA tables. This is the next step toward keeping server
access consistent with the measured fights. It does not turn the two diagnostic
combat cores into complete release offerings or install a runtime whitelist.

## Captured data and policy results

`aa-policy-snapshot.json.gz` contains 1,570 abilities, 6,655 ranks, 2,525 prerequisite
rows and 196 saved purchase rows. The capture uses a read-only transaction and
records its time and query hash. It includes character IDs but no character or
account names. Existing live characters were not edited or logged out.

| Candidate | Allowed native rank IDs | Retained purchase rows | Above cap | Outside core |
| --- | ---: | ---: | ---: | ---: |
| Launch core | 61 | 27 | 6 | 163 |
| Later core | 109 | 29 | 4 | 163 |

Both lists have complete prerequisite chains within their caps. Every calculator
allocation remains inside its corresponding list, with the same native rank
identity, ordinal, cost, level requirement, expansion metadata and prerequisites.
The later list contains every launch rank. These are global rank lists;
per-character native eligibility still applies. The later candidate is sensitivity
testing at fixed Classic gear/level, not an assigned expansion release.

Saved rows for ten character IDs are affected. The six launch over-cap rows are
Natural Durability, Combat Stability and Combat Agility on two characters. The
later core permits their full Natural Durability counts but still caps Stability
and Agility. No affected row in this capture has unspent charges. All 196 saved
rows resolve unambiguously; none requires guessing an ability from its ID.

The 163 outside-core rows are not a recommendation to remove 163 abilities:
rows represent character/family purchases, and the cores intentionally omit much
of the utility offering. Across all affected rows, the launch report covers 63
distinct families and the later report 62. Complete the offering review before
using either list as a server-wide allowlist.

## Native identity and persistence findings

`character_alternate_abilities.aa_id` stores a family's **first rank ID**;
`aa_value` counts purchased ranks. It is not a point budget. The native method
`GetRankByPointsSpent` walks by rank count despite its name. The preflight rejects
ambiguous ownership, noncanonical saved rank IDs, out-of-range counts, cycles,
shared enabled rank chains, overlapping free/paid caps and malformed caps.

The captured data has 775 missing next-rank references. The native loader ends a
chain when the next row is absent; existing earlier ranks remain valid. The
preflight records these missing tails, accepts valid retained prefixes and rejects
caps beyond their available length. Disabled abilities do not own native ranks.
Missing prerequisite abilities are explicit blockers even though native purchase
code can skip them; a reviewed release must not depend on an absent prerequisite.

Source excerpts and hashes are in `aa-policy-native-source.json`:

- `LoadAlternateAdvancement(Client*)` clears in-memory AAs, resolves the saved
  count to a rank and loads the family only if that rank passes `CanUse...`.
  It does not fall back to an allowed lower rank or issue a refund.
- `SaveAA()` replaces the current in-memory families at their canonical first-rank
  keys. It does not delete skipped families or preserve an overwritten higher
  value in a separate history. Repurchasing a lower rank can therefore replace
  the same stored key that held the unavailable higher count.
- `CalcAABonuses()` uses the loaded rank map without repeating the availability
  check. A rule change alone is not proof that already-loaded passive bonuses
  have changed. Purchase, activation, reload and persistence need joint tests.

These are source findings, not a new runtime test of policy enforcement.
`era.json` still has `aa_open: true`; the era script maps it to the native
expansion-gate rule being off. Simply enabling native expansion gating would not
implement the Nightcap exceptions and caps used in the calculator.

The report's `nominal_removed_rank_cost` is only the sum of current table costs
above the proposed cap. It is **not an authorized refund**: saved rows do not prove
whether ranks were earned, granted by a GM, automatically granted, or acquired at
an earlier cost. The tool emits no SQL mutations and never changes purchases.

## Reproduction and release work

From `tools/balance/`:

```powershell
python aa_policy_preflight.py --snapshot ../../docs/balance/aa-policy-snapshot.json.gz --specification ../../docs/balance/aa-release-candidates.json --output ../../docs/balance/aa-policy-preflight.json
python -m unittest tests.test_aa_policy_preflight tests.test_aa_policy_evidence
```

All 279 balance tests pass, including 16 new preflight and captured-evidence tests.
`aa-policy-evidence-manifest.json` pins the source snapshot, query, native excerpts,
policy, compiled report and verification code.

The remaining release work is concrete: complete the retained/deferred/excluded
ability list, assign Nightcap expansion unlocks, implement the same rank policy
at native access points, and reconcile existing purchases with durable ownership
and point accounting before activation. Compare the completed pool in the same
fixed-gear encounter matrix. Do not promote a combat-core preflight as that result.

Before test promotion, on disposable level-50 characters in PoK, verify an allowed
rank can be purchased and its first disallowed successor cannot. Test an excluded
active AA and a previously owned passive family above the cap. Camp/relog and
zone to soldungb; retained ownership, points and effective ranks must match the
documented reconciliation policy. Verify the next expansion unlocks its scheduled
ranks without duplicate charges or lost ownership. Repeat the pinned Vox 73057
(permafrost) and Nagafen 32040 (soldungb) scenarios after reconciliation; record
the exact gear, purchases, preparation, deaths, resources and fight durations.
Main still requires owner sign-off. No live restart is part of this preflight.
