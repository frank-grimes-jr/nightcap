# Native class-release reproduction

> Current status (2026-09-15): implemented server/AA/PoK candidates are deployed for live QA; main gameplay acceptance remains pending. See [current status](../status.md). The dated evidence below retains its original scope and is not a current deployment checklist.


2026-09-13. Before-state evidence on the isolated AA feature branch at d7c5613.
The atomic class-release fix is not implemented or deployed in this increment.

Seven cases exercise 36 native operations. Six fail the required atomic-release
contract; Second-slot promotion with a retained Wizard family already passes.
The source mixes the old active-only purge with the new canonical earned-AA map.

| Wizard AA267 rank6 state | Earned ranks remaining after release | Wallet refund | Required refund |
|---|---:|---:|---:|
| All six usable | 6 | 30 | 30 |
| Three usable, six earned | 6 | 18 | 30 |
| All six suspended | 6 | 0 | 30 |

All three should remove the class-only earned family and refund its full nominal
cost, while retaining shared-class families. The shared Natural Durability case
checks that separate entitlement. Class-update failure is currently ignored by
the old quest-equivalent sequence. The persisted class and AA/counter changes
are not one transaction.

The harness calls the current quest's separate class SQL and then the real native
PurgeAfterClassRelease. It does not invoke the Perl interpreter. When a public
ReleaseMulticlassSlot primitive exists, the same templated probe will call it
instead. Native behavior, persisted rows, profile, loaded/saved classes, wallet,
spent points, and failure counts are recorded after each operation.

## Scope limits

The mock ClientDataLoaded flag is false, recorded explicitly. Thus the old trailing
general Save exits early. The class-table trigger executes once; the points-table
trigger remains armed but executes zero times. The points case is an acceptance
requirement for the new atomic primitive, not a reproduced failure inside the live
general Save path. Retained earned ownership and partial/suspended under-refunds
are independently established by native purge/AA-save behavior.

The harness recalculates bonuses after operations, so these probes do not prove
that production release refreshes bonuses itself. They do not yet inspect actual
class-mask bits, trained skills, native reconnect, uncertain COMMIT outcomes,
quest dialogue, or success-packet timing. Those are required before accepting the
implementation, with the broader cases listed in ADR 0026.

Character 1 has the same synthetic WAR/CLR/WIZ configuration and no persisted
skills; earlier skill fixtures on character 4 are left untouched. The runner
restores original multiclass values and timestamps, verifies skills/catalog
unchanged, removes synthetic character/AA rows, and removes failure triggers.
Unexpected fixture state is retained for inspection rather than blindly deleted.

## Provenance and reproduction

Diagnostic binary SHA256:
f0bf9b58469d5eb1021ef8645fa1c501c80d1f6a4cd1501095b94c134e7b0eb8.
It links 130 pinned objects from the existing fresh purchase build at
`/tmp/nightcap-aa-purchase-20260913/source`; this increment is not a fresh full
engine rebuild. The diagnostic adapters/harness are built separately in
`/tmp/nightcap-balance-aa-release-before-20260913`. No live binary is touched.

`aa-release-before-*` contains inputs, native results, build manifest, retained
sources, and evidence hashes. From the worktree root, with that isolated runtime:

```powershell
python -B tools/balance/run_aa_class_release.py --phase before
```

All 343 Python calculator and evidence tests passed in 167.755 seconds. The
retained log is `aa-release-before-python-tests.log`. These tests verify the
expected before-state failures; they do not make the release implementation pass.

Run focused unit/evidence checks from `tools/balance/`:

```powershell
python -B -m unittest discover -s tests -p 'test_aa_class_release*.py' -v
```

The next implementation is one native transaction for class slots, canonical AA
refunds, and skill clamps, plus a boolean quest binding and removal of the old
write-then-purge path. The PoK usability candidate stays separate; it does not
resolve this native lifecycle issue. Do not promote the AA ownership binary
before these release failures and the remaining lifecycle gates are addressed.
