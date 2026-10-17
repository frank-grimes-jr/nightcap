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
- Local DB credentials are in `api/lib/database.cjs`; production credentials are read into backend memory over pinned-host SSH, never sent to the browser.
- `Start Nightcap GM.cmd` opens the owner-local UI. API binds only `127.0.0.1:3001`; Vite development binds loopback `5173`.
- `Start Nightcap GM Production.cmd` starts the owner-approved main release with production writes. Both shortcuts reuse the existing process without changing its mode; local session capabilities let the UI open even when SSH/DB is unavailable.
- Production writes require the reviewed release on `origin/main` and `tools/start-gm.ps1 -EnableProductionWrites`. Default startup is a read-only production preview.
- Character boosts must set cumulative XP using the native float32 threshold,
  preserve valid same-level progress and highest attained level, and credit new
  lifetime training points once. Never set `exp=0` for a level above1. Run
  `tools/tests/test_boost_xp.py` against changed native XP formulas; zone/Lua
  curve changes require revalidating the GM adapter. Incident and repair:
  `docs/ops/darthy-boost-20261012/README.md`.
- GM character/rule/vendor/deletion changes require explicit maintenance. A database advisory fence prevents resume while SQL is in flight. Do not bypass it or kill individual production zones.
- `npm test`, `npm run typecheck`, `npm run build`, `npm run test:browser` are the GM checks. Real disposable-DB and maintenance rehearsal details: `docs/ops/production-gm-20261010.md`.

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

- **Release disk headroom:** inspect free space before staging, image builds,
  stopped backups and cache regeneration. October 17 exhausted the 72 GB production
  disk during preflight. Only redundant transfer archives and unused Docker build
  cache were reclaimed; all image tags, service lifetimes, volumes and backups
  were verified preserved. Do not substitute broad image/volume cleanup.
- **Market stock rotates at world startup:** the unchanged world calls
  `nightcap_market_rotate`, incrementing its epoch and replacing finite offers.
  Authenticate that single transition and offer policy separately from player
  currency, inventory, trade audit and other custom state; retain original held
  receipts. October 17 evidence: `docs/releases/october-17-2026/reconcile_market.py`.

- **Idle production zones must preserve their worker process.** October 17
  correction sets inherited default `Zone:KillProcessOnDynamicShutdown=false`;
  alternate rulesets must not override it to true while `/opt/nightcap/start.py`
  restarts the whole runtime on any child exit. Existing values require a global
  world/zone rules reload, not a process kill. Activation and reload are verified;
  natural idle-unload/player-continuity acceptance remains pending. Current
  evidence: `docs/ops/dynamic-zone-worker-lifetime-20261017/README.md`.

- **Player access codes are live (October11):** issue/revoke personal codes from
  the owner-local production GM tool. Gateway `PLAYER_ACCESS_FILE` replaces
  `ALLOW_CIDRS`; Windows DPAPI remembers each launcher's code. Mount the registry
  directory read-only so atomic replacements are visible. Cloudflare exempts only
  native GET/HEAD paths from its player-IP check; other route/host protections
  remain. Do not add changing player IPs as the access lifecycle. Native ports
  stay private. Deployment/recovery: `docs/ops/player-access-20261011.md`; exact
  player QA and operator recovery: `deploy/production/PLAYER-ACCESS.md`.

- **Passive AA experience**: `AA:PassiveExpPercent` controls additive kill/quest/task
  AA at 0% allocation; `#aaexp on|off` selects 100% or 0%. Tiny gains round down.
  Percentage rewards must preserve independent level/AA modifiers and missing-row
  behavior. Catalog changes require matching world/zone. Existing values use
  `#reload rules global`; OVH uses 20% as of October 13 (compiled fallback 1%),
  with `AA:ExpPerPoint=4000`. Preserve points and partial XP; reload never rewrites
  player progress. Tuning and recovery: `docs/ops/passive-aa-twenty-20261013/README.md`.
  Tests, calibration and exact QA: `docs/releases/passive-aa-20261004.md`.

- **OVH zone exits restart the whole runtime.** The deployed start.py supervises
  every native child. Use a supported zone-unload mechanism for a single-zone
  refresh; do not assume local eqlaunch restart behavior applies to production.
  Evidence: docs/ops/camil-silvermist-20261004.md.

- **All-item LORE removal**: OVH uses Items:DisableLore=true as of October 12.
  The native shared-memory loader clears effective LoreFlag/LoreGroup while
  preserving original SQL definitions. Rebuild cache/restart game for changes;
  rules reload alone is insufficient. Never blindly re-enable LORE after players
  acquire duplicates: native cursor checks can delete conflicts. Evidence and
  exact QA: docs/releases/remove-item-lore-20261012/README.md.

- **Universal item trading**: Items:FreeTrade projects effective item
  flags and fixed former-NO-DROP resale from original SQL definitions. Preserve
  raw SQL flags and IsAttuned() persistence; use IsAttunedForTrade() for restrictions.
  ItemData layout changed: pair all native binaries with a regenerated cache,
  including on rollback. Merchant and #sellall share the fixed payout. Scope and
  QA: docs/releases/free-trade-20261004/README.md.
- **Epic 0.5 journal candidate**: native Tasks own progress; the character
  `nightcap_epic05_state` row owns only attunement/cooldown. Pair the native
  `Epic05Contract()` duration guard, three plugins, `global/items/900501.pl`,
  tasks 9500–9507 and spells 42800–42805. The SQL gate starts disabled. Native
  task history and proximity rules are required; Explore=5 credits movement,
  while Touch=11 is a dynamic-zone switch. Preserve owned definitions/history
  on rollback. Verify Classic gates on both spawn2 and spawnentry; spawn2 has
  no enabled column. Install plugins via configured plugin paths. Full scope,
  rehearsal and manual test route: `docs/adventure-journal/README.md`.

- **Spell access is per character in production release 2026092005**: use
  `common/spell_class_catalog.h`, generated from the pinned original spell file,
  for learnable spell levels and ownership. Never widen shared `spells_new` class
  columns on class selection or run the retired global `sync-spell-access.ps1`.
  The matching signed client handles merchant and scribing gates; ship both.
  New custom learnable spells require a reviewed catalog entry. Rollout and
  exact QA: `docs/releases/production-bugfixes-20260920.md`.
  Scroll inspection has separate canonical mask/level hooks: legacy item masks
  can include unusable classes, and the held-primary level projection must never
  label an original class. Audit/QA: `docs/releases/spell-inspection-20261001.md`.

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
  SSH retains its separate owner-access policy; player launcher/play traffic uses
  access codes as of October11, independently of changing player IP addresses.
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

- **Current tunnel layout**: `tools/tunnel_compact.py` and
  `tools/tunnel_compact_layout.py` own the compact class/service areas and
  tradeskill workshop. All 119 actors remain. The accepted six-resident ring,
  costumes and native fire from `tools/tunnel_campfire.py` must be preserved;
  do not rerun older social/court layout migrations over them. Capture fresh
  stopped-server preimages, invalidate only relocated actors' non-corpse
  instance-0 states, and retain fresh caches for unchanged actors on rollback.
  Current deployment and exact QA:
  `docs/releases/tunnel-compact-20261002/README.md`.

- **Docker data disk**: stored at `E:\Docker\wsl\disk\docker_data.vhdx`; the original `%LOCALAPPDATA%\Docker\wsl\disk` is a directory junction to that folder. Keep E: available before starting Docker. Migration evidence and rollback details: `docs/ops/docker-data-migration-20260913.md`.
- **Era lock is declarative**: `era.json` (repo root) is the source of truth; `tools/apply-era.ps1` applies it idempotently (+`-Check` for drift, `-CapCharacters` to de-level). Change era = edit era.json, commit, run the script. Do not set expansion rules by hand or via the GM tool.
- **AA offering has a separate compiled policy**: `era.json.aa_policy` selects `config/aa-policy.json`; `tools/aa_tbs_policy.py` generates the native rank/level allowlist. Every allowed rank opens at level 1. Regenerate and rebuild/deploy zone after changes; era SQL and AA/rule reloads do not install compiled caps. Preserve full AA definitions and canonical earned ranks/charges—do not disable definitions or truncate chains to hide purchases. The 26-line class expansion pairs the policy with `special_attacks.cpp` so earned Triple Backstab works below the native level-55 gate. Exact limits, guarded OVH restart, rollback and owner QA: `docs/releases/aa-class-ranks-20261013/README.md`.
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
The October 2 client interaction repair is signed generation 2026100201. Its
timeout retry refreshes state and must never replay an uncertain award. Native
click/render/acknowledgment acceptance is separate from controller fixtures and
publication checks; see `docs/releases/advanced-loot/UI-REPAIR.md`.
The subsequent action repair is paired world/zone plus signed game 2026100203.
Earned advanced loot (including existing auto-coin collection) is zone-wide;
classic/public loot keeps its 25-unit range. Bulk NO TRADE confirmation binds
session/revision and physical preimages, including bag contents; recheck after
each quest callback and never replay uncertain transfers. Current evidence and
owner acceptance: `docs/releases/advanced-loot/ACTION-REPAIR.md`.
Keep injected faults/synthetic loot in the isolated `QA.md` plan. Roll back only
to an explicitly verified receipt-aware image while retaining current data;
pre-receipt deployment rollback helpers are invalid after this boundary.

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

Player-facing client releases must maintain `eq-launcher/patch-notes.json`:
newest release first, dated, concise `feature`/`fix` bullets, retaining history.
Include it using `nightcap-package -patch-notes patch-notes.json`. Notes are part
of the signed game manifest; never edit a published release in place. Notes need
desktop/minimum launcher 0.6.0+, published through the stable starter before the
game channel. Verify actual channel counters before assigning the next release.
Desktop 0.6.0 and game release 2026101202 were published October 12 under explicit
owner approval. Future releases must preserve/update notes and the 0.6.0 floor.
See `docs/ops/permanent-patcher.md` for publishing and exact visual QA.

The winged Paladin helmet candidate is documented in
`docs/helmets/winged-paladin.md`. Its Blender/Unity assets and pinned native WLD
builder live under `assets/winged-helmet/` and `tools/*winged_helmet*`.
It appends head material 90 for the twelve original races, both genders;
High Elf uses HIM/HIF, not Wood Elf ELM/ELF. Build outside the read-only source
client, preserve existing archive fragments/textures, and install through the
signed launcher. Release 2026100401 is live; item 990500 is loaded in SQL/shared
memory and Camil 999521 uses head material 90, with his saved state retained.
Native wear and rendered Camil acceptance remain pending. Deployment evidence:
`docs/releases/winged-helmet-20261004/README.md`.

PFS version 2 (`0x20000`) requires decompressed blocks no larger than 8192
bytes, including its filename table. A Python zlib round-trip alone does not
prove native compatibility. Run `test_classic_model_pfs.py` and validate the
generated assets before regenerating the proxy/packager hashes. An owned
process/health pass or a short timed launch does not prove global models loaded;
verify through native login/character loading. Incident evidence:
`docs/releases/launcher-play-20261001/README.md`.

RoF2's per-actor WLD importer also filters bitmap (03), material (30) and palette
(31) fragments by the actor's three-letter prefix. Zone archives can reference
shared materials outside that prefix. `classic_model_materials.py` scopes those
dependencies while retaining ordered material graphs and geometry/animation
bytes. Validate every imported actor's dependency closure, not only PFS integrity
or reversible renaming. The native null-material crash and regression evidence:
`docs/releases/character-select-crash-20261001/README.md`.

Invisible actors must retain native IVM/IVF registration: EQGraphicsDX9 has a
separate prefix check at RVA 0x44EA2 that excludes them from automatic animation
startup. A renamed IVM still twitches after restoring its animation family.
The pinned native regression is `model-invisible-native`; user retest is
recorded in `docs/releases/npc-animation-20261004/enchanter.md`.

Classic NPC aliases must preserve RoF2's animation-family lookup (RVA 0x6A60).
Use the actual source skeleton code, including ELE for typed elemental clones,
and retain the native sharing flag. Archive/frame-byte integrity alone does not
prove animated rendering. Run the pinned-client `model-animation-native` test
and the visual matrix in `docs/releases/npc-animation-20261004/README.md`.

Classic-model candidate policy lives in `eq-client-dll/config/classic-models.json`.
Generate isolated archives with `tools/client_classic_models.py`, verify their
WLD material/geometry/texture integrity with `tools/verify_classic_models.py`,
then regenerate the shared proxy/packager hashes with `tools/generate-classic-model-contract.py`.
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

## Recommended AA — deployed October 17

`common/aa_recommendations.h` selects presentation guidance; native AA policy and
ownership still authorize purchases. Pair zone's `aa_recommendations.inc` with
proxy 0.10.0 / game 2026101702 and generated AA XML. Keep the bounded identity-scoped metadata
opt-in and native pre-row filter; do not delete rows after selection or globally
change AA eligibility. Source/test/release state and exact QA are in
`docs/releases/october-17-2026/README.md`. All 107 guards and the complete zone
build pass; visible gameplay acceptance remains open. This is not a future deployment grant.

## Non-obvious gotchas

- **Food/drink removal deployed (2026-10-11):** hunger/thirst/starvation predicates
  always return false; login and stamina/setter packets report both meters full.
  Legacy nutrition rules cannot restore this system. Consume packets preserve
  inventory; optional edible bonuses remain. OVH rollout passed; RoF2 rendering
  remains owner QA. Evidence: `docs/ops/food-drink-removal-20261011/README.md`.

- **Classic alternate heads require contiguous meshes.** RoF2 discovers head
  variants in the consecutive WLD 0x36 block around the skeleton's first mesh.
  Appending a named HE90 elsewhere does not register it. Preserve typed fragment
  references when inserting; see `tools/helmet_wld_layout.py` and
  `docs/releases/winged-helmet-display-20261004/`. All head variants also use the
  first mesh's material palette: extend that shared palette without renumbering
  its existing slots. A private HE90 palette leaves new surfaces invisible;
  see `docs/releases/winged-helmet-materials-20261004/`.

- **Spell selection caches levels**: the RoF2 menu stores labels and ordering
  before multiclass metadata may arrive. Accepted class snapshots invalidate it;
  rebuild on a safe native cast-window frame after identity/profile checks.
  A correct gem level does not prove the menu cache is current. Native trace,
  regression and exact QA: `docs/releases/spell-menu-20261002.md`.

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
- **All allowed AAs and ranks are available at character level 1.** Players choose where and when to spend points. Never add character-level AA gates; balance with the explicit expansion pool, release rank ceilings, costs and prerequisites. The owner reaffirmed this invariant on October 13, 2026 after rejecting the early-level gating candidate.
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

**October 11 food/drink exception:** the owner explicitly approved "Merge to main
and server" for the removal of hunger/thirst requirements, penalties and warnings.
This authorizes main promotion and OVH rollout before manual acceptance. Preserve
the outstanding client checks in `docs/qa/2026-10-11-food-drink-removal.md`.

`feature/<name>` → `dev` → `test` → `main`

**October 9 advanced-loot controls exception:** the owner explicitly requested
"Deploy to main and server" for direct Always/Never row controls and empty-queue
auto-close. This authorizes main promotion and signed client publication before
owner gameplay QA. Retain the pending native checks and paired DLL/XML rollback
in `docs/releases/advanced-loot/ROW-CONTROLS.md`; no game-runtime restart is needed.

**October 9 Throw Stone exception:** the owner explicitly requested "Push to main
and server." This authorizes main promotion and OVH deployment of Throw Stone's
Spell Damage scaling before in-game acceptance. Preserve the remaining QA in
`docs/releases/throw-stone-20261009.md`; this is not a general branch-policy change.

**October 4 helmet exception:** the owner explicitly requested "I want to do
this on the server. Push to main and the server." This authorizes direct main
promotion and hosted deployment of the winged Paladin helmet, including Camil's
head appearance and signed client archives, before native gameplay QA. Retain
the open visual/equip checks in `docs/helmets/winged-paladin.md`; do not treat
publication as successful native acceptance or a permanent branch-policy change.

- **feature branch**: temporary, one system/feature each.
- **dev**: Codex merges here and runs automated testing against the codebase.
- **test**: pause. The user runs manual in-game QA. Every promotion to `test` MUST include an explicit spike-out of exactly what to QA in game (steps, NPCs, zones, expected results).
- **main**: only after user sign-off on the manual QA.

Codex is free to commit, open PRs, and merge autonomously **up to `test`** when tests pass. `test` → `main` requires user sign-off.

**October 16 dungeon release exception:** the owner explicitly requested main
promotion and server deployment with matching binaries and item cache for
in-game testing. This authorizes the Raid/Grind release and controlled restart
before gameplay acceptance. Preserve the pending fourteen-mode and dragon
balance checks in `docs/dungeons/QA.md`; see `docs/dungeons/deployment/` for the
production-content rehearsal, access boundary and receipt-preserving recovery.

**October 13 tradeskill exception:** the owner explicitly requested "Push to main
and server for live QA." This authorizes PR #200's stacked tradeskills/Craft All
release and its paired native/client publication before manual acceptance.
Retain pending in-game checks in `docs/tradeskills/README.md`; this is specific
to this release and does not change the standing promotion policy.

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

### Reusable item upgrades

The Reforging Box uses native inventory transactions, not NPC ingredient
hand-ins: three eligible Normal/Base copies yield Polished; four Polished or Exalted copies yield one next-tier item. Box 900620 is
supplied by tunnel NPC 999820. Higher-tier `#zoneforge` costs also become four;
base remains three. Installation starts disabled and needs matching zone/item
cache/quest deployment. Evidence and required manual QA:
`docs/releases/item-upgrades-20261012/`. Owner-approved PR #171 and live deployment
completed October 12; revision 2026101201 is enabled. Real client acceptance is
pending. Recovery must preserve player/receipt state and hold the gateway closed
if unexplained data drift is detected before player access resumes.

**Always update `CHANGES.md`** when making significant changes — C++ patches, database schema changes, quest script additions, or SQL setup file corrections. Include: what changed, why, any gotchas. This is the primary audit trail for this repo since many changes touch the live database or compiled binaries and aren't fully captured by git diffs alone.

Format: date header, area, description. Most recent entry at the top.

## Current documentation and player website

Classic zone hunt/forge is live for owner QA; see `docs/releases/zone-loot-20261009/PRODUCTION.md`.
`tools/zone_hunt.py` generates guarded item/socket SQL from an explicit production
content capture. Do not attach its rewards to global loot tables: native death
rolls are exactly 0.5% per family and intentionally bypass GlobalLootMultiplier.
Keep restored corpses, owned NPCs and non-native clones excluded. Type-22 cap
credit is limited to six armor locations; preserve nonplayer cap behavior.
Forging uses the advanced-loot inventory serializer, exact persisted preimages,
single-use choices and commit-uncertainty quarantine. Universal trading remains
in force; new rewards cannot be sold to merchants. Acquisition rollback retains
owned definitions, sockets and receipts. Access-check zones remain disabled until
their separate source/access QA passes. Preserve production hardening by building
the scoped patch over the fingerprinted live source; a successful market/world
contract check does not verify login authentication hardening. Run the private
crypto self-test before activation.

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

RoF2's pet-arrival caller relies on ECX surviving the availability predicate,
even though ordinary C++ calling conventions permit clobbering it. Keep the
register-preserving bridge and compiled register/stack tests around
`PetAvailableHook`; bool-result tests alone missed a summon crash. Initial fault
and later crash-reporter recursion must be distinguished. Evidence and QA:
`docs/ops/darthy-pet-crash-20261011.md`.

Use `docs/status.md` for current deployment and issue status; `docs/README.md`
indexes operational guides and dated evidence. Preserve historical report scope.
The five-file `index.html`/`site-assets/` guide publishes privately on the existing
approved-IP `play.nightcapgame.org` host using `tools/player_site_package.py` and
`deploy/production/player-site-deploy.py`; see `docs/ops/player-website.md`. Preserve
private caching and closed apex/www routes. Website publication does not promote
gameplay to main or replace owner in-game QA.

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

### RoF2 buff reconnect state

Buff icons do not establish active native effects. OP_Buff mode 2 updates an
existing matching effect; mode 3 installs a slot. Restore saved player state only
after client-ready, without recasting or refreshing duration/charges. Keep the
permanent-buff sentinel policy. Exact-client regression and unresolved login QA:
`docs/releases/blessing-relogin-20261002/README.md`.

RoF2 native player profile/OP_Buff duration differs from icon countdowns: preserve
the server policy -1000 for effects, since -1 expires on a tick unless the spell
has duration formula 50. Icons still use -1. Test native ticking, not only formula
arithmetic or slot restoration. Evidence: `docs/releases/blessing-lifetime-20261004/README.md`.

### Official public wiki

`wiki/` owns the separate public guide at `wiki.nightcapgame.org`. Maintain reviewed
article JSON and the public reward projection, then generate/package only `dist/`.
Never expose raw exports, source ledgers, operations files or private game downloads.
Preserve the current credential-based player-access policy and apex/www 404 routes. Wiki and player-site
publishers must share `deploy/production/website-history/.lock`; preserve the
bind-mounted Nginx config inode, relative release symlinks and rollback preimages.
Public HTTPS is active. `wiki/update.py` performs guarded content-only updates
with an atomic relative pointer, exact config/previous-release checks and rehearsed
rollback; it does not reload Nginx or restart services. Run its POSIX tests on Linux.
Keep equipment variants grouped in `items.html`; do not reintroduce flat item dumps
into category navigation. See `docs/ops/nightcap-wiki.md` for current release and
recovery. Website deployment does not promote gameplay.


### Wiki maintenance with every change

Every Nightcap feature, fix, tuning/content change, deployment and accepted player
correction requires a wiki impact review before completion. Update affected guides,
Features (major departures from Classic), home summaries, commands, generated
item/zone pages, catalog values, release labels and Recent changes together. If
there is no player-facing impact, record that assessment in the change evidence.
Do not claim local edits are published; verify the authorized public release.

Use the current wiki checkout and `wiki/README.md`; run `wiki/check_refresh.py`
against the actual current source ref, including worktree changes when applicable.
Source drift means review required, not permission to blindly advance the ledger.
Check dated deployment/QA and outside-Git operations too. Preserve candidate labels,
private operational data and the installed Nightcap skill's wiki knowledge.
This is part of each change, not a scheduled job or gameplay deployment authority.
