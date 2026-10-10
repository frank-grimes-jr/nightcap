# Phase 62 — Production GM controls

Date: 2026-10-10. Candidate, not production activation.

Activation addendum: the owner later approved main and production. PR #143 merged,
production GM writes/support tables are active after a verified backup, and the
empty registry/helper are installed. The independent credential gateway rollout
still awaits Cloudflare authentication and recipient-code authorization. The
original candidate verification scope below remains historical.

Built the owner-local Local/Production GM connection, access-code lifecycle,
verified account password resets and the existing character/rule/progression/
merchant/client controls. Added explicit setup, maintenance/recovery, private
backups, transactional receipts, browser boundaries and cross-tab recovery.

Corrected the legacy MD5 reset, namespace/deletion hazards, wrong teleport ID,
base-class-only skills, non-atomic preset/progression writes and stale target state.
The reviewed source policy replaces direct era changes with a release proposal;
unsupported catalog activation is not presented as successful.

Nothing was cut from the supported existing operational categories. Direct era
mutation and edits to Client_RoF2_Dev remain prohibited by repository policy.
Production writes, player gateway activation, Cloudflare migration and real-player
QA are still pending. Local Docker was stopped; SQL and runtime mechanics were
tested using isolated OVH fixtures instead of claiming full local native QA.

Evidence: four HTTP/SSH checks, twelve DB scenarios, six Python and seven Chrome
checks; build/typecheck/audit; independent review with no remaining coding blocker;
production read-only smoke; isolated backup/maintenance/fence/resume rehearsal.
No live player data or game runtime was changed. See
[rollout and exact acceptance steps](../ops/production-gm-20261010.md).
