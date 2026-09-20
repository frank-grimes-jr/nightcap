# Verification record: 2026-09-20

The first sections record isolated checks. Activation subsequently exposed stale
build artifacts; the correction below supersedes the initial binary evidence.
This is automated evidence, not completed in-game acceptance.

| Check | Result |
|---|---|
| Repository Python/native regression discovery | 54 tests, 53 passed; existing opt-in pet database test skipped |
| Final focused market tests | 7 passed |
| Extracted production transaction body, MSVC | 24 injected SQL failures, 16 stale predicates, stale cursor states, rollback failure and conservation passed |
| Real MariaDB disposable-schema rehearsal | 24 checks passed; scratch schema removed |
| Concurrent purchase | Exactly one winner, one item, one payment and one audit row |
| Rollback rehearsal | New NPC/spawn removal only; player state, audit, original merchants and unrelated saved states retained |
| Perl adapters and shared cadence | 10 assertions passed |
| Geometry | All 10 positions, 5 ground samples each, approximately 30 units headroom |
| Independent same-model review | Merchant slot collision/hidden-slot allocation, queued packets and weight refresh findings corrected |
| Initial paired build | Command succeeded, but stale objects invalidated its provenance during activation |
| Owner gameplay QA | Not performed |

The full suite's first attempt could not access Docker from the sandbox. The
rerun with Docker access passed as above; it was an environment restriction,
not a missing data fixture. Initial compilation found four signed-coin narrowing
errors; explicit negative-balance rejection and checked conversion corrected them.

Rejected initial artifact SHA256 (retain for incident evidence; do not deploy):

- World: `a10f0b7423433edef872b45085e1bebb401ef437e79ec99595b3975918786817`
- Zone: `e2ba36f37543fb89c30c6a4c30f13a83db2c4f2de9cc521bef0e8ea50f850185`

Full build manifest/logs and binary copies are retained under
`E:/EQ_Local_Dev/artifacts/living-economy-20260920/`. The isolated container build
is `/tmp/nightcap-market-20260920`. See the corrected artifact record below.

Evidence:

- `evidence/market-database.json`: real SQL and rollback assertions.
- `evidence/market-sql.json`: production-generated transaction statements.
- `evidence/map-probe.json`: actual map geometry samples.
- `generated/placement.json`: exact merchant and trader positions/identities.
- `generated/catalog.json`: final scaled asks/payouts with P1999 provenance.
- `tools/tests/living_economy_fixture.cpp`: failure-injection fixture around the
  extracted production transaction, not a rewritten implementation.

The user declined a cross-model second opinion and chose continued current review
and tests. The current reviewer traced the existing quarantine/save hooks and
native hand-in return path. No new automatic promotion to main is authorized.

## Named resident follow-up

- Final repository regression: 59 tests, 58 passed; the existing opt-in pet
  database test remains skipped. This includes five resident-specific tests.
- Twenty-one Perl assertions passed for menu destinations, forged/stale links,
  era/range/combat checks, cooldown, hand-in returns and Trift's OOC cadence.
- Sixteen real MariaDB checks passed in a removed disposable schema; see
  `residents/database-rehearsal.json`. Installation/rollback preserve unrelated
  NPCs, traders, merchant stock, player items/money and non-owned saved states.
- All 25 positions pass five-sample ground/headroom checks with landing height
  between ground and 12 units above it. Lavastorm uses the verified Classic
  source map, **not the then-missing configured alias**. That preactivation
  prerequisite was resolved during the approved activation; the dated probe
  remains in `residents/geometry.json`, with installed-map evidence in activation.
- Independent follow-up review found a dangling-tint-reference ownership gap;
  the forward guard now rejects it and the database rehearsal covers it.
  Rehearsal also caught six-decimal spawn formatting; exact rollback preimages
  and column-type guards now pass. Reviewer confirmed the regenerated package.

This follow-up changes no C++ and uses the paired binaries recorded above.
Actual costume rendering and ring-stone/client terrain QA remain open.
No original client files were changed.

## Activation recovery checks

The first world startup rejected `CALL nightcap_market_rotate(0)`: the compiled
call was stale while current source/SQL required era plus both earning rules.
The helper had reused objects after copying source with preserved timestamps.
Failed attempts left epoch zero, no offers and no trades. The launcher retry loop
was stopped; no zones opened for players during that attempt.

All nine modified C++ sources/headers were explicitly invalidated and both targets
rebuilt. The recovery log proves each changed direct object and the Perl unity
object recompiled; header-dependent units rebuilt as well. All source hashes
still match the reviewed source manifest. The corrected world passes the actual
ELF contract check; the rejected artifact demonstrably fails it.

- Corrected world: `c7a008e95615ff7f74cdca946ef889ad013052227b5593854e56e0091d8c51b3`.
- Corrected zone: `6f110f50ad9018a380f65fe47bd4cc0388bb7c4103a9665d569902d4411a843e`.
- Full repository regression: 62 tests, 61 passed and one existing opt-in skip.
- Resident quest tests: 23 passed, including missing-readiness/stale-link guards.
- The future build helper now requires a fresh output directory, brackets the
  build with source fingerprints and rejects stale ELF startup contracts.
- Independent review accepted the fix; its additional Perl-object assertion was
  incorporated into the recovery installer before execution.

Recovery evidence is retained under
`E:/EQ_Local_Dev/artifacts/living-economy-20260920/activation/`:
`first-start-failure.log`, `rebuilt/build.log`, `rebuilt-manifest.json`,
`rebuilt-installed.json`, `quest-fix.json`, and `file-manifest-effective.json`.
The original manifests and failed artifacts are retained separately.

## Dev/Test Source Promotion

The owner requested pushing all living-economy work through dev and QA (`test`).
The five existing economy/resident commits and the Lavastorm packaging follow-up
are included; main, installed clients and running server processes are untouched.

- Full repository suite: 63 tests, 62 passed and one existing opt-in skip.
  The initial sandbox run lacked Docker access; the authorized rerun passed
  against the test's unique disposable database, without selecting live PEQ.
- Normal launcher `go test ./...`: all packages pass.
- Independent Lavastorm packaging review: no actionable findings.
- Exact in-game handoff: [market transactions, chatter and rotation](QA.md),
  [six resident appearances and Khalure travel](residents/README.md), and
  [Lavastorm build/install and terrain acceptance](residents/CLIENT-TERRAIN.md).

This source push is not a signed-client release, new deployment, manual gameplay
acceptance or authorization to enable the global Lavastorm readiness flag.
