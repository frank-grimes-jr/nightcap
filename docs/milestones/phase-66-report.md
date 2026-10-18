# Phase 66 — Cooldown identity audit and AA correction

Reproduced Rampage locking Purify Body and inventoried all inspected AA, spell,
discipline and item groups. The deployed correction isolates AA families in server state
and the bounded native client table, separates item and discipline persistence,
and fixes completion, reconnect and scoped reset paths. The stopped-game
migration and rollback preserve existing deadlines and reject incompatible
catalog/schema state. PR223 is on main and the guarded OVH rollout passed on
October 18. All twelve zone hashes, migration receipt and data preservation verify;
access is open with owner gameplay acceptance pending.

Source and pinned-native tests cover unrelated AA pairs, same-family ranks,
signed focus, item aliases, all discipline groups, the -1 sentinel, relog and
reset isolation. Fifteen disposable MariaDB tests pass. Independent source and
migration review passes. The full native zone build and dependency checks pass;
exact provenance and promotion status are recorded in
[the release](../releases/cooldown-identities-20261017/README.md).

Content-defined linked spells, grouped disciplines and items remain explicit
open cases. Shared generic basic combat and Begging/Pick Pockets timers also
remain; this is not a claim of complete cooldown independence. Main/live
promotion was explicitly authorized and completed; [visible gameplay QA](../releases/cooldown-identities-20261017/QA.md)
remains open. The 25 deployment recovery tests and live forward/reverse rehearsal pass.
