# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

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

## Non-obvious gotchas

- MariaDB is always on **port 3307**, not the default 3306
- `Client_RoF2_Dev/` is binary EQ client data — never try to build, lint, or modify it
- No root `package.json` — do not run `npm install` or `npm run` from the repo root
- Subproject CLAUDE.md files can be added per-directory for module-specific instructions
