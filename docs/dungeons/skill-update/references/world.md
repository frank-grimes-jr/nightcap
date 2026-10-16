# Quests, tunnel services and travel

Audited 2026-10-12. Placement history has several revisions; use current feature source and exact runbook, not a convenient old SQL file.

## Routing and APIs

- Tracked quests: `server-mods/quests/`; tracked plugins: `server-mods/plugins/`. Local plugins actually install to `akk-stack/server/plugins/`, not `quests/plugins/`. Production can configure additional paths; inspect the real loader/path configuration.
- Lua wins over Perl for `global_player` in this build. Don't add an event to the shadowed Perl file and assume it executes. ID-based global NPC scripts can avoid that ambiguity.
- Perl bindings define exported names. Use `Database->new()`, `prepare`, `execute`, `fetch_hashref`, `rows_affected`; there is no injected `$DB`, DBI `do`, or `fetchrow_hashref`. Client binding is `CharacterID()`, not C++ `GetCharacterID()`. Confirm exact methods with the existing `lookup_quest_api` or targeted `zone/perl_*.cpp`; declarations alone aren't evidence.

## Service map

| Feature | Where to start | Critical distinction |
|---|---|---|
| Multiclass/Chronicler | `plugins/multiclass.pl`, Chronicler quests; class release is native atomic API | Canonical table, not NPC qglobals; deployed EC hub supersedes PoK-only assumptions |
| City travel / Merrin | `quests/ecommons/999810.pl`, `plugins/tunnel_travel.pl`, `tunnel_travel_data.pl`, `tools/tunnel_travel.py` | Ten city routes use canonical IDs/landings; guard EC zone 22, instance 0, NPC 999810, 50-unit 3D distance, player state and 5-second repeat guard |
| Druid rings / Khalure | Find exact ID/name quest in `quests/ecommons/` and current tunnel release | Distinct from Merrin and wizard travel; no response requires checking actual binding/API/quest error, not guessing a new destination |
| Wizard spires / Khaleid | `plugins/tunnel_spires.pl`, `tunnel_spire_data.pl`, class-courts release | Eight normal Classic routes; no planes/future expansions |
| Waypoint discovery | `quests/global/999240.pl` | Marker owns proximity discovery in all catalog zones; don't move it to shadowed global_player.pl |
| Personal dungeon instances | `zone/dungeon_service.cpp`, `quests/global/Instance_Keeper.pl`, `docs/dungeons/` | Raid/Grind is deployed for live QA; existing legacy runs retain version-zero content and twelve-hour lifetime |
| Reforging | `quests/ecommons/999820.pl` | Veyra gives a reusable container; native inventory handler performs atomic combines |

Waypoint marker 999240 uses invisible actor race 127 and WizardPortal nimbus 178; live-refresh signal 20261011 is idempotent. It retains nameplate/proximity/discovery and late-joiner effects. Progress is in `nightcap_character_waypoints`; destinations in `nightcap_waypoints`; Explorer title is 100. The old 72 count is a dated catalog count, not a permanent completion constant.

October 13 **Unrest entrance relocation deployed**, owner-approved PR #198:
the eye is Keeper 999228 (spawn2 3266037). Marker 999240 (spawn2 3266123)
and recall were 921 units away at DB XYZ `118,881,3.75`; both now use entrance
`52,-38,3` (`/loc -38,52,3`) beside the unchanged eye. Installed portal/discovery
and Keeper quests were correct and remain unchanged. Matching non-corpse,
non-metadata instance-zero saved marker poses moved, including dormant ID zero.
Existing saved private-instance positions, discoveries and nonposition state
are preserved; new instances inherit the base spawn. The placement generator
is `tools/unrest_waypoint.py`; it reuses full-row transaction/engine/trigger
guards from `tools/content_patch.py`. The adapted operator retains deployment/GM
locks, full stopped backup, isolated restore with FLOAT precision companion,
exact forward/inverse rehearsal and activity-preserving recovery. Never restore
old player or full NPC state for this position-only rollback.

All 68 local placement/visual/SQL/generator/recovery checks and independent
reviews pass. Live restore/rehearsal, 64 preservation fingerprints, unchanged
8,140 quest/plugin files and current runtime/client pairing verify. All 12
zone workers are healthy and access is open after a controlled restart. Quest
reload alone cannot relocate an existing marker. No native or client update.
Owner portal/discovery/recall gameplay acceptance remains **open**, separately
from verified deployment. Source, tests, public-safe receipt and exact QA:
`docs/ops/unrest-waypoint-20261013/`, `tools/tests/test_unrest_waypoint.py` and
`tools/tests/test_unrest_waypoint_content.py` in
`C:/Users/verre/Documents/Codex/2026-10-13/go/work/unrest-waypoint`.

The other human at Befallen/Permafrost was an overlapping **Instance Keeper**, not a duplicate marker. October 12 keeper quest adds a small floating-eye appearance (race 108, gender 2, size 3), retaining its interaction; refresh signal 20261014 covers existing Keepers. Both repairs use quest reload plus scoped signals, with no client update or native restart. Permafrost portal visibility/function was owner-confirmed October 12. On October 13 the owner confirmed "resolved" after the Keeper follow-up, closing the reported visual issue; the reply does not individually attest every zone or optional QA case. The 16 waypoint and 13 Keeper regression assertions are in `tools/tests/waypoint_visuals.t` and `tools/tests/instance_keeper_visuals.t`. `docs/ops/waypoint-visuals-20261011/README.md`, `docs/ops/keeper-visuals-20261012/README.md`. Crushbone marker, recall and matching saved state moved together to entrance `/loc -644,158,4`; `/loc` display ordering differs from DB x/y. See `docs/ops/crushbone-waypoint-20261009/README.md`.

## Raid and Grind dungeons deployed for live QA

October 16 deployed release: `docs/dungeons/README.md` and `QA.md` in the dungeon-modes
checkout own current evidence. Native `zone/dungeon_service.cpp` validates Keeper
operations and owns twelve-hour, six-participant, fixed-mode runs for all seven
dungeons. UUID + native allocation start + `nc-dungeon:<UUID>` identifies a run;
the 47-byte marker must fit native notes. Do not key progress on recyclable IDs.
Grind keeps native stats/timers. Raid has 135% HP/115% outgoing damage, permanent
spawn deaths and a final boss unlocked by all minibosses. Player-owned pets are
excluded from scaling. Explicit catalog revision 2026101601 has 52 objectives;
Permafrost excludes three audited later/nonqualifying native identities.

Encounter credit uses connected, loaded, enrolled party/owned-pet attribution
within a 200-unit 3D sphere. No retrospective credit; Grind respawns permit
catch-up. Tasks display the ledger; abandonment never resets eligibility.
Only the creator can confirm reset, with no pending/inside participants or
recoverable player corpses. Completed connections acknowledge entry/exit.
Earned claims and permanent completion counts survive reset and expiry.

Both-mode finalized corpse envelopes, Raid deaths, Grind timers and credit commit
before death publication. UUID checkpoints work independently of global state
saving; stale living checkpoints cannot override a newer death. Existing native
item/currency receipts filter replay. Uncertain persistence suspends the zone;
never clear receipts or restore older player data. Existing unmanaged runs retain
legacy behavior. SQL/content/cache drift and split game/content DB configuration
refuse activation/new runs/managed boot. Classic CT's pinned private 188-point,
29-NPC restoration does not change public spawn/door definitions.

Ship matching zone/world/shared_memory, regenerated target-content cache, SQL and
Keeper quest. Production startup regenerated its own cache; the older local-test
package cache must not replace it. Production preserved all 309,410 existing
item records and added exactly 330. See `docs/dungeons/deployment/` for native
hashes, cache pairing, recovery and the separately recorded preflight DB restart.
No client assets; a quest reload cannot install native hooks/cache. Automated
native policy/credit/spawn, receipt adapters, SQL/fault/concurrency and build/cache
evidence are separate from deployment. Fourteen-mode gameplay, CT path/door QA,
level-50 Vox/Nagafen balance and owner acceptance remain open. Source flow ran
through dev/test to owner-authorized main and production deployment. The gateway
is open. Website publication remains separate; owner gameplay is not accepted.

## Travel failure diagnosis and current QA

October 12 audit: owner-confirmed Merrin West Freeport and Khalure West Commonlands/North Karana clicks work. Before the asset repair, Toxxulia was reproducibly silent, but current game-container stdout recorded the correct ZonePC request for zone 38; retained files under `data/server/logs` missed the current events. Prefer `docker logs` for fresh correlation. Empty passive UDP traces did not establish packet loss. Correct saylink strings and isolated Perl tests do not prove native zoning.

The affected `E:/Nightcap` client lacked `tox.s3d`, `tox_obj.s3d`, `misty.s3d`, and `misty_obj.s3d`. All four were restored locally from byte-identical retained QA clients after complete PFS/WLD validation and verified by SHA-256. After repair all 34 terrain/object archives for the 17 offered zones passed decompression and expected-WLD checks. Of 17 distinct offered zones, these two lacked terrain. Supported eqgame.exe hash matched. No quest, database, binary or service was changed. The owner confirmed on October 12 that Khalure's Toxxulia click now teleports after repair ("Yes, now it ports me"). This closes that route's silent-click failure. Misty, Toxxulia from the other NPCs, detailed terrain/landing/return-path QA, the other untested routes, and signed fleet delivery remain open. Close/relaunch EQ if it cached missing archives; do not substitute revamped zone IDs. Four `.s3d` paths already fit the signed game-asset policy; publication needs the normal complete inventory/higher release flow and environment-specific authority.

Current evidence: `docs/ops/travel-client-audit-20261012/{README.md,asset-audit.json,install-receipt.json,archive-checks.json}` in `C:/Users/verre/Documents/Codex/2026-10-12/g/work/travel-client-audit` (based on `4e3acd83019a915b04a9ec1f222c3bc2543d0bfe`). Archive validator: `tools/classic_model_archives.py::read_pfs`. Full 26-route production snapshot and 142 isolated checks are retained in the originating chat's `outputs/`. This records local repair and partial owner travel acceptance, not all-route QA or hosted publication.

## Commonlands banker

October 16 owner-requested Mira Coinwell deployed on OVH: native banker class 40,
NPC/spawn/group 999821, East Commonlands version 0, `/loc -1584,-144,3.75`, heading
128, beside Bartholomew/buff services. Neutral stationary human woman, copied from
the current Tessa service template with merchant ID cleared; no quest or client
asset required. Nearest static object is 17.09 units away, walking route 14.14;
10 ground/headroom samples and the approach ray pass. Owner banking/visual QA is
pending. Source, guarded SQL rehearsal, rollback and deployed health evidence:
`E:/EQ_Local_Dev/docs/ops/commonlands-services-20261016/`.

The same controlled runtime restart also regenerated the paired Leather Padding
price cache, retaining all native binaries. No saved states were deleted:
`Zone::LoadZoneState` in `akk-stack/code/zone/zone_save_state.cpp` explicitly loads
new spawn2 records missing from saved state. Do not broadly clear state or repop
to add this banker. After she has run, rollback must inspect/remove only her
exact non-corpse, non-metadata base-instance saved rows as well as permanent
records; preserve unrelated state and all subsequent bank/player activity.

## Layout/content work

EC is the active tunnel service hub with trainers, merchants, suppliers, residents, workshop and travel. October 2 compact layout preserves 119 actors; dated PoK layout or September lineups aren't current positions. Read `docs/releases/tunnel-compact-20261002/README.md` and current status. Appearance needs race+gender+texture+helm/material compatibility in that zone; race alone can fall back to a human. NPC merchant class is 41; merchant_id alone isn't sufficient. NPC display equipment need not be loot.

October 13 relaxed workshop **deployed for owner visual QA**, PRs #194/#195:
`tools/tunnel_cozy_layout.py` and `tools/tunnel_cozy.py` relocate 25 NPCs and six
stations, adding three native static ornaments. The Chronicler, Bartholomew and
Tessa join the unchanged buffers; the 21 dedicated suppliers form loose crafting
groups, with alchemy in the former Chronicler space. The current scene includes
Artisan Veyra; the old 119-actor roster is not a completeness check. Review
`docs/releases/tunnel-cozy-20261013/{README.md,production.json}`, roster and diagram
in `C:/Users/verre/.codex/worktrees/cozy-tradeskill-hub/EQ_Local_Dev`.
Nine layout tests, thirteen operator tests, eleven local SQL checks, 945 native
ground samples, 67 rays and the fresh full-backup forward/inverse rehearsal pass.
Exact production poses, preserved data/runtime/public fingerprints and all 12
zones verify. Runtime and client files remain unchanged; no client update is
needed. The controlled full runtime restart refreshed NPCs/stations/doors.
Owner appearance, cozy feel and interaction acceptance remain open; follow the
six exact in-game checks in the release README.

Check moved obstacles against **unchanged neighbors' front approaches** too:
Veyra's approach caught an initially missed obstruction. `probe_tunnel_cozy.py`
and its unit regression cover this. Donor ornament `opentype=58` alone does not
disable dynamic-zone/adventure switches: native `doors.cpp` handles those first.
The generator rejects interactive donor flags and guards global DB IDs and
cross-version door IDs. Saved NPC ID zero can represent an owned dormant spawn;
invalidate only with exact spawn/group identity, retaining corpses, metadata,
other instances and fresh unrelated states. Never restore stale caches on rollback.

Use actual map ground/headroom/approach checks, exact DB preimages, quest bindings and in-game visual checks. Saved non-corpse instance-zero NPC state can override fresh spawns. Scope invalidation; preserve corpses, other instances, metadata and unrelated actors. Prefer reviewed generators/rehearsals (`tools/tunnel_*.py`, `tools/tests/test_tunnel_travel*.py`, `tunnel_*_quests.t`) rather than hand-authoring broad SQL.

PoK stock derives from `docs/pok/hub-stock-audit.json` original class levels and catalog policy, not widened spell columns. Use `tools/pok_hub*.py` and `tools/pok-hub-era.ps1` only from a checkout where present and after reading its release procedure. Current GM restock has guarded canonical SQL; don't revive old unguarded refresh logic.

Adventure Journal / Epic 0.5 remains a **candidate**, not recorded production: native Tasks own progression; `nightcap_epic05_state` owns attunement/cooldown only. Pair native `Epic05Contract()`, plugins, item 900501, tasks 9500–9507 and spells 42800–42805; gate starts disabled. Explore=5 credits movement; Touch=11 is a dynamic-zone switch. `docs/adventure-journal/README.md` is the implementation route, not permission to enable it.
