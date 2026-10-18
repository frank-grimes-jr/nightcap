# 0063 — Stable cooldown families and bounded native client slots

Status: deployed October 18, 2026 via PR223; owner gameplay acceptance remains open.

Rampage and Purify Body share raw AA group 1. In a multiclass character, this
aliases both the persisted server timer and the native client button clock.
The earlier duration correction cannot fix a shared identity.

Use the AA ability ID as the stable cooldown family. Ranks of one family retain
their shared deadline. Allocate persistence in a disjoint positive namespace;
project the full allowed held-class catalog into the native client's 100 slots.
Ownership, rank visibility and charges must not renumber slots. Class/catalog
changes clear and rebuild native clocks from retained server deadlines. Refuse
an unsupported family or overflow rather than silently sharing a timer.

Widen internal timer keys to uint32 while staying within SQL's unsigned 24-bit
column. Allocate separate namespaces for unlinked items, grouped disciplines
and disciplines with the native -1 sentinel. Preserve linked content groups as
explicit unresolved cases; changing only their server identity would disagree
with native client readiness. Generic combat skill grouping also needs its own
paired design. This correction makes no implicit balance or ownership changes.

Migration conservatively copies ambiguous legacy waits to every possible
successor, including dormant families, and retains the longest deadline.
Gameplay must be stopped. The transaction commits a receipt with timer rows;
zone admission requires that receipt. Rollback projects current waits back and
removes every namespaced key before an old uint16 loader may run. Do not wipe
timers or restore an old player snapshot to simplify this transition.

Rejected alternatives: changing only raw AA database groups exceeds the client's
100-slot bound; using uint16 positive AA keys collides with other domains;
widening negative item IDs exceeds the SQL column; erasing legacy waits refunds
cooldowns; assigning slots by owned ranks makes purchases shift active clocks.

Exact native contract, full catalog membership, reset call graph, migration
rehearsal, source review, build status and visible QA are recorded in
[the release evidence](../releases/cooldown-identities-20261017/README.md).
