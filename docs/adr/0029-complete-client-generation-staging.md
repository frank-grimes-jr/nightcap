# ADR 0029: Stage a complete verified client generation

Date: 2026-09-15. Status: staging implemented; activation remains pending.

The launcher must eventually activate and recover one complete release. A set of
changed downloads alone is insufficient proof of a complete candidate.

Verify the signed manifest before disk access. Inspect current files through a
rooted directory, reject nonregular/link paths, and compare size plus SHA256.
Copy and rehash current assets; download changed/missing assets through bounded
HTTPS with the manifest host policy applied on every redirect. Preserve metadata
and mark staging complete only after all writes and file syncs succeed.

Stage outside the physical client tree, checking ancestor directory identities
and Windows junction aliases. Failure removes only the newly created candidate;
join cleanup errors so retained partial directories are visible. Interruption
can leave an orphan. A completion marker aids discovery but grants no trust:
the future installer must verify metadata and every file again under its process
lock, then use a recovery journal before any installed asset changes. Play stays
blocked until full generation, executable and required patch health pass.

Tests cover trusted/hostile metadata, local corruption, bounded/chunked downloads,
partial release failures, cancellation, real Windows junctions and cleanup errors.
[Staging contract](../../eq-launcher/README.md). No runtime acceptance claimed.
