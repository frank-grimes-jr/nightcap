# Titles activation · November 14, 2026

Owner explicitly requested deployment and activation. **Active on production; all twelve open workers verified.**
[Runtime verification](production-verified.json) · [Activation proof](activation-summary.json) ·
[Published guide checks](wiki-public-verification.json). Native visible player QA remains OPEN. The 77 permanent cosmetic titles give no combat or economy
power. New kill totals start at activation; existing personal clear, skill and
campaign goals reconcile through the title picker or `#titles`.

The linked shipping zone `f35b4e3d` reproduces the previous fixed-AA `82d5e2d2`
predecessor exactly before changing only title hooks/helpers and one command
archive member. All 144 retained link inputs and eleven other command archive
members are preserved. No new client, cache, quests or world binary is required.
The separate Classic prismatic content rollout completed first; title staging
captures its new live state and pins its terminal receipt.

The fresh current-title probe separates original activation preservation from
later independent content maintenance. A subsequent maintenance restart retained
the same title-capable image/binaries; the probe records its new start time and
current cache hashes. Original stopped-state/content preservation remains dated
in the immutable activation receipts, rather than being claimed as a fresh match
after another authorized content release.

Evidence: `shipping-{baseline,candidate}.json`, `source-delta.json`, exact
`feature.patch`, `storage-tests.json` and `schema-expected.json`. Four compiled
policy/adapter test groups, twelve rollout boundary tests, seven continuation
checkpoint cases and the publication-control regression pass. Disposable real
MariaDB checks cover strict schemas, command privilege drift, unique concurrent
awards, disabling without data loss and 1/6/72-member counter bursts. Ordinary
kills use four SQL statements independent of party size; newly earned awards add
unique inserts. These timings are local SQL measurements, not live latency claims.

Independent fresh review found excessive per-member kill queries; batching fixed
it and follow-up review found no blocker. Deployment review found the inherited
backup hook blocked predecessor recovery; explicit guarded recovery and three
additional fault tests fixed that. Follow-up found no remaining blocker. An
external second opinion was offered; the owner chose to continue with the completed
review. No external CLI review ran. The stopped-world RPC incident and bounded
continuation are documented in [INCIDENT.md](INCIDENT.md).

## Activation and recovery

`control.py stage --revision FULL_MAIN_SHA`, then `deploy --start` stages once and
starts a durable systemd service. Read receipts with `deploy` and verify with
`verify`. Never replay terminal/uncertain actions. Shared deploy/GM locks, exact
current services/native/client guards, admission drain, whole-game clean stop,
fresh verified stopped backup, strict additive SQL readback, native saved-state
expiry/one market rotation and twelve-worker checks gate reopening. Three new
tables are separately verified and only these are excluded from legacy player
snapshot comparison; all unrelated state remains checked. The single new
command row is independently checked before normalizing its legacy content hash.

Do not replay this stage's terminal commands. Its original operator is retained
as `release-original.py`; corrected `release.py` is reference source and differs
from the immutable stage. See INCIDENT.md for the exact one-shot continuation.
Partial/uncertain SQL requires explicit inspection and guarded forward completion,
never a blind replay or table deletion. After opening or title activity, repair
forward with the capable binary and preserve all awards/counters. No player
snapshot restore. The corrected reference recovery preserves tables, disables
owned additions and takes a fresh backup, with RPC only while the game is running.

## Player acceptance remains open

With an ordinary account and GM off, open the title picker and use `#titles`.
Confirm earned skill/level/clear goals appear, locked titles cannot be worn, and
selecting a prefix/suffix persists after zoning/relog. Kill a qualifying natural
non-gray NPC and verify counting once for eligible nearby living participants.
Defeat home-zone Nagafen: **Flamebreaker** should unlock with a notification;
Nagafen **and Vox** are required for **Dragonslayer**. Repeating an earned goal
must not notify twice. Verify nameplates/picker in the native RoF2 client.

Palwar's earlier kill is independently logged as event20094, NPC32040/zone32,
public instance0 at2026-11-14 19:40:51UTC. It predates title activation. Any scoped
correction must record its own receipt and credit only that named victory; do not
invent general/dragon totals or claim a live native notification for an SQL repair.
