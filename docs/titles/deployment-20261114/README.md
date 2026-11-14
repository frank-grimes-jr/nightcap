# Titles activation · November 14, 2026

Owner explicitly requested deployment and activation. **Prepared; production
activation pending.** The 77 permanent cosmetic titles give no combat or economy
power. New kill totals start at activation; existing personal clear, skill and
campaign goals reconcile through the title picker or `#titles`.

The linked shipping candidate `f35b4e3d` reproduces the running fixed-AA `82d5e2d2`
predecessor exactly before changing only title hooks/helpers and one command
archive member. All 144 retained link inputs and eleven other command archive
members are preserved. No new client, cache, quests or world binary is required.
The separate Classic prismatic content rollout completed first; title staging
captures its new live state and pins its terminal receipt.

Evidence: `shipping-{baseline,candidate}.json`, `source-delta.json`, exact
`feature.patch`, `storage-tests.json` and `schema-expected.json`. Four compiled
policy/adapter test groups and ten rollout boundary tests pass. Disposable real
MariaDB checks cover strict schemas, command privilege drift, unique concurrent
awards, disabling without data loss and 1/6/72-member counter bursts. Ordinary
kills use four SQL statements independent of party size; newly earned awards add
unique inserts. These timings are local SQL measurements, not live latency claims.

Independent fresh review found excessive per-member kill queries; batching fixed
it and follow-up review found no blocker. Deployment review found the inherited
backup hook blocked predecessor recovery; explicit guarded recovery and three
additional fault tests fixed that. Follow-up found no remaining blocker. An
external second opinion was offered, not requested; no external CLI review ran.

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

On a failure **before** opening and before any title counters/awards exist,
`recover-closed --start` can disable the exact owned control row, remove its exact
command row, retain all title tables, take a fresh backup and verify/reopen the
incumbent. No player snapshot restore. Partial/uncertain SQL is held closed for
explicit inspection and guarded forward completion, never a blind replay or
table deletion. After opening or title activity, repair forward with the capable
binary and preserve all awards/counters; predecessor recovery is refused.

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
