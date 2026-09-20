# Verification record: 2026-09-20

All checks below were isolated from live PEQ writes and installed server binaries.
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
| Full paired world/zone build | Passed with clang 14; neither binary installed |
| Live activation / owner gameplay QA | Not performed |

The full suite's first attempt could not access Docker from the sandbox. The
rerun with Docker access passed as above; it was an environment restriction,
not a missing data fixture. Initial compilation found four signed-coin narrowing
errors; explicit negative-balance rejection and checked conversion corrected them.

Paired build SHA256:

- World: `a10f0b7423433edef872b45085e1bebb401ef437e79ec99595b3975918786817`
- Zone: `e2ba36f37543fb89c30c6a4c30f13a83db2c4f2de9cc521bef0e8ea50f850185`

Full build manifest/logs and binary copies are retained under
`E:/EQ_Local_Dev/artifacts/living-economy-20260920/`. The isolated container build
is `/tmp/nightcap-market-20260920`; live executables were not replaced.

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
  source map, **not the missing configured alias**; the prerequisite remains
  uninstalled and blocks activation. See `residents/geometry.json` and README.
- Independent follow-up review found a dangling-tint-reference ownership gap;
  the forward guard now rejects it and the database rehearsal covers it.
  Rehearsal also caught six-decimal spawn formatting; exact rollback preimages
  and column-type guards now pass. Reviewer confirmed the regenerated package.

This follow-up changes no C++ and uses the paired binaries recorded above.
Live activation, actual costume rendering and ring-stone/client terrain QA have
not been performed. No original client files were changed.
