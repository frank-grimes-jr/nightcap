# Quests, tunnel services and travel

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

## Every Classic dungeon and unique rewards — October22 deployed for live testing

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

Source 0d61d9b47322 in E:/EQ_Local_Dev/_worktrees/classic-dungeon-options covers21
Classic combat dungeon zones including Fear/Hate/Sky,147 objectives and42 journals.
Originalseven indices/objectives/tasks and revision2026101601 remain stable.
All21 finals now have three exclusive designs. Added14 contribute84 definitions;
all414 rewards are MAGIC. Existing330 change only220 MAGIC flags; old names,
stats, IDs, runs, earned rewards and recorded drops remain. Current native content
is retained, including the Hole; private Classic CT remains the prior restoration.

The screenshot mismatch was stale October16 item predicates after October18's
retune:39 schema checks passed and41 old item batches failed in the read-only
capture. Current guards derive from the reviewed compiler, not live acceptance
hashes. The combined release uses the additive dungeon SQL followed by
20261022_classic_dungeon_rewards.sql; never rerun old October16 installation.

Native eq.get_dungeon_run_id() and paired nightcap_dungeons Lua module isolate
plane quest state by permanent UUID. ManagedFear cannot toggle public conditions.
Sky uses five canonical private bosses plus seven protected persistent Sirran
services; four bosses use8h Grind timers and princess4h. All eight key routes
retain required tokens. Managed saved-state skips living dynamic NPCs, so do not
rely on temporary quest-spawned services. Bazzt z806 is ground-probed. Public and
legacy quest behavior remains. Every-zone gameplay and solo balance remain open.

Pair matching world,zone,shared_memory, regenerated target item cache and the
11 plane quest scripts/Lua module. common/shareddb consumes the expanded reward
range; ItemData/rule ABI is unchanged. Existing spell IDs need no new client
assets: preserve the current signed client and never downgrade parallel releases.
Production child exit restarts the runtime: use full maintenance, not zone kill.
After access, preserve a compatible21-zone/414-item runtime and all earned state.

Current source/evidence: tools/classic_dungeon_rewards.py, classic_reward_migration.py,
dungeon_catalog.py, dungeon_refresh_contract.py; common/dungeon_policy/contract;
docs/dungeons/classic-rewards-20261022/{README.md,REWARDS.md,QA.md,verification.json,
rehearsal.json,build-manifest.json,cache-verification.json,review.md}. Prior
classic-expansion-20261022 records retain their pre-reward330-item scope.
Native world/zone/shared_memory build and baseline reproduction pass;39schema/
497content SQL checks and414 actual cache rows/888 negative cases pass. Broader
77-test suite:74pass,2optionalDBskips,1 unchanged generator drift reproduced at
HEAD. Historical installation/package/verification and expansion-only rehearsal
entrypoints are frozen; use combined reward rehearsal. Main/live activation and wiki publication are verified; owner acceptance remains open.

## Routing and APIs

- Tracked quests: `server-mods/quests/`; tracked plugins: `server-mods/plugins/`. Local plugins actually install to `akk-stack/server/plugins/`, not `quests/plugins/`. Production can configure additional paths; inspect the real loader/path configuration.
- Lua wins over Perl for `global_player` in this build. Don't add an event to the shadowed Perl file and assume it executes. ID-based global NPC scripts can avoid that ambiguity.
- Perl bindings define exported names. Use `Database->new()`, `prepare`, `execute`, `fetch_hashref`, `rows_affected`; there is no injected `$DB`, DBI `do`, or `fetchrow_hashref`. Client binding is `CharacterID()`, not C++ `GetCharacterID()`. Confirm exact methods with the existing `lookup_quest_api` or targeted `zone/perl_*.cpp`; declarations alone aren't evidence.

## Commonlands XP blessing - retired October 21
Owner-authorized main PR268 and production release retire both ecommons and
legacy poknowledge Magus_Goldwind.pl payment/grant paths. Hail/empower direct
players to Matron Restora's free ordinary buffs. Matron scripts remain exact.
No replacement earned boost is released.

The old explicit2400-tick spell21030 grant could inherit ordinary buff permanence.
The zone now classifies PercentXPIncrease effects as temporary: positive timers
are preserved; stale finite-duration -1000/-1 copies receive the minimum native
countdown on load (two unsuspended processing callbacks to fade). Native
permanent/aura formulas remain intact. Offline character rows are not deleted.
Do not infer every existing boost came from Goldwind or clear unrelated buffs.

Source/tests/evidence: C:/Users/verre/.codex/worktrees/aa-point-cost-40000/EQ_Local_Dev, docs/releases/aa-pacing-million-20261021/.
Zone5dd5a655 plus the paired quest scripts and1m AA rule are deployed through a
supported full-runtime restart. Client/world/shared caches unchanged; earned
state preserved. Native21 duration groups,6 quest interactions and23 operation
tests pass; public guides verify. Owner gameplay acceptance remains open.

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

## Waypoint crystal - October22 deployed for live QA

The owner selected a glowing crystal with the existing `a waypoint` label and
authorized "Merge to main and server", then confirmed full client exit. Main
PR280/f293626, signed game2026102202 and the paired quest are deployed. Source
and final release evidence10f162c are in
C:/Users/verre/.codex/worktrees/waypoint-markers/EQ_Local_Dev,
docs/ops/waypoint-crystal-20261022/ and deployment/. Native acceptance remains open.

Quest999240 uses Crystal Shard race425, neutral gender2, size6 and portal nimbus178.
Signals20261011/20261022 refresh idempotently. Positions,25-unit horizontal and
30-unit vertical discovery, earned progress, recall and Explorer title100 remain.
No new NPC, SQL, native build, repop or saved-state edit. The former deployed
race127 portal-only presentation is historical. Destination/progress tables are
nightcap_waypoints/nightcap_character_waypoints; old72 count is not permanent.

Matching proxy/catalog0.11.1 and both complete import lists pluscrs.eqg are
mandatory; client.md owns the contract. Publication verified all140 signed files
before quest activation. Fully close EQ and use normal launcher Play. The exact
committed UTF-8/LF quest hash is
4b15350087dfd4153ea2ef98e418da9696b0c7efe99cdd8fe62cb96483f764a2;
the Windows CRLF candidate hash981a7c3c is not the Linux deployment hash.

The operator takes deployment/GM locks, preserves the original world-lock intent,
holds admissions with world lock plus gateway pause, then rechecks zero clients.
World lock alone permits GM bypass. Supported quest reload without timer reset
produced12 aggregate acknowledgments before signal20261022; logs do not attribute
each worker or prove visible processing. Host/container hashes and absence of
quest errors verify. Admissions restored; world/all12 zones, five services and
Keeper quest remain unchanged. Do not kill a production zone process.

Recovery: deployment/activate.py rollback restores exact retained old quest,
reloads, then signals999240 with20261011. That verified old handler actively
restores race127/gender0/size6 and portal178; no temporary script is needed.
Bytes alone do not undo an illusion. Uncertain post-write failure holds admissions;
validated owned partials and exact matching rollback retries are recoverable.
Never overwrite foreign files, replay player snapshots or lower client counters.
Client rollback keeps a complete matching pair at a fresh higher signed counter.

Quest19/Keeper52 and Python27 checks pass. Deployment has11 Linux publisher and
13 Linux quest tests, including interrupted install and rollback retry; independent
review resolved both recovery findings before activation. Source/tests include
server-mods/quests/global/999240.pl, tools/tests/waypoint_visuals.t and deployment/
{quest_remote.py,test_quest.py,quest-apply.json}. Race425's additive material still
needs actual particles-off/both-mode visibility. Exact Befallen/Unrest/Crushbone
scale, label, late-join, attunement/recall and separate-Keeper QA remains open.

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

Instance Keepers use a small floating eye (race108, gender2, size3), distinct
from waypoint999240's crystal plus portal nimbus. October13 visual
acceptance is historical; the October22 report remains open for visible QA.

**All-dungeon overlap correction deployed October22 through main PR274/7792171.**
The initial Befallen-only PR272 was extended after the owner asked about the
remaining zones. Fresh all-seven audit found five exact Keeper/waypoint overlaps:
Befallen, Unrest, Najena, Permafrost and Nagafen's Lair. The shared quest uses
exact NPC-ID/zone guards and absolute poses on spawn/signals20261014/20261022:

| Zone / NPC | XYZ / heading |
|---|---|
| befallen999227 |35,-67,3.1 /256 (retained prior correction)|
| unrest999228 |67,-38,3.1 /384|
| najena999230 |858,-61,4.1 /256|
| permafrost999232 |46,-121,2.1 /128|
| soldungb999233 |-248,-424,-108 /384|

High Keep999229 at88,-16,4 and Cazic-Thule999231 at-74,71,4 already have distant
separate waypoints; neither placement changes. This does not prove their visible
model works. All seven have valid ground, normal targetability/bodytype1/model0,
zero grid/roam and the same shared quest with no zone/ID override. Available
saved service poses have no buffs. Client-rendering causality is not established.

All seven production/local map hashes match. Four final destination/approach
pairs pass40 ground/headroom samples and8 clear rays; nearby doors/spawns/zone
metadata checked. SolB retains original z=-108 beneath its12-unit ceiling; the
probe's z+8 cast at-107.9 would start just above that ceiling. Najena moves away
from the existing skeleton. Tests:52 Keeper,16 waypoint,10 recovery assertions,
8 operator groups and independent review pass. Doubles do not execute the native
saved-state loader; GMMove guard saving and loader order were inspected separately.

Installed quest SHA903086e695615f3c8f3f3a05ca1bf3bd96c1d8a6cff4700fc7ad6858215580b1
matches committed UTF-8/LF bytes. Supported quest reload without timer reset
produced12 aggregate acknowledgments before signaling the four added NPC types.
World/all12 zone lifetimes, five service identities and waypoint hash are unchanged.
Shared logs do not identify individual workers; signal sent does not prove visible
NPC processing. Unbooted zones apply the policy on their next normal load. No
restart, DB rewrite, client/cache/binary change, dungeon action or progress reset.

Use docs/ops/dungeon-keeper-visibility-20261022/{run.py,remote.py} and its retained
backup/recovery helper for current activation/recovery. The inverse restores only
the four new poses, retaining Befallen, and must remain for dormant saved poses.
Never restore old player/loot/dungeon snapshots or only the old quest bytes.
The superseded Befallen operator has a historical cp1252 comment-only payload;
do not apply its preimage/recovery guards to this successor. New operators must
preserve UTF-8 bytes. Saved guard positions are absolute and tolerate0.25 units.

Source, audit, exact all-seven /loc QA and receipts:
`C:/Users/verre/.codex/worktrees/befallen-keeper-visibility/EQ_Local_Dev`,
`docs/ops/dungeon-keeper-visibility-20261022/`,
`server-mods/quests/global/Instance_Keeper.pl`, `tools/tests/instance_keeper_visuals.t`.
Owner answered "Not tested yet" for Befallen; no zone's current visibility is
accepted. Wiki20261022-dungeon-keepers-v1 publishes all-seven locations and the
/target Instance_Keeper fallback with explicit Live testing labels.

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
evidence are separate from deployment. On October 16, Palwar confirmed Befallen Keeper selection, Raid entry and a named
kill, but reported blank task objectives. Saved task/ledger credit matched.
The journal repair is deployed after the owner requested "Restart now". The
owner then replied "Confirmed" after the Befallen journal retest instructions,
accepting the reported display fix. This does not individually attest every
retest step; full-clear rewards and broader gameplay QA remain open. The exact
reply and scope are in docs/dungeons/journal-repair/verification.json. `/target Instance_Keeper`
selects the eye when the colocated waypoint obscures it; waypoints do not hail.

Journal definitions 9700–9713 are projected natively after task loading into Kill
display rows controlled only by METHODQUEST. Every boss is step0 and the required,
never-credited sentinel is step1: all-zero steps invoke native sequential mode
and hide later objectives. Entry/Status print all boss names and personal credit;
chat distinguishes a boss stage from full completion. The ledger projects earned
full clears directly into Completed history without task events/native rewards.
Reconnect preserves matching acceptedtime; failed history writes retry even after
reset/expiry. Older completion cannot remove a newer or ambiguous same-second run.

Source: zone/dungeon_service.cpp::ConfigureJournalTask, Journal, JournalHistory;
task_manager.cpp::LoadTasks; task_client_state.cpp::RecordCompletedTaskFromLedger.
Four compiled journal regressions include the pinned retained GetActiveElements,
out-of-order bosses, reconnect/abandonment and history failures; all15 dungeon
tests and27 release controls pass. Three translation units link against objects
which reproduce the exact deployed baseline. Source/build/deployment evidence
and exact in-game retest: docs/dungeons/journal-repair/. Native zone only; matching
world/shared_memory and the unchanged regenerated production item cache are kept.
No migration, quest or client asset change; whole-runtime restart is required.
Do not reset a live run or replay player snapshots to repair its journal.

Earlier old-runtime restarts are recorded separately from the repaired runtime.
All14-mode gameplay, CT paths/doors and level50 Vox/Nagafen balance remain open.
Wiki release20261016-dungeon-journal-v1 is published with all52 required names,
stage/full-clear/fallback guidance and465 verified public hashes; publication does
not establish native rendering acceptance. The main promotion and restart were
explicitly authorized for this follow-up, not future unrelated releases.

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

Adventure Journal / Epic 0.5 remains a **candidate**, not recorded production: native Tasks own progression; `nightcap_epic05_state` owns attunement/cooldown only. Pair native `Epic05Contract()`, plugins, item 900501, tasks 9500â€“9507 and spells 42800â€“42805; gate starts disabled. Explore=5 credits movement; Touch=11 is a dynamic-zone switch. `docs/adventure-journal/README.md` is the implementation route, not permission to enable it.
