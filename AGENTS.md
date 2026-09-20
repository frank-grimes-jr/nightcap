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
  Client terrain must also match: the QA RoF2 copy lacks `lavastorm.s3d`, so
  Khalure withholds Lavastorm until `nightcap:classic_lavastorm_client_ready=1`.
  Do not enable that global gate merely because one client was patched.
- **Market build provenance**: `tools/build_living_economy.py` requires a fresh
  output directory. Never reuse objects after copying sources with preserved
  mtimes. Source hashes must stay identical across compilation; run
  `tools/check_living_economy_binary.py <world>` before installation, then verify
  the actual startup rotation and running world/zone hashes.

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

### Commits

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

Use `docs/status.md` for current deployment and issue status; `docs/README.md`
indexes operational guides and dated evidence. Preserve historical report scope.
The standalone `index.html` publishes with `.nojekyll` from `gh-pages`; see
`docs/ops/player-website.md`. Website publication does not promote gameplay to
main or replace owner in-game QA.

### Client UI request transport

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
