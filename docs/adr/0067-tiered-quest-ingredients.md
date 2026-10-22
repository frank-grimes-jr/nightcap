# 0067 — Accept ordinary item qualities in Normal quest requirements

Date: 2026-10-22. Status: implemented candidate; deployment and player QA pending.

The Aviak Charm (Polished) rejected by Shakrn has a different item ID from the
Normal charm. Lua and native hand-ins both compared exact IDs. Some older Perl
quests bypassed the shared checker entirely.

Accept a real ordinary +200000/+400000/+600000 variant when a quest requests its
Normal family ID and the definition name matches the generated suffix. Apply
this at shared Lua/native hand-in and native Deliver boundaries, keeping real
instances and IDs for counts, returns and logging. Migrate audited legacy
equipment-input scripts to the native helper. Prefer exact inputs and allocate
explicit qualities before flexible requirements. Failed checks commit nothing.

Do not normalize inventory identities or script event globals: that would lose
quality on manual returns and could weaken explicit reforging/epic progression
contracts. Explicit quality requirements, separate reward catalogs and reward
tiers remain unchanged. Do not patch only Shakrn: that would leave the same bug
in other quests. A script-only fix would miss native Perl/task consumers.

The cost is paired native/quest deployment and a retained audit for custom
scripts that bypass helpers. The shared APIs cover standard new quests without
per-quest edits. Evidence, recovery and exact QA:
`docs/releases/quest-tier-handins-20261022/`.
