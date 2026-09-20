# September 20 main source promotion

The owner explicitly requested "Push to main" after dev/test publication. This
authorizes source promotion before manual acceptance for this candidate only.
The previously verified test revision is `dd24fe0`; the promotion adds only
documentation to that revision. Previous remote main `b620beb` is its ancestor:
the 15 existing commits can be promoted without rewriting or dropping history.

## Scope

- Three-class pet roster and persistence, with existing native controls/armor.
- East Commonlands service/travel hub, recall repair and pinned archive recovery.
- Quantity-one city finds, six WTS/four WTB traders and income-scaled pricing.
- Six requested named tunnel residents, costumes, chatter and era-gated ports.
- Reviewed Classic Lavastorm package preparation and travel-readiness guard.
- Activation/recovery evidence, tests, rollback guidance and exact player QA.

The local root `main` checkout contains unrelated owner changes and is left
untouched. Promotion uses the clean feature/dev/test worktrees and fast-forward
remote updates. Game archives, private signing material, build artifacts and
unrelated production-launcher work are not added to the source release.

## Verification

The feature and promoted dev repository suites both passed 62 tests with one
existing opt-in pet database skip. The uncached launcher `go test -count=1 ./...`
passed on dev. Docker and Windows file-lock tests required authorized execution
outside the sandbox; their fixture databases/directories were isolated from live
player/client state. Independent packaging review found no actionable issues.
Promotion documentation changes no tested application code or package policy.

## Remaining Gates

This push does not restart servers, rotate stock, apply SQL or install a client.
Earlier activation evidence remains dated; it is not a new live-state audit.

1. Run the [market QA](../economy/QA.md): normal-account city and tunnel trades,
   exact payments/quantity, failure/refund paths, simultaneous purchases, auction
   filtering, price balance and restart-only rotation.
2. Run [resident QA](../economy/residents/README.md): all six identities, persistent
   costumes, Trift's OOC story, Khalure's eight currently offered Classic rings,
   safe landings and stale/future-link rejection.
3. Complete [Lavastorm build/install and terrain QA](../economy/residents/CLIENT-TERRAIN.md).
   The archive is verified and staged, not installed. Keep global readiness
   absent until every eligible client is ready, not merely one QA client.
4. Finish the existing [EC hub checks](ecommons-hub-20260920/README.md) and
   [pet roster checks](multiclass-pets-20260919/QA.md), including reconnect,
   transfers, controls and actual encounter balance.

Main source promotion is not a record of passing these manual checks.
