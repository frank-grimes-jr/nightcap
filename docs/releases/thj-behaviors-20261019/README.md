# THJ custom AA, focus and stock-gear testing candidate

Source branch: feature/thj-behaviors-gear, based on main 45e8416. Gameplay is not deployed,
the client is unsigned, and owner gameplay acceptance is pending. See CHANGELIST.md for the clean
AA/gear list and QA.md for exact owner tests. PLAN.md records accepted scope.

The public wiki is20261019-thj-behaviors-candidate-v1; all465 file hashes, security
headers and five private-route denials verify. Eleven guides label the new
mechanics Not released. Existing runtime/services/private downloads are preserved. Client staging is an unsigned two-file
delta requiring signed2026101901 and its unchanged proxy0.11.0/catalog pair.
No protected reference-client writes, era changes or production gameplay mutations.

## Reproduce and activate only in the isolated test environment

1. Generate AA/spell content with `python tools/thj_behavior_content.py` and
   verify the generated allowlist. Generate gear from a fresh public full-row
   capture with `tools/thj_stock_scaling.py --capture PATH`. Retain the exact
   preimage SHA. Current SQL is guarded against the October19 capture, not any
   future production changes. Reconcile drift instead of bypassing guards.
2. Fresh installations: generate `eq-solo-gm/scripts/thj-stock-bootstrap.sql`
   with `python tools/thj_stock_scaling.py --bootstrap PATH` before running
   tiered_loot_setup.sql from that scripts directory. A compressed deterministic
   copy is stock-bootstrap.sql.gz. This destructive fresh bootstrap is never
   a live migration. Its family/numeric guards agree with the live planner.
3. Build matching world, zone and shared_memory from the retained verified source
   plus the tracked overlay. The new rule name requires world and zone together.
   The isolated build script does not install anything. Final source/binary
   hashes must agree with the candidate manifest before packaging.
4. In a stopped disposable candidate database, apply content-forward.sql,
   decompressed gear-forward.sql.gz and rule-forward.sql. Use a fail-fast MariaDB
   client (never --force). Hash/value staging uses small packets and its complete
   identity set is checked before the atomic update. Retry is supported.
   Generate matching item/spell caches with the paired cache loader. Start the
   test runtime and verify the rule remains true after world boot.
5. Use tools/thj_behavior_client.py with the verified signed client base to stage
   spells_us.txt and dbstr_us.txt. Keep the other signed assets/proxy/catalog
   exact. Use a separate test-client copy; launcher publication/signing is a
   later deployment step. Do not mix the candidate client with the old server.
6. Run QA.md and retain results. Test→main and production activation still need
   the owner's explicit release authorization; this request prepares testing.

## Recovery

Stop the candidate before content/cache changes. rule-disable.sql is guarded.
gear-rollback.sql.gz restores only the captured numerical tier fields with full
current-row guards, preserving ownership and effect/socket data. The content
inverse restores existing spell/AA rows but retains new IDs so newly earned state
can still resolve. A policy rollback makes unsupported new purchases dormant;
it must not erase them. Retired-AA refunds are earned state and are not reversed
by restoring an older player snapshot. Retain current player/timer data, pair
older content with its matching runtime/client/cache, and reconcile any drift.

## Evidence

stock-source-manifest.json identifies the independent2026-10-17 ProjectEQ archive;
stock-REVIEW.md/field summaries and original131 catalog retain measured evidence
and its limits. gear-audit.json records inclusion/exclusion and capture SHA.
Native review executes actual methods/blocks with explicit mocked boundaries.
Database rehearsal uses a dedicated local database only; it checks full285-column
hashes, retries, inverse, late-row fault atomicity and bootstrap equivalence.
Build, client, wiki and test receipts are separate from owner gameplay acceptance.

## Automated verification and test handoff

The matching world, zone and shared_memory build and dependency checks passed.
All eight final inputs are pinned in native-build-manifest.json. The regression
suite passed 71 checks with eight optional environment skips; 44 supplemental
checks include native pet stacking and cooldown behavior. The latter covers
46,872 ordered AA pairs and 2,417 same-family rank pairs. Native AA eligibility
covers 11,070 cases; extracted refund/resource behavior covers 85 checks,
including group debit and incoming-heal modifier order. Five real MariaDB tests
cover retry, inverse, late drift, afterimage rollback and incomplete staging.
See the named JSON/log receipts for precise scope and mocked boundaries.

The optional diagnostic cache smoke test was not run: automatic approval review
rejected a new persistent database account, and no privileges were changed.
Regenerate complete caches on the intended test target using its existing runtime
credentials. The paired loader is built and verified; diagnostic caches are
excluded from the bundle. See cache-verification.json.

Public wiki verification covers 465 files, security headers and private-route
protection. Source review findings are resolved in review-disposition.json;
manual client/group/raid/reflection/resist and encounter-balance QA remain open.

The full isolated database rehearsal passed across 308,932 item rows and all
285 columns: 143,332 changed definitions, 733 content groups, forward/inverse
replay, complete rollback, late-row drift rejection without partial writes,
and fresh-bootstrap equivalence. Both gear SQL files reproduce exactly from the
current planner. Receipts: database-rehearsal.json and gear-reproducibility.json.
