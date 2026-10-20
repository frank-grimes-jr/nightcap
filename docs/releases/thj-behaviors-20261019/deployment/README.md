# THJ behavior and stock-gear production release

The owner explicitly authorized main and server deployment. PR256 promoted the
reviewed test tree to main 7104c6b. Production activation is complete and access is open. Receipts are in receipts/.
Signed game2026101902 and wiki20261019-thj-behaviors-live-v1 are verified.
Owner gameplay and balance acceptance remain pending.

The paired world, zone and shared_memory binaries are unchanged from the tested
bundle. The operator reuses the October18 paired release pipeline: deployment
and GM locks, a fresh public-content clone, full table before/after checksums,
a stopped full backup, player/custom preservation, cache generation, native
health and market-rotation checks, signed client publication, then access open.
The three guarded SQL components cover AA/spells, ordinary tier stats and the
new rule. Rule descriptions use the exact compiled text so native boot does not
invalidate guarded recovery; values are unchanged. No expansion promotion.

Only unused Docker builder cache and the verified redundant transfer archive
were removed for capacity. Image tags, service identities, backups and extracted
release history remain. The first preflight stopped at its disk gate before any
live or clone write; its log is retained. The full local forward/retry/inverse/
fault rehearsal remains the recovery evidence; this fresh remote clone adds
current full-table parity. The temporary public clone is removed after its
checksums are recorded and before activation.

## Operator and recovery

Stage: /opt/nightcap/releases/thj-behaviors-live-20261019. Run rollout.py actions
preflight, activate and open only in order. Actions are one-shot and guarded;
inspect attempted/committed receipts after any failure. Never replay uncertain
SQL. Client publication uses signed game2026101902 with unchanged proxy0.11.0
and matching catalog; all136 unrelated assets remain exact. Access stays closed
until all138 HTTPS assets verify with the shipped trust policy.

For recovery, hold game/gateway and take a fresh backup. Inspect committed
components before applying only their guarded inverse under deployment/GM locks.
The recovery SQL preserves item identities/effects/sockets and new AA identities;
never restore old player state or undo earned login refunds. Pair prior content,
image, fresh caches and a higher signed client release. A new unexplained hold
needs diagnosis; the original operator is not an automatic rollback command.

Twenty-five operator/publisher fault tests pass. Source/gameplay regressions and
native builds are unchanged from the test release. Gameplay and balance
acceptance remain pending; follow ../QA.md after opening the normal launcher.

## Diagnosed pre-write memory hold

The first live AA/spell CREATE PROCEDURE hit the database container's 2 GiB
memory limit after the clone rehearsal had already compiled the same large
procedure. The kernel recorded a cgroup OOM and MariaDB restarted once. Exact
content/control checksums, original stopped player/custom state, market state
and absence of candidate routines proved that no content transaction committed.
Original attempt and hold receipts are retained. No data snapshot was restored.

resume_oom.py admits only that specific pre-write checkpoint: same DB container/
image, exactly one restart, healthy state, unchanged original content/ownership,
no committed component, no generated cache and no possible player access. It
records a fresh stopped backup and resumes against the recovered cold database.
Eleven actual-function admission tests reject data drift, replacement, extra
restarts, prior commits/access/cache generation and an unclean stop. It preserves
the original backup and verified rollback caches. Use its open action only after
paired client publication and complete shipped-trust HTTPS verification. Never
reuse this resume for a different failure. Later recovery needs fresh diagnosis.

## Authenticated saved-zone expiry

The first new-world boot purged exactly1,113 non-corpse, non-instance NPC cache
rows older than seven days in zones13,25,30,73, using Zone:StateSaveClearDays=7.
world/world_boot.cpp and zone_state_spawns_repository.h match the native build
manifest. An isolated cache-only restore proves no added rows, preserved surviving
fields (FLOAT uses canonical stored text), exact expired IDs/counts and no corpse
rows. Every other original player/custom receipt matches; no live data was
restored. Both startup market rotations are authenticated separately.

finish_zone_cache.py is the final entrypoint for this diagnosed hold. It requires
all three content commits, original afterimages/caches, exact scoped expiry and
unchanged remaining earned state, then takes a fresh backup and restarts the
paired image. Its open action requires complete signed-client HTTPS verification.
Original holds and the diagnosed resume remain immutable evidence. Do not rerun
an earlier activate/open action or accept a different state change implicitly.

Rollback cache files are retained as private-backup/cache-items.gz and
cache-spells.gz. Lossless decompression hashes match the original files; restore
only into a stopped, correctly paired runtime if needed. This preserves recovery
while leaving about1.47GiB free. See compressed-cache-backups.json.
