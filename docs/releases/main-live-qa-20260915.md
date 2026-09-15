# Main promotion for owner live QA — September 15, 2026

Owner instruction: "Move all gameplay changes into main . I will test it live."
This explicitly authorizes promotion before manual acceptance for this release.
It supersedes the earlier hold on main, not the unfinished feature/QA findings.

## Scope

Promote the complete tested history from `0e1b360efa45c71fdb09609893178102a061bc01`
plus this status documentation. Prior main was
`191bf8efaaa2427eb4b0e02ea5b2c4a2532192ae`; it is an ancestor of test, with
138 incoming commits and no main-only commits at preflight.

Included gameplay: native earned-AA purchases/grants/refunds/atomic class release,
canonical skills and lifecycle, held-class weapon damage, extra-pet ownership and
orders, direct-AA buff duration, waypoints, sixteen PoK class merchants and
relocated utilities, class guidance and 22 bag prices. Tests, tooling and dated
research accompany the source; merging experimental policy tools does not apply
their optional SQL or change the live balance/AA availability policy.

## Verification and deployment

The implementation is the previously reviewed, tested and deployed combined
release. Retained checks include 351 evidence/unit tests, 87 C++ tests, 14 MariaDB
hub controls, three bag integration tests and quest/plugin checks. Source
promotion introduces no additional gameplay edit or deployment/restart action.

[Live deployment hashes and rollback](live-qa-20260915/README.md) and
[exact owner QA checklist](live-qa-20260915/QA.md) remain authoritative. Record
PASS/FAIL per feature; issue closure needs its acceptance evidence. Public Pages
hosting remains separately blocked by the private-repository plan restriction.

## Branch and rollback handling

Merge through dev/test into main without force-pushing or rewriting existing
history. Preserve the dirty local root checkout and its runtime files. If live
rollback is needed, use the saved binary/plugin/database rollback evidence;
a Git revert alone does not reverse deployed database or cache changes.
