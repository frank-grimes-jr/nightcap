# ADR 0068: production-backed wiki loot finder

Date: 2026-10-22. Status: accepted and deployed with owner approval.

Players need equipment shared with their held classes, current-era source mobs,
locations and drop chances. The owner chose **any held class** as the default and
**automatic refresh**. An optional all-selected-classes mode remains available.

Keep the public wiki static. A host systemd job reads a fixed content-only field
allowlist in one MariaDB read-only consistent transaction every fifteen minutes.
It reuses the existing private database client option file inside the DB container;
credentials, SQL, raw captures and player/account tables never reach the web root.
The browser reads a public index and immutable per-item JSON, applying filters
locally. The snapshot named by the index also owns its details. Refresh failures
retain the last good capture; the page warns after 45 minutes. Keep eight snapshots.

The active production era and content flags gate the complete public version-0
spawn-to-loot path (including spawn version -1). NPC/global loot rules, level ranges,
weighted/minimum/repeated pool rolls and ordinary per-copy quality rolls determine
the chance of at least one copy. Spawn selection weight is separate. Public stats
are explicitly allowlisted again at the projection boundary. Quest/scripted/shop/
crafting and private dungeon/Hunt reward acquisition remain separate guides.

This avoids exposing a database socket or user-supplied SQL and bounds database
load independently of public traffic. Trade-offs: a roughly fifteen-minute delay,
only the active era, and database-derived availability rather than proof of game
cache state, encounter access or measured kills. The 6,293-item projection has about
327 MB of canonical JSON; gzip-only storage reduces payloads to 23.34 MB. The
deployment preflight found only about 720 MB free, so uncompressed retention was
rejected. Canonical JSON URLs/hashes are unchanged; nginx's static gzip and gunzip
modules serve both identity and gzip clients. File allocation is budgeted before
staging, with an additional 256 MiB disk reserve; insufficient space preserves the
last good capture. Eight generations are retained. The decoded index is about
1.6 MB and details load on demand. Local Linux peak RSS is about 640 MiB under the
1 GiB unit limit. Reassess size/time/memory before expanding capture scope.

Alternatives considered: a publish-only capture is simpler but fails the automatic
refresh request; a public query API adds attack surface and traffic-driven DB load
without helping these fixed filters. A separate replica is an optional future
deployment improvement, not required for the initial content-only reader.

Verification, acceptance boundaries and recovery:
`docs/releases/wiki-loot-finder-20261022/` and `docs/ops/wiki-loot-reader.md`.
