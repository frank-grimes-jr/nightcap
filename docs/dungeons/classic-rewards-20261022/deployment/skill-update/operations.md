# Source authority, builds and reloads

## Classic dungeon options and MAGIC rewards — October22 live testing

Owner-authorized main PR293 and paired live deployment are verified. Source
0d61d9b47322 in E:/EQ_Local_Dev/_worktrees/classic-dungeon-options. Exact receipts:
docs/dungeons/classic-rewards-20261022/deployment/. Zone8c9b97d5 preserves the latest
quest-tier matcher after byte-reproducing live6da991b6; world49f87aaf and loader
6b314bf0 are paired with the414-MAGIC cache and12 quest/module files. Signed
game2026102204 remains unchanged. All12 workers,39 schema/497 content checks,
414 cache definitions/888 rejection cases and full-cache preservation pass.
Fresh stopped backup and exact player/custom-state preservation are recorded;
only precisely authenticated native seven-day non-corpse cache expiry is allowed.
Gateway is open. Owner gameplay and solo/multiclass balance acceptance remain open.

Fresh preflight copies actual SHOW CREATE DDL, preserving foreign keys; CREATE
TABLE LIKE omits them. Copy every runtime-content dependency, including loot,
NPC spells/factions and grids. Temporary clone/user/config/cache are removed in
finally. The isolated full-item loader requires a3072MiB cap and at least4GiB
available host memory;1536MiB OOMed only that test container. Failed preflights
never changed live content/services and remain in stage/attempts. Never bypass
contract checks to make a rehearsal pass. Three packaging/cache/dependency tests
and independent operator review pass.

Stage /opt/nightcap/releases/classic-dungeons-rewards-20261022 contains the
guarded rollout and receipts. Both October22 migrations run with acquisition
disabled and the whole supervised runtime stopped; regenerate target caches,
verify all workers/state and then reopen admissions. Do not kill individual
children. After new rewards/runs exist, use compatible21-zone/414-item forward
repair; never down-migrate or restore an old player database. Thirty-six exact
unmounted historical staging files were losslessly compressed on the host with
decompressed SHA verification; adjacent .dungeon-space-20261022.gz copies and
three dungeon-space receipts preserve recovery. No live files/backups removed.


## Quest ingredient qualities — October22 deployed for live QA

Owner-authorized main PR290/c66df0e and the paired zone/seven-quest deployment
are verified in docs/releases/quest-tier-handins-20261022/deployment/. Source: E:/EQ_Local_Dev/_worktrees/quest-tier-handins.
Normal requirements accept exact generated Polished/Exalted/Ascended family
definitions (+200000/+400000/+600000) in shared Lua/native hand-ins and task
Deliver. Explicit tier requirements stay exact; epic/hunt/dungeon identities and
forging costs remain separate. Exact inputs are preferred; explicit qualities
reserve first. Failure restores tentative counts and actual item instances.
Inherited multiquest completion still clears the whole donation bucket, including
surplus; Lua retains separate trade-slot semantics.

Shakrn14075 in southkarana accepts Aviak Charm13737/213737/413737/613737 plus two
Star Rubies10032, granting the already-live Ascended Crafted Gauntlets604178.
Five soltemple scripts now share native matching for17 recipes. Kurron retains
three Darkforge pieces/raw900pp, faction and one letter/spawn; all64 ordinary
quality combinations pass. Declare submitted currency to CheckHandin, refund
once on success, use native returns on failure. Active root plugins/ differs
from unused captured quests/plugins/ fixtures; do not conflate their evidence.

Zone6da991b6 is the successor to byte-reproduced5dd5a655. Full supervised restart,
fresh stopped backup, all12 zone hashes and exact player/custom/content/cache/
client preservation verified before access reopened. Seven files only; the ten
already-live armor reward scripts remain unchanged. No SQL migration, world,
cache ABI or client update. Never kill one zone or restore player snapshots.
Windows/Linux native method tests, actual Lua callbacks,357 Perl assertions,
113 armor Lua cases,21 catalog guards and16 deployment fault tests pass.
Owner gameplay acceptance and complete task-delivery lifecycle QA remain open;
exact source/tests/build/rollback boundary and QA: docs/releases/quest-tier-handins-20261022/.

## AA million-point release - October 21, deployed for live QA
Main PR268/e64f502 and C:/Users/verre/.codex/worktrees/aa-point-cost-40000/EQ_Local_Dev/docs/releases/aa-pacing-million-20261021/ record owner-authorized
1m XP per point,10% passive, retired Goldwind scripts and timed XP boost policy.
Zone-only successor5dd5a655 is built from exact reproduced59831725 baseline;
world/shared/client/caches are retained. Full-runtime restart, fresh stopped
backup, current player/content checks and all12 zones verify before reopening.
Never kill one child or restore old player snapshots.

Two preflights stopped before live changes because image construction consumed
more than a raw zone layer. Recovery pruned only three named task build caches
and four upload archives with exact retained local copies. Pinned candidate reuse
avoided another build; backups and active services were retained. Reserve512MiB
runtime headroom after backup and before reopening.

First boot naturally expired485 non-corpse NPC cache rows older than7days in
zones38/75. An exact cache-only scratch restore authenticated the original hash,
removed set and surviving fields; all other player/custom state was unchanged.
finish_cache.py pins the after hash, preserves the original hold, takes another
stopped backup and verifies a fresh restart before reopening. Never ignore cache
drift generically or restore old earned state. Deployment and website evidence
remain distinct from owner gameplay acceptance.

## THJ custom behavior and stock gear — October 19, deployed for live testing

Owner-authorized main promotion PR256/7104c6b and OVH activation are verified in
docs/releases/thj-behaviors-20261019/deployment/. Stage:
/opt/nightcap/releases/thj-behaviors-live-20261019. Matching world/zone/cache loader,
three guarded SQL components and regenerated target caches are installed. Signed
game2026101902 retains proxy0.11.0, its matching catalog and all136 unrelated assets;
all138 hosted files verify with shipped trust. Classic50 and209 starter families
remain. Owner gameplay and balance acceptance remain pending; ../QA.md owns tests.

The retained paired operator verifies a fresh public clone, stopped full backup,
player/custom receipts, full content/control hashes, market rotation and all12
zone processes before opening access. Recovery preserves earned AA/refund state;
never restore player snapshots or blindly retry an uncertain component. Rule SQL
uses compiled descriptions, preventing startup normalization from invalidating
inverse guards. Existing runtime credentials generated complete target caches;
no new database account or grants were needed. The optional earlier local cache
smoke remains skipped, superseded for deployment by verified target generation.


The first live procedure compilation hit the2GiB DB cgroup limit after clone
rehearsal; kernel evidence and exact unchanged content/player receipts justified
resume_oom.py with a fresh backup (11 admission tests). The next boot expired1113
non-corpse NPC cache rows older than7days in zones13/25/30/73. Built source and a
cache-only scratch restore authenticated the exact deletion and preserved
survivors/all other player state. finish_zone_cache.py owns the final open action;
original attempts remain immutable. Never blanket-ignore cache/player drift.
Recovery cache files are lossless hash-verified private-backup/cache-items.gz and
cache-spells.gz; decompress only for a correctly paired stopped recovery. Final
headroom is about1.47GiB; retain images/backups and check space before later work.

## Current all-class AA release — October19, live QA open

Main PR250/c3f0686 and owner-authorized OVH activation are verified at
docs/releases/thj-all-class-aa-20261019/deployment/. Stage:
/opt/nightcap/releases/all-class-aa-20261019. Current image:
sha256:32bf376af4402c3288c83c5d72f2810b8d35ddae06327d5521d1efb6b20ef942.
All12 zones match e1dd9c4cdd6bf95db7ffc909f224b1603e9e07e1ad05925bcdd7bd0359cd3eb0.
This is a zone-only policy successor to the October18 combined image; unchanged
world/shared_memory retain its ItemData/cache contract. Only Healing Boon389
classes518→550 changes content. Classic50, all rules/caches/quests, current
client2026101901 and all138 published assets are preserved.

The stopped64,416,158-byte gzip backup passed integrity;47 player tables and28
custom/timer tables preserve earned state without restoration or grants. One
market startup85→86 has42 valid offers within44 slots. Access is healthy/open;
owner AA gameplay/balance acceptance remains pending.21 Windows/Linux operator
groups and independent review cover disk gates, SQL uncertainty and recovery.
Preflight authenticates all4 AA tables; candidate fixture normalization changes
only the expected Healing Boon preimage in memory. Isolated clone replay and
inverse checks pass. SQL attempted/committed receipts are never blindly replayed.

Rollback keeps new earned ranks dormant and restores only the prior image plus
guarded Healing Boon inverse, with a fresh stopped backup. Before any opening
attempt, unexplained original player/timer drift and the first market rotation
must verify before recovery can proceed. Later player gains are preserved.
Do not restore old player rows or kill one zone under the whole-runtime supervisor.
Final disk headroom was about2.1GiB; check capacity before later builds and retain
recovery artifacts. Operator reserves backup/cache space and1GiB headroom.

## Combined THJ item/spell and pet/WPM deployed — October 18, 2026

Source: C:/Users/verre/.codex/worktrees/thj-item-spell-parity/EQ_Local_Dev. Owner-authorized main/OVH deployment is verified in
`docs/releases/thj-parity-20261018/deployment/README.md` and `receipts/`. PR235 promotes the tested source;
signed client2026101802/proxy0.11.0 and wiki20261018-thj-parity-v1 are published
and verified. Classic50 remains active; level65/PoP and389 stock additions stay
staged. Owner gameplay and balance acceptance remain open. Exact testing:
`docs/releases/thj-parity-20261018/QA.md`; measured limitations: `COMPARISON.md`.

Production stage /opt/nightcap/releases/thj-parity-20261018 runs the full
reviewed image sha256:7013e41696649bb82d5776659b3b21c37456862f4c90ecc44805f5d6b2fcc258.
All12 zones, world and shared_memory match native-build-manifest.json;119 source
overlays retain the cooldown/auth/reforge base. Ten guarded content components,
regenerated item/spell caches and signed138-file client are verified. A fresh
stopped64,405,100-byte compressed backup passed integrity. 46 player and
28 custom-table receipts preserve owned state without restoration.
Game/gateway are open and healthy; db/web/tunnel were preserved. Final disk
headroom was3.6GiB; retain recovery artifacts and check capacity before later builds.

The first boot held access only because RuleManager::UpdateInjectedRules
(retained common/rulesys.cpp) replaced three descriptions with compiled notes;
values and other content matched. resume_rule_notes.py authenticates exactly
those transitions and rehearses ten corrected recovery/reapply checks on the
public clone. No production SQL replay or player snapshot restoration occurred.
Use resume_pinned.py for a retained restart: it authenticates/reselects the new
immutable image under both deployment/GM locks before recovery.resume(). The
original rollout.py open is not valid for this reviewed hold. Recovery open
requires all138 HTTPS assets verified by the shipped-key manifest parser.
Both market startup epochs are authenticated independently. New holds need a
fresh diagnosis. Existing procedure remnants must be inspected before retry.

New rules require paired world/zone; regenerate both caches and use a supported
full runtime restart. Do not revert to the older eight-location pet binary or
delete earned AA content while new state is owned. Formula disable/enable and
numeric recovery preserve sockets/effects/owned data. Exact operator source,
29 regression groups, content rehearsal and deployed receipts are in deployment/.
Native47-case and165-test evidence remains distinct from player acceptance.

## October18 reforging successor deployment

The current zone-only successor to the cooldown release is in
C:/Users/verre/.codex/worktrees/reforge-default-colors/EQ_Local_Dev,
docs/releases/reforge-colors-20261018/. Native zone29b8093147ffbc4c0d387a4e3fa55a3a041dbb9ae7da731b493b21601a6dec2f
preserves the d3908e cooldown baseline and its migration. Whole-runtime restart,
fresh stopped backup,12 zone hashes,47 player/28 custom tables and client2026101801
verify; access is open. No SQL/schema/cache/client update. The owner confirmed
the reported Palwar combine; broader QA remains open (owner-acceptance.json).
The market procedure skips exhausted pools: authenticate a single startup epoch,
present-offer eligibility/prices/stock and actor/scarcity capacities, not mandatory
full slots. Epoch82→83 retained42/44 valid offers with no player snapshot restore.

BuildKit interprets a bare image ID in FROM as a registry name. Create a scoped
local baseline tag from the authenticated immutable ID, verify its resolution
before/after --pull=false build, then verify all binary hashes and exact base
layers plus one. The operator's12 test groups cover failures and recovery.
Never roll back to the pre-cooldown timer binary. Recovery retains current data.

## Resolve the source before editing

- Main workspace: `E:/EQ_Local_Dev`. Current October17 integrated release checkout: `E:/EQ_Local_Dev/_worktrees/october-17-release`, main via PR220. Use its latest deployment record and exact retained build manifest; older merchant-sell-all and default mirrors lag. These are dated anchors, not branch-switch instructions.
- The default checkout was `feature/npc-heal-self` at `ce161c5`; local main was still September history. Its `docs/status.md` missed many October deployments. Use `git worktree list --porcelain`, scoped log/diff and exact paths; don't switch a shared checkout or assume local main is the latest release.
- `server-mods/code/` is the tracked customization overlay, not a complete compilable source tree. Local full source is `akk-stack/code/`; local live quests/plugins are `akk-stack/server/quests/` and `akk-stack/server/plugins/`. Compare relevant copies, normalizing line endings only for semantic comparison; deployment hashes remain byte-exact.
- Production builders layer reviewed patches onto fingerprinted retained source. Preserve authentication hardening, advanced-loot receipts and intervening releases. A generic local build or an older development archive is not a valid production replacement.
- Other project `C:/nightcap-development-mmo` contains character/texture/production labs, not the core EQEmu implementation. No root package.json/shared npm build exists. Local PEQ is port 3307. Don't read credential-bearing API/config files wholesale.

## October 17 combined release and storage

docs/releases/october-17-2026/ owns the full zone rebuild from the fingerprinted
dungeon-journal source, proxy0.10.0/game2026101702 pairing, SQL/cache checks and
guarded activation. Client layout changed: rebuild all zone units, not selected
retained objects. World/shared_memory and ItemData ABI are unchanged. Production
stage is /opt/nightcap/releases/october-17-2026. The owner replied "Confirmed"
on October 18 to the combined release report. This is general release
confirmation; individual scenarios and balance measurements were not enumerated.
Scope: docs/releases/october-17-2026/owner-confirmation.json. Preserve newer
cooldown, client and reforging releases and their separate acceptance records.

Preflight encountered a full72GB filesystem. Reclaimed only redundant transferred
archives and unused Docker build cache; all image tags/service lifetimes/volumes/
backups were verified preserved. Check headroom for image layers, stopped backup
and cache before release. Never substitute broad image/volume prune. Local Docker
Desktop recovered from stale runtime sockets with data disk preserved; exact
procedure: docs/ops/docker-stale-sockets-20261017.md.

Hold the gateway through server verification and signed client publication.
The unchanged world rotates finite market stock at startup. Authenticate the
single epoch change, offer policy and unchanged trade/player records before
reconciling those two checksums; retain original held receipts.
Operator failures preserve current state and require receipt-aware inspection;
never replay uncertain SQL or restore player snapshots. Rollback pairs the prior
image/client using a higher signed counter. Keep stack limits100 after access
could open. New deployment/QA is required for later releases; this authorization
is not standing permission.

## Cooldown identity deployment and recovery

PR223 promoted the reviewed correction to main on October18. Source checkout:
C:/Users/verre/Documents/Codex/2026-10-17/see/work/cooldown-identities.
Exact build,25 operator tests,9 resume tests,7 completion tests, source/native/migration tests
and live receipts: docs/releases/cooldown-identities-20261017/ (deployment/).
OVH stage /opt/nightcap/releases/cooldown-identities-20261018 runs zone SHA
d3908e0348715e94955d84f629e4f27e91f15c7dd661e437efbba580ce3d216a.
All12 running zone hashes, health, atomic receipt and preserved deadlines pass.
Owner gameplay acceptance and generic/content-defined sharing remain open.

Internal keys are uint32 within SQL unsigned24-bit; authorized zone admission
requires version1 atomic migration receipt and timer-load failure disconnects.
Pair the rebuilt zone with guarded stopped-game SQL; rule/quest reload is
insufficient. Existing proxy0.10.0 is retained. Concurrent signed client2026101801
preserves all106 old bytes and adds32 Classic zone assets; original preflight
correctly rejected changed channel metadata before any service/SQL change.

Actual forward/reverse conversion was rehearsed in a disposable schema after a
fresh stopped backup. Unindexed CTAS catalog copies made this slow; future
rehearsals should preserve lookup indexes before evaluating full-catalog guards.
The first activation then held before live SQL because a concurrent authorized
character port changed five location columns. A separate one-shot resume proved
the exact difference against a scratch-restored backup, preserved the move, took
a supplemental backup and continued from the verified checkpoint. No original
receipt was erased, no uncertain SQL replayed and no player snapshot restored.
The next check held after migration because it wrongly required all44 market
slots filled. The separate finish.py verified the committed migration and both
holds, then proved42 offers valid and every deficient actor's pool exhausted.
It contains no migration SQL or restore path. Both restart epochs80→81→82
were authenticated. Original operators/manifests/holds remain immutable.

Locks do not protect against an external operator that ignores them. On drift,
identify the actual writer and fields before reconciling a narrow baseline;
never accept all new player state just to pass a check. Failed holds independently
attempt both stops and record observed false/true/unknown states.

Keep receipt and rows together on recovery. Reverse migration preserves current
deadlines, rejects unknown keys and removes all namespaced rows before the old
uint16 loader starts. Never reset all timers or restore old player data. The
two world starts rotated market epoch80→81→82 with policy/trade state intact.
Verified cooldown image: sha256:4b1c7b78964f975baa1323baf6b18fe504cd59988e08d0f502501f22f4d5a56a. Access opened;
the separately authorized reforging successor now owns the next runtime change.
Read its current receipt before future deployment. No standing rollout permission.

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

Default repo promotion is feature → dev → test with explicit in-game steps → main after owner sign-off. Historical live-QA exceptions aren't standing permission. The October 17 combined main/server release was explicitly authorized by the owner; later releases require their own applicable authorization.

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
