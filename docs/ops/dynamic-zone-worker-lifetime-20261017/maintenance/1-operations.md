# Source authority, builds and reloads

Audited 2026-10-12. Consult the selected checkout's current instructions and release record. `references/sources.json` pins inspected files and their locations; hashes detect change, not correctness or deployment.

## Resolve the source before editing

- Main workspace: `E:/EQ_Local_Dev`. Latest inspected integrated checkout: `E:/EQ_Local_Dev/_worktrees/merchant-sell-all` at `eeb79ddebd69bdc4bda1725e7ccf5fa6e18591d1`. The supply-protection checkout is `C:/Users/verre/.codex/worktrees/sellall-supplies/EQ_Local_Dev`; observed `origin/main` advanced to `890a9c0` during this audit. These are dated anchors, not branch-selection commands.
- The default checkout was `feature/npc-heal-self` at `ce161c5`; local main was still September history. Its `docs/status.md` missed many October deployments. Use `git worktree list --porcelain`, scoped log/diff and exact paths; don't switch a shared checkout or assume local main is the latest release.
- `server-mods/code/` is the tracked customization overlay, not a complete compilable source tree. Local full source is `akk-stack/code/`; local live quests/plugins are `akk-stack/server/quests/` and `akk-stack/server/plugins/`. Compare relevant copies, normalizing line endings only for semantic comparison; deployment hashes remain byte-exact.
- Production builders layer reviewed patches onto fingerprinted retained source. Preserve authentication hardening, advanced-loot receipts and intervening releases. A generic local build or an older development archive is not a valid production replacement.
- Other project `C:/nightcap-development-mmo` contains character/texture/production labs, not the core EQEmu implementation. No root package.json/shared npm build exists. Local PEQ is port 3307. Don't read credential-bearing API/config files wholesale.

## Application boundaries

| Change | Required refresh/pairing |
|---|---|
| Quest/plugin | Correct installed path and interpreter precedence, then supported quest reload; verify completion/errors |
| Existing rule value | World and zones' rules reload; latest runbooks use `#reload rules global` |
| New rule name/catalog | Matching world and zone build; old world deletes unknown names at boot; verify DB values afterward |
| Items, new spells/shared data | Appropriate shared-memory regeneration and supported runtime restart; existing-row hotfix is not a universal new-row solution |
| FreeTrade or DisableLore | Rebuild item cache and restart; SQL raw flags intentionally differ from effective flags |
| Shared ItemData ABI | Matching complete native binary/cache generation, including rollback |
| `skill_caps` | Process-local loader in world/every zone; restart those processes under the correct supervisor, not legacy shared/skill_caps |
| NPC/merchant templates | Zone cache refresh under documented unload/maintenance; `#repop` alone is insufficient |
| spawn/placement | Spawn refresh plus scoped saved-state handling; inspect zone_state_spawns so stale positions don't return |
| AA catalog | Zone AA reload/restart supported by the build; no generic shared-item regeneration |
| Era | Committed `era.json`, `tools/apply-era.ps1`, catalog review; do not activate via ad hoc GM SQL |

On OVH any native child exit can restart the entire runtime. The October 17
correction disables inherited `Zone:KillProcessOnDynamicShutdown` in default
ruleset 1; no alternate override existed. Preserve false in future rulesets. Inspect the current supervisor and release-specific procedure. Local eqlaunch behavior is not portable. Saved-state edits must be limited by zone, instance and exact NPC identity, preserving corpses and unrelated states. New additions may already load correctly without invalidating saved states: item-upgrade release explicitly needed none.

## Verification and recovery

Select tests from the feature reference and the release README; inspect runners before running them. Some native probes/rehearsals create disposable DBs or temporary fixtures; do not aim them at production merely because they are called tests. For a production change, use the matching release helper with fresh backups, maintenance/GM locks, current preimages, binary/cache checks and recovery tests. Once access may have opened, preserve subsequent activity and reconcile durable receipts before any retry/recovery. An uncertain acknowledgment isn't proof nothing happened.

Full-backup restore verification must account for SQL-dump FLOAT rounding.
The October 13 workshop rehearsal caught character coordinates with identical
displayed values but different binary checksums. `tunnel-cozy-20261013/ops/rollout.py`
captures a stopped-backup precision companion using DOUBLE-promoted coordinate
values, applies it only to the isolated restore, then requires exact checksums.
Keep that companion with the backup; never replay old positions or player data
against the live DB during content recovery. The first attempt aborted before
live SQL and recovered the original layout. The corrected release passed the
complete restored forward/inverse rehearsal. Its recovery tests require a
verified stopped baseline and close the gateway again if recovery itself fails.

October 12 early-scribing rollout (`docs/releases/early-spell-scribing-20261012/`)
layers only zone onto the retained image; current dated image is
`sha256:058330bce1e2539612d705b95b726d5143daa7ca5e6897debe0f598ba470558f`.
Its native operator has nine recovery tests: if persisted player/custom drift
remains after image rollback before any access, hold the gateway closed. Never
restore SQL; once access may have opened, preserve subsequent activity. Finish
native public-baseline reports before signed client publication, then capture a
fresh service/public baseline. Concurrent launcher publication was detected and
preserved by advancing this client to 2026101203 with its existing patch history.
Twelve publisher recovery tests and all 105 hosted-file checks pass. These are
dated deployment facts, not standing deployment authority or gameplay acceptance.

Default repo promotion is feature → dev → test with explicit in-game steps → main after owner sign-off. Historical live-QA exceptions aren't standing permission. This knowledge task deploys no game change.

Read: `docs/ops/camil-silvermist-20261004.md`, `docs/releases/item-upgrades-20261012/README.md`, `docs/releases/zone-loot-20261009/PRODUCTION.md`, and the task's specific runbook. The old EQEmu skill/THJ gap map contains historical assumptions; consult the newer source and dated evidence when they disagree.

## Offline character rescue evidence

October 12 Karl rescue: production character 27 was saved in West Commonlands
after a reported zoning disconnect. A backed-up, preimage-guarded update moved
only location/heading to the DB-verified East Commonlands safe point. Full row
comparison and inventory preservation passed; no reload, restart or client
pairing was needed for the server rescue. The owner subsequently supplied an
"Unable to load World" screenshot explicitly naming missing zone file commons
in C:/Nightcap. A two-archive manual repair ZIP is prepared and its source hashes,
PFS decompression, WLD headers and ZIP round-trip verified; installation on Karl's
computer and login/zoning acceptance remain open. This is not launcher publication.
Read `E:/EQ_Local_Dev/docs/ops/karl-rescue-20261012.md` and the one-shot operator
`artifacts/karl-rescue-20261012/rescue.py`. The incident used complete current
runtime login logs plus last_login predating startup to establish offline state;
do not reuse that inference if logs are incomplete or a player is reconnecting.
Never restore an old full character row over subsequent play. Use fresh state
and a guarded location-only operation for any later rescue.

## Dungeon deployment resource and recovery contract

October 16 Raid/Grind release is on main and deployed for owner live QA; use
`docs/dungeons/deployment/` in the dungeon-modes checkout for current evidence.
The operator takes deployment/GM locks, retains a stopped full backup, rehearses
additive SQL and old/new loaders against public-only content, then regenerates
the actual production cache. It preserves 309,410 old items and adds 330.
Retain UUID ledgers/corpses/receipts; no old player snapshot restore or automatic
older-binary rollback. Uncertain SQL or opening acknowledgment closes access.

The initial buffered raw-row fingerprint exhausted the DB container's 2 GiB
limit at 18:53:02 UTC; MariaDB recovered at 18:53:04. Game/gateway did not restart
and no feature migration had begun. Use `--quick`, compact per-row SQL SHA-256
digests, DOUBLE-promoted FLOAT fields and a 128 MiB per-session memory cap.
Never buffer a full wide production item dump in a database-container client.
The active config is a read-only bind from `private/eqemu_config.json`; the
data/server path is an empty placeholder. Inspect mounts, keep secrets in memory
and redact credential-bearing SQL failures. MariaDB's utf8_general_ci and
utf8mb3_general_ci names are the sole audited schema-collation alias; do not
accept utf8mb4 or other metadata changes. Eleven focused and twenty operator
tests pass. In-game acceptance is separate; no new client assets are required.

The old world later stopped answering port 9001 without an image/container or
restart change. Ordinary preflight correctly failed, despite successful content
and cache rehearsal. A separately reviewed exact-identity completion recorded
the unhealthy baseline and revalidated public schema/content/config/native
processes before controlled activation. No cause was established for the old
stall. Check the native health port directly across >=15 seconds; cached Docker
health can lag. A zero container exit does not prove native flush: the supervisor
can kill remaining children after 75 seconds. Retain the shutdown receipt and
fresh stopped backup; never recover by replaying stale player snapshots.

## Idle-zone lifetime correction

October 17 14:47 UTC: production default `Zone:KillProcessOnDynamicShutdown`
changed true to false. `RuleManager::LoadRules` loads default before alternate
rulesets; a single stored row covered all active zones. `Zone::Shutdown` still
unloads data and saves state, but skips event-loop shutdown when false. The
supervisor itself is unchanged and still restarts everything on a native exit.

Runbook/source authority: `E:/EQ_Local_Dev/_worktrees/dynamic-zone-worker-lifetime/`
at origin/main a59974d plus the reviewed correction. Read
`docs/ops/dynamic-zone-worker-lifetime-20261017/README.md`, `ops/apply.py`,
`result.json`, `followup.json`, and `server-mods/code/zone/zone.cpp`. The deployed
journal manifest pins that zone source and the common rule loader, world/zone
reload handlers and wire declarations. Current local full-source zone.cpp lags.

Forward/inverse rollback-only transaction rehearsal passed before exactly one
live update; complete rule preimage retained privately. Authenticated global
Rules reload completed in world and all12 workers, preserving all15 native
lifetimes and all5 service identities. No binary/cache/client pairing is needed.
Natural timer-driven unload and player continuity acceptance remain pending.
Do not force a process exit to test or refresh a zone. Keep a player elsewhere
while an empty East Commonlands or Befallen instance reaches its existing timer;
verify the same worker lifetime, no supervisor restart, and continued play.

Both October16 reported incidents and another October17 10:42 a.m. Eastern
incident are in retained Docker logs. Capture the full relevant interval and
both stdout/stderr before filtering; a filtered tail missed the original cause.
OS exit code and introduction date remain unknown. Native file log time differs
from Eastern; correlate using UTC Docker timestamps. On uncertain activation,
inspect the receipt and row, retain false and retry the supported reload; never
automatically re-enable the restart cause or restore old player data. Historical
October9/11 true-rule operations notes are dated, not current instructions.
