# AGENTS.md

This file provides guidance to Codex (Codex.ai/code) when working with code in this repository.

## Repo overview

Personal EverQuest emulator dev workspace — five independent subprojects in one directory. Each has its own dependencies and tooling; there is no root `package.json` or shared build system. Always `cd` into the subproject before running commands.

| Subproject | Stack | Purpose |
|---|---|---|
| `akk-stack/` | Docker Compose + C++ (vcpkg) | Containerized EQEmu server |
| `eq-solo-gm/` | Vue3 + Vite + Express | Web GM tool |
| `eq-expansion-switcher/` | Go + Wails + Vue-TS | Windows desktop EQ expansion switcher |
| `eqemu-monocle/` | PHP/Laravel | Zone tools web app |
| `eqemu-install-v2/` | Go | Spire installer |
| `Client_RoF2_Dev/` | Binary | RoF2 game client — do not modify or build |

## akk-stack

All commands run from `akk-stack/`:

- `make up` / `make down` — start/stop Docker containers
- `make bash` — shell into eqemu-server container
- `make mc` — MariaDB console
- `make mysql-backup` — dump database
- `make install` — first-time full install
- `make env-scramble-secrets` — initialize `.env` secrets
- `make env-transplant` — merge `.env.example` into existing `.env`

**C++ source** (`akk-stack/code/`): uses **tab indentation** (not spaces). The `vcpkg/` subdirectory is a large git submodule — do not modify or delete it.

## eq-solo-gm

- `npm run dev` — starts API on port 3001 and Vite on port 5173 concurrently
- MariaDB is on **port 3307** (not 3306); database is `peq`
- DB credentials are **hardcoded in `api/server.cjs`** — there is no `.env` for this project

## eq-expansion-switcher

- `wails build -platform=windows/amd64` — local Windows build
- `make ci-build` — full release (requires `GH_RELEASE_GITHUB_API_TOKEN` in `.env`)
- CI runs on Drone.io, triggers on push to `main`

## eqemu-monocle

- Copy `.env.example` → `.env` and set DB credentials before first use
- `docker-compose up -d workspace` — start dev container
- `php artisan zonetools:*` — zone-related artisan commands

## Domain knowledge

`.Codex/skills/eqemu/` — EQEmu/Nightcap server internals (caches/reloads, RoF2 client limits, Perl DB API) and the THJ replication spec with gap roadmap (`thj-blueprint.md`). Consult it before touching server systems; keep it updated as systems change.

## Server ops

- **Spell access is per character in production release 2026092005**: use
  `common/spell_class_catalog.h`, generated from the pinned original spell file,
  for learnable spell levels and ownership. Never widen shared `spells_new` class
  columns on class selection or run the retired global `sync-spell-access.ps1`.
  The matching signed client handles merchant and scribing gates; ship both.
  New custom learnable spells require a reviewed catalog entry. Rollout and
  exact QA: `docs/releases/production-bugfixes-20260920.md`.

- **Quest API compatibility is a release gate**: a successful Perl mock test
  does not prove the running zone exposes its mocked methods. Production startup
  checks the native economy/OOC/spell contracts before accepting players. Keep
  the full paired build provenance and verify actual running hashes.

- **OVH owner-test host**: `/opt/nightcap/deploy/production` runs the private
  database/game/gateway/web/tunnel Compose stack for `play.nightcapgame.org`.
  Requests to "push to the server" target this OVH stack; the local akk-stack
  is a separate development deployment.
  Use `sudo docker compose`; no host game or database ports are published.
  Stop `gateway game` for gameplay downtime; never use `down -v` on this data.
  SSH, Cloudflare and gateway allowlists need coordinated owner-IP changes.
  Initial activation, verified account namespace migration and open native/R2
  acceptance gates: `docs/releases/ovh-activation-20260920.md`.

- **Custom rules require matching world and zone builds.** World deletes rules
  absent from its compiled catalog during boot. The old world removed
  `Character:AAExpMinLevel` despite the newer zone supporting it. Build/deploy
  both when `common/ruletypes.h` changes, and verify required values after boot.
- **PoK relocation also needs saved-state handling.** With
  `Zone:StateSavingOnShutdown=true`, `zone_state_spawns` can restore old positions
  and deleted NPC spawns. Back up and invalidate only the affected non-corpse,
  correct-instance cache rows; retain unrelated states. Evidence and scoped
  rollback rehearsal: `docs/releases/live-qa-20260915/`.

- **Docker data disk**: stored at `E:\Docker\wsl\disk\docker_data.vhdx`; the original `%LOCALAPPDATA%\Docker\wsl\disk` is a directory junction to that folder. Keep E: available before starting Docker. Migration evidence and rollback details: `docs/ops/docker-data-migration-20260913.md`.
- **Era lock is declarative**: `era.json` (repo root) is the source of truth; `tools/apply-era.ps1` applies it idempotently (+`-Check` for drift, `-CapCharacters` to de-level). Change era = edit era.json, commit, run the script. Do not set expansion rules by hand or via the GM tool.
- **PoK class hub**: `tools/pok_hub.py` plans from `docs/pok/hub-stock-audit.json` (original class levels, not widened `spells_new` columns). `tools/pok_hub_migration.py` generates guarded forward/rollback SQL; `tools/pok_hub_restock.py` generates the canonical restock. `docs/pok/catalog-policy.json` gates era promotion before writes. Current catalog preserves the existing expansion-0, level-50 item pool; extending it requires review and regeneration. Activation/rollback and exact player QA: `docs/pok/QA.md`. Candidate only until the recorded in-game QA passes.
- **DB backups**: `tools/backup-peq.ps1`, scheduled daily 04:00 (task `NightcapPeqBackup`), 14-day retention, includes the era drift check. Take a manual backup before destructive SQL.
- **Ring geometry**: validate against `zone.map_file_name`, not only the short
  zone name. The September 20 resident candidate found missing `lavastorm_v0.map`;
  `lavastorm_orig.map` is the verified Classic source. The approved activation
  installed the byte-identical alias; do not substitute newer terrain. See
  `docs/economy/residents/README.md` for the hash and activation gate.
  Client terrain must also match: the supplied `lavastorm.s3d` passes the ring
  geometry check and is staged, but the signed QA update is not yet installed.
  Khalure withholds Lavastorm until `nightcap:classic_lavastorm_client_ready=1`.
  Do not enable that global gate merely because one client was patched.
- **Market build provenance**: `tools/build_living_economy.py` requires a fresh
  output directory. Never reuse objects after copying sources with preserved
  mtimes. Source hashes must stay identical across compilation; run
  `tools/check_living_economy_binary.py <world>` before installation, then verify
  the actual startup rotation and running world/zone hashes.

### Advanced loot deployed for live QA

The owner explicitly authorized direct main and hosted live deployment on
September 30, 2026, with manual acceptance to follow live. This is release-specific;
retain all open gameplay QA and receipt-aware recovery gates.

The implementation lives in `eq-client-dll` and the tracked `server-mods/code` overlay;
the original RoF2 installation remains read-only. The server owns physical-drop
IDs, corpse permissions, filters, rolls and checked transfers. Never award items
from client row data or open the classic corpse window as an automatic substitute.
Item/coin receipts commit with inventory/currency and survive saved-state replay.
Retain receipt tables; an older receipt-unaware binary must not load unreconciled
NPC checkpoints. Current scope, evidence and exact native QA:
`docs/releases/advanced-loot/README.md` and `docs/releases/advanced-loot/LIVE-QA.md`.
Matching hardened world/zone and signed game 2026093006 are deployed on OVH;
`docs/releases/advanced-loot/PRODUCTION.md` owns activation and recovery evidence.
Keep injected faults/synthetic loot in the isolated `QA.md` plan. A previous
deployment's binary rollback helper is not valid after this receipt boundary.

### Multiclass release candidate

The AA ownership feature uses `Client::ReleaseMulticlassSlot(slot)` to commit
class slots, canonical AA refunds and skill clamps together. Quest code must
check the boolean result and must not update `character_multiclass` before
calling the retired `PurgeAfterClassRelease` API. Deploy the matching binary and
multiclass plugin together. The owner authorized promotion to main for live QA
on September 15, 2026; this is not a record of completed manual acceptance.
Current scope and QA: `docs/releases/main-live-qa-20260915.md` and
`docs/releases/live-qa-20260915/QA.md`.

### September 19 client/gameplay candidate

The owner explicitly authorized signed repair release 2026091905 in
`Client_RoF2_Dev/everquest_rof2` on September 19. It was installed through the
verified launcher and all 13 managed files/runtime features checked; eqgame.exe
remained unchanged. This scoped exception does not authorize arbitrary client
binary/data edits. Current delivery evidence is in the skin-repair release guide.

RoF2's UI parser requires literal unprefixed `Schema` with both
`xmlns="EverQuestData"` and `xmlns:dt="EverQuestDataTypes"`. Generic XML
namespace rewriting (`ns0:Schema`) makes the entire skin fall back to Default.
Preserve these declarations and verify native character loading; successful
runtime hook health alone does not prove that a skin loaded. See
`docs/releases/client-skin-repair-20260919.md`.

`docs/releases/client-gameplay-20260919.md` owns this candidate's activation and
in-game gates. The original client stays read-only; generate assets separately
and install into a QA copy. Native SEH prologue signatures contain HIGHLOW
relocations: rebase their verified immediate before runtime comparison or copying
to a trampoline. Keep the on-disk signed catalog bytes unchanged.

`character_pet_armor` owns complete player item instances. Never drop/truncate it
on rollback. Transfers use no-retry transactions and full preimages; uncertain
commit acknowledgement quarantines all cursor-saving and quest-callback paths.
Saved GUIDs are CAS preimages, not runtime serials restored after inventory load.
PoK FLOAT heading rollback preimages must match float32 storage, not Python double
formatting. Rehearse forward and rollback against captured schemas before apply.

## Launcher delivery

PFS version 2 (`0x20000`) requires decompressed blocks no larger than 8192
bytes, including its filename table. A Python zlib round-trip alone does not
prove native compatibility. Run `test_classic_model_pfs.py` and validate the
generated assets before regenerating the proxy/packager hashes. An owned
process/health pass or a short timed launch does not prove global models loaded;
verify through native login/character loading. Incident evidence:
`docs/releases/launcher-play-20261001/README.md`.

Classic-model candidate policy lives in `eq-client-dll/config/classic-models.json`.
Generate isolated archives with `tools/client_classic_models.py`, verify their
inverse WLD/texture integrity with `tools/verify_classic_models.py`, then regenerate
the shared proxy/packager hashes with `tools/generate-classic-model-contract.py`.
Do not rename or delete stock archives or overwrite user INIs. Modern visuals
require `[Nightcap] UseModernModels=TRUE`; missing/invalid values force the
classic defaults. This restores native preferences when enabled. Publish the
matching proxy, config, catalog and generated assets together only after the
gates in `docs/releases/classic-models-20260930/QA.md`. Original client stays
read-only. Per the owner's September 30 clarification, creatures and playable
races without old counterparts keep their existing models.
The owner explicitly authorized this feature's main promotion and production
publication on September 30 ("Push to main and server"). Retain the outstanding
visual QA; this deployment instruction does not record rendered acceptance.

`eq-launcher/` is the Nightcap Wails/Go patcher (separate from the expansion
switcher). Its stable starter verifies a separate signed desktop channel; the
desktop checks on opening and patches before Play. Game release counters, launcher
release counters and `minimum_launcher` are independent. Preserve the legacy
inventory for old recovery journals. Signing/build/publication and forward-only
rollback: `docs/ops/permanent-patcher.md`.

## Non-obvious gotchas

- **Finite living economy**: `docs/economy/policy.json` and the reviewed catalog
  define prices and eligibility. Regenerate guarded SQL with
  `tools/generate_living_economy.py`; never rotate offers on zone boot or quest
  reload. Deploy matching world/zone plus the market plugin/quests. Money, item,
  stock and audit must remain one native transaction. Read `docs/economy/QA.md`
  before activation/rollback; preserve player progress and trade audit.

- MariaDB is always on **port 3307**, not the default 3306
- `Client_RoF2_Dev/` is binary EQ client data — never try to build, lint, or modify it
- No root `package.json` — do not run `npm install` or `npm run` from the repo root
- Subproject AGENTS.md files can be added per-directory for module-specific instructions

## Working agreement

### Core design principle: solo-preferred, demanding, balanced

Nightcap is a solo-preferred EverQuest server. Solo accessibility must preserve
meaningful difficulty: preparation, class choices, earned gear, resource management,
and encounter execution should matter. Balance is a requirement for every gameplay
change, including quality-of-life features and reward systems.

- Evaluate the combined power of multiclass abilities, AAs, gear tiers, heroics,
  augments, buffs, pets, and sustain; do not tune each system in isolation.
- Curate AA availability by expansion: remove overpowered interactions and unlock
  additional abilities/ranks with later releases. Balance against an explicit legal
  pool and rank caps; "all AAs" means all allowed in that release. Keep unrestricted
  access as a separately labeled stress test, and report actual spent points when
  a curated pool exhausts below a requested budget.
- Spell damage/healing caps and NPC HP are adjustable levers. The owner explicitly
  permits considering caps above 250 when evidence supports better balance; 250 is
  not a permanent design ceiling. Verify the active formulas and rules first.
- Preserve worthwhile progression and rewards for difficult content. Avoid making
  encounters trivial or using excessive HP as the sole source of difficulty.
- Validate balance across representative builds and progression stages, with
  reproducible encounter measurements and explicit in-game QA before promotion.

The current project assessment and observed balance baseline are recorded in
`docs/project-understanding.md` (2026-09-12; observations are dated, not permanent
claims about live state).

### Branch flow

`feature/<name>` → `dev` → `test` → `main`

- **feature branch**: temporary, one system/feature each.
- **dev**: Codex merges here and runs automated testing against the codebase.
- **test**: pause. The user runs manual in-game QA. Every promotion to `test` MUST include an explicit spike-out of exactly what to QA in game (steps, NPCs, zones, expected results).
- **main**: only after user sign-off on the manual QA.

Codex is free to commit, open PRs, and merge autonomously **up to `test`** when tests pass. `test` → `main` requires user sign-off.

**September 15, 2026 exception:** the owner explicitly requested all gameplay
changes move into main so they can test live. This authorizes the current
`test` release promotion before manual acceptance; retain all unresolved QA
and issue gates. It does not permanently remove the default branch policy.

**September 19, 2026 exception:** the owner explicitly requested all remaining
client/gameplay changes be made live and then merged into main. This authorizes
this release's deployment and main promotion before manual acceptance. Preserve
all remaining in-game checks in `docs/releases/client-gameplay-20260919.md`; this
is not a permanent change to branch policy.

**September 20, 2026 source-promotion exception:** the owner explicitly requested
the verified `test` candidate (`dd24fe0`) be pushed to main, including the pet
roster, EC hub, living economy, residents and Lavastorm package preparation.
This is source promotion, not completed manual acceptance or a new deployment.
Keep the signed-client build/install and global Lavastorm readiness gates open.
Scope and remaining QA: `docs/releases/main-promotion-20260920.md`.

**September 20 hosted integration:** the owner requested server/client updates
be combined in main and delivered to OVH. This release integrates main `014978f`
with the production launcher/hosting branch for owner QA. Retain the manual gates
in `docs/releases/hosted-main-update-20260920.md`; this does not authorize blanket
future gameplay promotion or friend distribution without acceptance.

### Commits

**September 20 production bugfix promotion:** the owner explicitly requested
"Push to main when you're done" for the NPC and multiclass spell fixes. This
authorized source promotion of tested release 2026092005. The owner then said
"And apply to the server", authorizing the completed production deployment and
matching client publication. Manual gameplay acceptance remains open; see
`docs/releases/production-bugfixes-20260920.md`.

- Small commits/PRs. One system or feature per commit, **with tests**.
- If a task is ambiguous, propose 2–3 options with tradeoffs in the PR/commit description rather than silently choosing.

### Documentation duties

- **This file**: keep conventions, commands, and architecture summary current. Update as decisions are made.
- **ADRs**: record significant decisions as short ADRs in `docs/adr/` (`NNNN-title.md`).
- **Milestone reports**: every phase ends with `docs/milestones/phase-N-report.md` — what was built, what was cut, what's shaky.
- **Lore**: when lore details are needed (rare — systems here are new, not canon), keep a running doc at `docs/lore/structure.md`, noting anything left mid-design/interrupted.

## Changelog

**Always update `CHANGES.md`** when making significant changes — C++ patches, database schema changes, quest script additions, or SQL setup file corrections. Include: what changed, why, any gotchas. This is the primary audit trail for this repo since many changes touch the live database or compiled binaries and aren't fully captured by git diffs alone.

Format: date header, area, description. Most recent entry at the top.

## Current documentation and player website

Tunnel court follow-ups use `tools/tunnel_courts.py`, not regeneration of the
historical services release. Verify terrain plus DB furniture and patrol paths.
Local PEQ has an older services roster than OVH: capture the actual target, stop
writers before final preimages, and recapture before post-activity rollback.
Khaleid is reserved at 999527. Runtime paths and exact normal-account QA:
`docs/releases/tunnel-class-courts/README.md`.

Pet command selection is separate from Pet Armor selection. The September 22
candidate uses `GetSelectedCommandPets()` for commands and retains
`GetCommandPets()` for full-roster lifecycle/spell operations. Pair server,
proxy and generated Pet Info XML; retain native pet controls for existing hotbar
assignments. Tokens invalidate when the roster changes or selection is lost
automatically. Deliberate selection keeps the token so a quick select/order pair
uses the latest player input without waiting for a snapshot round trip.
Candidate activation and exact QA: `docs/releases/pet-management-20260922/`.

Use `docs/status.md` for current deployment and issue status; `docs/README.md`
indexes operational guides and dated evidence. Preserve historical report scope.
The standalone `index.html` publishes with `.nojekyll` from `gh-pages`; see
`docs/ops/player-website.md`. Website publication does not promote gameplay to
main or replace owner in-game QA.

### Client UI request transport

Class adoption must publish the loaded class/AA snapshot when the reconciler
detects changed class slots. The client retains a valid same-zone identity and
does not poll again just because Inventory opens. Keep publication independent
of whether new skills unlock, and avoid duplicate sends from native adoption.
Regression and rollout: `docs/releases/inventory-class-refresh-20260921.md`.

Internal class/AA and pet armor requests must bypass InterpretCmd and Say's local
chat echo/history. Proxy 0.4.2 uses the pinned native channel sender with an
ASLR-aware signed guard. Keep ordinary chat and actionable server errors visible;
retain authoritative server handlers. Native evidence and QA are in
`docs/releases/client-silent-ui-20260919.md`.

### East Commonlands hub QA (September 20)

Approved service/travel plan: `docs/ecommons-hub/plan.json`; generator:
`tools/ecommons_hub.py`. Preserve original doors, merchant stock and all existing
binds. Fresh stop/capture/backup precedes SQL. New door DBIDs 40600..40621 are
range-gated, and client release 2026092002 imports PoK objects and selects classic
Nektulos by pinned EQG retirement. Recall AA 2220 owns rank 22200; use spell 42604,
type 1/category 9 and dbstr 22200 types 1/2/4, preserving type 6. Native client lists
exclude AA type 0 and its spell table stops at 45000. Exact QA and post-activity
rollback constraints: `docs/releases/ecommons-hub-20260920/README.md`.

### Hosted production owner-QA release (September 20)

`eq-launcher` owns production builds (`build-production.ps1`, `production` tag),
separate from the embedded `qacandidate` policy. Hosted channel metadata is one
canonical envelope containing the exact signed bytes and signature. Upload immutable
assets before replacing the channel. New hosts/keys/inventory require a new EXE.
`deploy/production/` owns private hosting: launcher WSS relay, fixed UDP ports,
Cloudflare Tunnel-only ingress, IP allow/deny, private mode14 scrypt login, account
provisioning and backups. Never set LSPX (even0); it enables public login lookup.
Use a separate production signing seed and retain it locally. OVH + Cloudflare at
`play.nightcapgame.org` hosts launcher0.2.2/release2026092005 and the matching native
runtime; transport/hash verification passed, but native gameplay acceptance and
R2 backup/restore testing remain open. See the production bugfix release record.
GitHub Actions deployment, patch-before-Play and EXE self-update are not implemented;
a main push alone does not change OVH. Players fetch built signed artifacts.

Before a hosted update, compare native feature contracts with the existing DB and
quests. Never restore a newer feature snapshot onto older native binaries. Rebuild
in a fresh isolated directory with the production hardening patch, verify source
stability and running executable hashes, and keep gateway access stopped until
preservation checks pass. Market stock rotates on each successful world startup.
Preserve hosted player progress and never replay initial-restore SQL for an update.
For publication recovery, inspect the visible channel before restoring pointers;
clients that saw a newer release require a higher-numbered corrective release.

### Tunnel services and creation provisions deployed for QA (September 21)

The travel alcove follow-up uses `tools/tunnel_travel.py`, guide 999810 and three
native props reusing retired city-door IDs. All twelve return/PoK books remain.
After zone activity, generate rollback with a fresh stopped-target capture via
`--rollback-from`; never replay the immediate rollback against new cached state.
Exact QA and scoped recovery: `docs/releases/tunnel-travel-alcove/README.md`.

Plugin installation must follow the target's `server.directories` config:
nonempty `plugin_paths` overrides scalar `plugins` (default `plugins/`). Production
uses `data/server/plugins/`, not `data/server/quests/plugins/`. Confirm the native
startup path log and run the installed-runtime hail smoke; `perl -c` and source
tests missed the September 22 silent-hail failure. Current recovery wrapper and
evidence: `docs/releases/tunnel-travel-alcove/HAIL-FIX.md`.

`tools/tunnel_services.py` plans from the reviewed release catalog and emits
forward/rollback SQL from `tools/tunnel_services_capture.py` preimages. Stop the
target world/zones and back up before capture/apply; local evidence is not a
production preimage. Retain starter item definitions during rollback because
characters may own them. Deploy matching world/zone, supervisor and chatter
plugins with the multi-offer market schema/procedure. Composite audit keys must
survive rollback. Starting currency belongs in `character_currency`, not merely
the creation profile. No repeatable login grants. The historical living-economy
generator intentionally refuses refresh after this coordinator is installed.
Exact scope and owner QA: `docs/releases/tunnel-services-starters/README.md`.
The owner explicitly authorized this release's main promotion and OVH deployment;
it is live for QA, not manually accepted. Activation evidence and scoped rollback:
`docs/releases/tunnel-services-starters/ACTIVATION.md`. Keep native key predicates
before exact binary row comparisons: casting every key forces repeated full PEQ
table scans. The MariaDB rehearsal checks EXPLAIN index use and case-only drift.
For a full restore rehearsal, wait for MariaDB's final PID 1 process, not its
temporary bootstrap server. Copy the compressed dump into the isolated container
and use pipefail with a private error file; captured stderr pipes can fill with
large SQL statement diagnostics and deadlock a streaming restore.
