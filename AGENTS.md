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

- **Era lock is declarative**: `era.json` (repo root) is the source of truth; `tools/apply-era.ps1` applies it idempotently (+`-Check` for drift, `-CapCharacters` to de-level). Change era = edit era.json, commit, run the script. Do not set expansion rules by hand or via the GM tool.
- **DB backups**: `tools/backup-peq.ps1`, scheduled daily 04:00 (task `NightcapPeqBackup`), 14-day retention, includes the era drift check. Take a manual backup before destructive SQL.

## Non-obvious gotchas

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
