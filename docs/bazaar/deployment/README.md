# Commonlands bazaar — October26 live QA deployment

Owner approval: AUTHORIZATION.md. Main PR339/29e4e84b contains the reviewed
feature and28-test operator. Source8e8ef65a; zone SHA256
84b6b9ff5a5ce598e0e583d948c945b79c7742ee1a9364ddd1ed05148b6c5bc1.
The runtime started2026-10-26T17:19:48Z; gateway opening and post-opening checks
passed. Exact receipts: ../deployed.json, ../deployment-receipt.json and
../preflight-receipt.json. Owner will perform ../QA.md later.

All12zones plus world/login/ucs are paired.51schema/565content predicates,
97saved-state tables (with authenticated native expiry), and170existing command
permission rows were preserved. Only bazaar/access0/empty aliases was added.
Existing world/loader/cache, quests, signed client and unrelated services remain.
Zero native/quest/database errors detected. Five new InnoDB tables and their
exact inventory contract were rehearsed before installation; enabled state verified.
Fresh stopped backup:64,890,623compressed bytes,462,418,343uncompressed, gzip integrity
passed. Private backup and exact state snapshots remain on the host. No DB restore.

Initial preflight built the image, then failed only its672MiB reserve; game and
gateway stayed running. Reclaimed only task-created source.local cache
pyf6j6rkzq4pvi7al04hdmr6d. The initial raw image-list comparison failed; subsequent
exact identity, binary-hash, parent-layer and service checks verified preservation.
Free space recovered to975,933,440bytes. resume_preflight.py rechecked original
guards and fresh empty-schema rehearsal without rebuild, pruning or activation.
Original failure and exclusive continuation receipts are retained. Six continuation
fault tests pass; independent review found no blockers. No uncertain action replay.

Activation held access, gracefully stopped the full supervised runtime, verified
its stopped backup/state, installed additive escrow once, restarted and checked all
workers/state/content before enabling new trading. A separate open action verified
again before and after gateway opening. Native RoF2 UI/complete ownership-flow
acceptance remain open; source tests and runtime checks do not establish them.

Recovery: run the staged rollout.py disable action under its locks; preserve
compatible code, all five escrow tables and later earned state. Cancellation and
collection remain available. On an uncertain result inspect immutable receipts;
never replay, drop escrow or restore old player snapshots. See ../RUNBOOK.md.

The related wiki release preserves Rogue tome content and publishes the already-
deployed coordinated High Keep/Ashen guidance with bazaar live-testing instructions.
Publication wiki-publication.json and HTTPS wiki-public-verification.json both
pass:499files/security headers, five private denials,16Linux tests and pointer
rollback rehearsal.35files changed,464exactly preserved,none removed. Native
gameplay QA remains separate.
