# Tunnel services and starters: OVH activation

Deployed September 21, 2026 at 11:30 UTC (07:30 Eastern) after the owner explicitly
approved main promotion and live deployment with "Move ahead with it". This is
authorization for this release; **manual gameplay acceptance remains open**.
The game and gateway are running. [Exact owner QA](QA.md).

## Released source and runtime

- Gameplay promotion: PR 57, main `0f023711a0ef1f60a26d6e466a722778b6688056`.
- Migration performance fix: `feda6ae64d5e6a3786955bed96ec035b910d7391`, promoted
  through dev/test/main by PRs 58-60. Approved release main:
  `e4c996c32ca9025d94e15a0399e94ab922494ac4`.
- Image: `nightcap-game:tunnel-services-20260921`, immutable ID
  `sha256:7219a5e43b6f00e96e6abf88914e309f0ea3c36ad381a9f840f6a605c8e0c570`.
- World SHA-256: `6bf1827689b9887dea150f69f2a9bce43a5a8039b834dc55c6d70bfaf20b0994`.
- Zone SHA-256: `09996b0732642178b9b869e9a3a5d24c8a0cbb2a0c5645ee532536fa59e70823`.

The paired binaries include the latest inventory refresh and existing production
hardening. The migration-only fix required no native rebuild. Loginserver, UCS
and shared-memory binaries retain their prior hashes; shared memory regenerated
from the updated content on startup. Nineteen quest/plugin files and the matching
supervisor were installed together. No new client assets were published.

## Deployment evidence

[Machine-readable activation record](ACTIVATION.json) includes the sanitized
host reports and artifact hashes. Local operational evidence:
`E:/EQ_Local_Dev/artifacts/tunnel-services-starters/ovh-20260921/`.
Private backups, SQL preimages and error logs remain on the host in
`/opt/nightcap/releases/tunnel-services-evidence-20260921`.
The pinned release/helper is in `/opt/nightcap/releases/tunnel-services-20260921`.

- Closed gateway and stopped world/zones before capture. Validated the full
  445,236,201-byte uncompressed SQL backup, then restored it into isolated
  MariaDB 10.11 with no production volume or published ports.
- Compared all 148 starting rules and the complete generated plan with the
  reviewed candidate. Verified exact forward changes, three 20-sale/12-buy market
  rotations, scoped rollback and 46 preservation fingerprints in the restored DB.
- Passed 34 database regressions, including exact case-only drift rejection,
  replay/collision rejection and MariaDB index selection. Seventeen deployment
  failure tests cover preservation, artifact drift, failed SQL/startup and rollback
  after later QA progress. Original build/native/Perl/map checks remain in
  [the candidate verification record](verification.json).
- After actual application and startup, all 15 running native process hashes
  matched. Health passed with zero restarts and no matched native, quest API or
  database startup errors. All 19 installed runtime file hashes matched.
- Before reopening access, all 46 fingerprints remained unchanged: character
  tables, accounts, inventory, quest globals, starting rules, market audit, rules
  and merchant rows outside the changed range. All 22 existing characters were
  preserved. This is an activation-time comparison, not a prohibition on later
  legitimate player progress.
- Post-startup static afterimages matched: 90 NPCs/spawn groups/entries/placements,
  2,199 supply listings, six objects, eight grids/32 waypoints, 32 starter item
  definitions plus the priced Plains Pebble, and 16 market actors. Explicit
  trainer checks confirm exactly one NPC for every class 20-35.
- Market advanced once from epoch 4 to 5: 20 sales, 12 buys and ten merchant finds,
  each initially quantity one. Four TLS-verified native handshakes passed through
  the public gateway on ports 5998, 9000, 7778 and 7000. These are transport checks,
  not an authenticated RoF2 gameplay session.

The first isolated restore stalled when a diagnostic pipe filled with a large
SQL statement. It was stopped without production SQL changes. The corrected
restore waits for the final MariaDB PID 1 process, copies the compressed dump
into the disposable container, and uses pipefail plus a private error file.
The restored full database then exposed unindexed binary row comparisons:
one merchant check scanned an estimated 82,755 rows. Adding native key predicates
while retaining every binary comparison changed it to a one-row PRIMARY lookup.
The successful final restore/rehearsal used that indexed implementation.

## Recovery

The previous paired image remains `nightcap-game:inventory-ui-20260921`, immutable
ID `sha256:d797c1246ea4359b5d6758b06c215f2fea821c110594686438a5874c59533ea6`.
Full backup SHA-256:
`b89adaec9f43e142577f16d6079d026ffc496975b36120443e299ea2d25b4e7f`.
Original runtime files and exact target forward/rollback SQL are retained in the
private evidence directory. Do not restore the whole database over later play.

For an authorized rollback, invoke the pinned helper on the host:

```sh
sudo -n python3 /opt/nightcap/releases/tunnel-services-20260921/rollout.py rollback
```

It closes access, captures current preservation fingerprints, validates the
manifest and exact target artifacts, rolls back only scoped content/procedure,
retains starter definitions and market audit, restores the prior paired runtime
and changed files, then verifies health and preservation before reopening.
No wallet or inventory grant is undone. If affected EC saved-state rows have
changed since startup, the exact guard intentionally stops: back up the current
state and use the scoped saved-state procedure in [the release guide](README.md).
Never bypass a drift assertion or delete unrelated/corpse/other-instance states.

## Remaining owner checks

Verify actual station and trainer windows, robe appearance/stats, new-character
100pp and weapon, natural grouping and walking, first-name OOC/auction variety,
real purchases and finite stock, and economic balance using [QA.md](QA.md).
The related spell issue had a stale local installation; the signed updater and
desktop shortcut were repaired. Close the old launcher and start through
`E:/Nightcap/nightcap-launcher.exe` for the spell level/filter checks. No graphical
acceptance is claimed by these database, binary or transport results.
