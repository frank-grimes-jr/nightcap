# Current Nightcap status

Updated October 2, 2026. This is the current status index; dated studies and
QA reports preserve their original evidence and are not live-state promises.

## Resident campfire correction deployed for visual QA

PR 115 is merged to main and the server update is complete. Six residents form a
compact circle around a native campfire at /loc -1707, -274. Glorphyndel is a
High Elf in the requested Valorium with his sword and shield. Nalin keeps social
facing without idle emotes. Automated deployment checks passed; no client patch
is needed. The intermittent sword pose and rendered fire/armor still need
in-game inspection. [Exact visual QA](releases/tunnel-campfire-20261002/README.md).

## Spell-selection menu cache correction deployed for owner QA

Signed release **2026100202**, proxy **0.7.4-dev**, is live after PR 116 merged to
main. It refreshes native menu labels and ordering after class snapshots, fixing
cached 255 levels while preserving canonical scroll inspection. All 70 patch
sites, native regressions, runtime/launcher/loot suites, 46 hosted files and
existing-updater installation pass. The other 44 assets and all five production
services are preserved. Close EverQuest and click Play to update; check that
Pet > Sum: Water shows **02 - Elementalkin: Water** before memorization and after
zoning. [Evidence and exact owner QA](releases/spell-menu-20261002.md).

## Advanced loot interaction repair deployed for owner QA

Signed release **2026100201**, proxy **0.7.3-dev**, introduced this repair
after PR 113 merged to main; current **2026100202** retains it. It replaces the
crowded loot screen with compact panels, keeps navigation usable during requests, adds timeout/retry
feedback and prevents stale selection from targeting another item. All 46 hosted
files and the signature verify. Exactly three files changed from 2026100104;
the pet repair, other 43 assets and all five running services are preserved.
Close EverQuest and click Play to update, then enter `/advloot`. Actual native
clicks, rendering and server acknowledgments remain open; the original button
failure has not been localized. [Exact QA and evidence](releases/advanced-loot/UI-REPAIR.md).

## Compact pet window repair deployed for owner QA

Signed production release **2026100104** corrects native buff-panel resize
anchors that covered the compact roster and commands. All 46 hosted files
verify; only the pet UI changed from 2026100103. Production services and other
assets are preserved. Close the game and click Play in the normal launcher to
apply it. Existing saved window sizes remain; resize down if needed. Rendered
acceptance remains open in the [repair report](releases/pet-window-layout-20261001.md).

## Character-selection crash repair deployed for owner QA

The [October 1 material repair](releases/character-select-crash-20261001/README.md)
fixes missing shared materials in seven imported classic models. The player's
crash dump identified a null material after login, before character selection.
Signed production release **2026100103**, proxy **0.7.2-dev**, introduced this
repair, retained in **2026100202** through the existing launcher: opening it and clicking **Play** applies the patch before
starting the game. No reinstall is needed. All 22 archives pass material,
geometry, animation and texture preservation checks; the independent review,
six focused regressions, full Go and native tests pass. All five production
services and the starter/desktop/guide are preserved. All 46 hosted files and
the signature verify; the existing updater installed 2026100103 into E:/Nightcap
with all INIs and original executables preserved. Actual character-screen
and world-entry acceptance remain open with exact steps in the incident report.

## Spell inspection correction deployed for owner QA

The [spell inspection audit and fix](releases/spell-inspection-20261001.md)
removes 18,990 unusable original-class entries across 7,636 scroll items. Both
native inspection paths and all canonical class levels pass automated checks.
Owner-approved PR 101 is on main. Signed production release **2026100102**,
proxy **0.7.1-dev**, introduced this fix on OVH with 67 patch sites. Current
release **2026100202** retains it with proxy **0.7.4-dev**.
The original spell-inspection release passed hosted checks for all 46 files,
signature verification and installation through the production controller. That
release changed only the DLL and patch catalog, preserving all five services and
other assets. Close the game and reopen the patcher to apply the current update.
Rendered owner acceptance remains open with exact merchant/inventory QA linked.

## High-impact Play incident repair deployed

The [October 1 startup repair](releases/launcher-play-20261001/README.md) fixes
PFS version-2 archives exceeding RoF2's 8 KiB block limit. Signed game release
**2026100101** introduced the repair, retained in current **2026100202**. That
repair replaced all 22 archives and their matching proxy, preserving all 14,858
extracted entries and the other 23 managed files. The material repair above
subsequently updated seven WLDs. Production services, desktop/starter
and guide are unchanged. Regression, native, Go and publisher checks pass;
all 46 hosted files and the existing production signature verify over HTTPS.
Visible Play and post-login model loading still require the exact linked QA;
computer-control access to Nightcap was denied after the isolated login-UI run.

## Social tunnel revision deployed for owner QA

[The revised gathering layout](releases/tunnel-social-20261001/README.md)
accounts for all 119 actors, names class merchants, restores the six missing
residents, groups crafting in one corner and places the Chronicler by Shady.
Geometry, guarded database recovery and silent resident behavior checks pass.
[Activated October 2](releases/tunnel-social-20261001/PRODUCTION.md) after a full
backup restore, 17 SQL checks, 59 preservation checks, 72 installed quest
assertions and four public handshakes. The native image is preserved. This
supersedes the September 30 placement; rendered owner acceptance remains open.

## Tunnel class courts baseline

[Eight class courts and Khaleid](releases/tunnel-class-courts/PRODUCTION.md) are
the September 30 baseline, with placements superseded by the social revision
above. Matching class/profession
uniforms, Roman supply pages, Khalure's Druid Rings subtitle and Khaleid's Classic
wizard travel are installed. Fresh backup restore, 19 SQL checks, 50 preservation
fingerprints, 26 installed-file quest assertions, 15 native hashes and four
public handshakes pass. Exact visual/interaction QA remains open.

## Advanced loot deployed for owner live QA

The [advanced-loot release](releases/advanced-loot/PRODUCTION.md) has a native
RoF2 window and server queue, saved filters, personal/shared controls, checked
item/coin transfers and saved-state receipt protection. Focused fixtures and
the disposable SQL rehearsal pass. The clean world/zone build and locally signed
QA package pass compilation, installation and actual RoF2 startup. Isolated
login/world/ecommons services boot successfully. Per the owner's explicit request,
PR 91 merged to main and the paired hardened production build is live on OVH.
Signed game release **2026093006** introduced this client content; the current
**2026100201** release retains the server contract and includes the client
interaction repair above through the usual starter.
Backup restore/migration rehearsal, 47 preservation checks, all 15 native process
hashes, application-account permissions, all 46 hosted client files/signature
and four public native handshakes passed. [Owner live QA](releases/advanced-loot/LIVE-QA.md)
remains open. The isolated port cutover was superseded and not performed.

## Classic models deployed

The [classic-model release](releases/classic-models-20260930/PRODUCTION.md)
adds a mandatory client policy, 22 isolated classic archives, original elemental
palettes and 98 remake mappings. Existing INI settings cannot silently opt in.
Signed game release **2026093004** introduced this policy, retained in the current
**2026100201** release through the existing patcher after
the owner's explicit main/server instruction. Native x86, archive integrity
and packaging checks pass. Rendering and owner acceptance remain open. Creatures with no old
counterpart retain their existing model, as the owner explicitly requested on
September 30. The policy choice is resolved; see the [coverage audit](releases/classic-models-20260930/scope-audit.md)
for the mapping scope and remaining visual acceptance.

## Enchanter animation commands deployed

Enchanter animations now accept standard pet commands without an AA unlock on
the live OVH server, including when Enchanter is a secondary class. The fresh
zone build, native command checks, backup restore, preservation and live process
checks passed. No client update is required. [Deployment and recovery evidence](releases/enchanter-animation-pet-commands-20260930/PRODUCTION.md);
[owner in-game QA](releases/enchanter-animation-pet-commands-20260930/QA.md) remains open.

## Combat and item repair candidate

[Monk fists and tier spell/heal fixes](releases/combat-item-fixes-20260922/README.md)
are under verification, not deployed. The personal casting bar also freezes
outside combat while spells finish; its cause remains open. Ten focused tests
and full-table item migration/rollback rehearsal pass. Full native build and
nine balance-audit tests also pass.
[Gameplay acceptance](releases/combat-item-fixes-20260922/QA.md) remains required.

## Three-pet management deployed for live QA

The [pet management release](releases/pet-management-20260922/README.md) shows
all three pets with shared commands by default and individual selection by name
or world target. Owner-approved main/OVH activation completed September 27.
Game 2026092201 and automatic launcher 0.3.1 are published; E:/Nightcap is updated
and its actual startup passed. All 15 native hashes, 46 preservation checks,
a full backup restore, 47 publication/rollout fault cases and four encrypted
handshakes passed. The updater now locks only its exact client executable, so
independent Legends installations do not block it. [Production evidence and
recovery](releases/pet-management-20260922/PRODUCTION.md).
[Owner graphical/gameplay QA](releases/pet-management-20260922/QA.md) remains open.

## Tunnel services and starters deployed

The [travel alcove](releases/tunnel-travel-alcove/README.md) replaces the ten city
stones with Merrin and three rustic props. The owner explicitly authorized main
promotion and production deployment on September 22. It is live at
`play.nightcapgame.org`: exact content, three quest hashes/syntax checks,
46 preservation fingerprints, all 15 native process hashes and four encrypted
public handshakes passed. [Production evidence and rollback](releases/tunnel-travel-alcove/PRODUCTION.md).
The owner's silent-hail report exposed a deployment path error: production loads
`plugins/`, but the helpers were under `quests/plugins/`. The
[September 22 hail fix](releases/tunnel-travel-alcove/HAIL-FIX.md) is live after a
graceful restart; the configured runtime passes all 25 quest checks, preservation
and native hashes match, and no new quest errors were found. On September 30 the
owner confirmed Merrin is fixed. His three production files already match main;
the installed handler, scoped content and current pet-release native hashes
were reverified without a restart. [Owner report and current verification](releases/tunnel-travel-alcove/OWNER-QA.json).
All ten destinations and return/PoK books remain; the complete round-trip,
appearance and pet QA matrix remains open. The September 22 recovery wrapper is
pinned to the old native image: read the current-target caveat in the hail-fix
guide before recovery. The earlier local QA deployment remains dated evidence.

[Deployed scope, evidence and exact QA](releases/tunnel-services-starters/README.md):
22 supply merchants, six crafting stations, all 16 trainers, eight walkers,
varied first-name OOC/auction and two finite offers per tunnel trader. Creation
provides 100pp, a primary-class weapon and a 10 AC/+5 main-stat robe. Includes the
latest inventory refresh repair. The owner explicitly authorized main promotion
and OVH deployment on September 21. The server is online: all 15 running native
hashes, 19 runtime files, exact static content, 46 preservation checks and four
encrypted native handshakes passed. A full production-backup restore, forward /
rollback rehearsal and 34 content regressions passed before application.
**Deployed for live QA; manual gameplay acceptance remains open.**
[Activation and rollback evidence](releases/tunnel-services-starters/ACTIVATION.md).

For the reported spell level/filter issue, the owner's `E:/Nightcap` installation
was stale at game release 2026092003 / proxy 0.4.2-dev. The signed production
updater installed 2026092006 / proxy 0.5.0 and verified all 22 managed files. The
desktop Nightcap shortcut now opens `E:/Nightcap/nightcap-launcher.exe`; close the
old nested launcher before reopening it. Real spell levels and merchant filtering
still need the [in-game check](releases/tunnel-services-starters/QA.md#spell-display-and-filter-follow-up).

## Inventory class refresh deployed

[The class-selection refresh fix](releases/inventory-class-refresh-20260921.md)
is live on OVH. Selecting an extra class now publishes the class/AA snapshot
immediately, including when no new skills unlock. Seven regression controls,
the full native build, twelve rollout/rollback rehearsals, all 15 running process
hashes and four encrypted native handshakes pass. Eight player/merchant
fingerprints and all rules were preserved. No client update is required; manual
visual acceptance remains in the linked QA steps.

## Permanent patcher deployed

[Launcher 0.3.0](releases/permanent-patcher-20260920.md) established the stable
starter, automatic launcher updates and patch-before-Play on September 20.
Players keep their game folder and use the same shortcut. That historical release
verified launcher 2026092001 and game 2026092006, with 22 managed game files;
it did not restart production. Its native/Go/UI checks and 63 publication failure
rehearsals passed. The current launcher is 0.3.1 / release 2026092701 and the game
is **2026100201** with 46 files, as recorded in the incident repairs above. Owner in-game
acceptance remains open. [Release operations](ops/permanent-patcher.md).

## Production NPC and spell-access repair deployed

[Release 2026092005](releases/production-bugfixes-20260920.md) is deployed on OVH
with launcher 0.2.2 and 22 signed client files. It repairs secondary-class vendor
usability, level-255 scroll handling and the missing resident OOC API. The owner
explicitly requested main promotion and then production application.

All 15 running native process hashes, 33 runtime files, 30 resident afterimages,
hosted signature/file hashes and four encrypted native handshakes passed for that
release. Eight player/merchant preservation fingerprints and all rules stayed
unchanged. At that release, market epoch 3 had ten finds, six sales and four buys,
each quantity one; the tunnel deployment above supersedes that market stock. A validated
full backup and the previous image/plugin are retained. Players must install the
new launcher/client update; [exact in-game QA](releases/production-bugfixes-20260920.md#exact-owner-in-game-qa)
remains open. The original workspace client and local QA server were not changed.

## Production launcher and hosting candidate

The earlier [coordinated hosted update](releases/hosted-main-update-20260920.md)
was deployed for owner QA and is superseded by the repair above: launcher 0.2.1, signed release2026092004, 22 client files and matching
economy-aware native binaries. All 15 running native process hashes, hosted file
hashes/signature and four encrypted native transport checks pass. Eight player and
merchant fingerprints are preserved; no schema/content migration was replayed.
Market stock rotated once to epoch2. Lavastorm travel readiness stays closed.

A separate [production hosting/launcher candidate](../deploy/production/README.md)
implements hosted signed updates and launcher-managed encrypted transport for ten
friends. Infrastructure, private-account provisioning, backups and guides exist.
The owner selected OVH + Cloudflare; follow the [short setup guide](../deploy/production/QUICKSTART.md).
The owner-test deployment is running at `play.nightcapgame.org`: database restored,
private world registered, Cloudflare IP blocking verified, and signed production
release2026092005 published. Native transport handshakes pass through the encrypted
relay; actual RoF2 login/gameplay and R2 backups remain open. See
[OVH activation and recovery evidence](releases/ovh-activation-20260920.md).
GitHub Actions deployment remains unimplemented. Automatic patch-before-Play and
launcher self-update are implemented by the permanent patcher above. The running local QA server and workspace clients are unchanged.

## Local living economy QA candidate

Finite city-merchant finds, ten EC traders and all six requested residents are
**active for QA** after owner-approved backup/restart. The corrected world and
all eight zones have verified running hashes and clean checked startup logs.
Epoch 1 has 10 finds, six WTS and four WTB offers, each quantity one. Existing
player/merchant fingerprints are unchanged. Dated P1999 prices are scaled for
observed earning boosts before premiums. [Activation evidence](economy/ACTIVATION.md).

Initial activation exposed stale build artifacts; the corrected paired rebuild
and regression guard are recorded in [verification](economy/VERIFICATION.md).
The Classic Lavastorm server map alias is repaired. The owner has now supplied
matching client terrain: archive inspection and five ring samples pass, and the
two pinned assets are staged. The signed QA update is not installed; dependency
approval was blocked by the approval service's usage limit. Khalure still offers
the other eight Classic rings and rejects stale Lavastorm links. Neither client
was changed by this repair. [Client prerequisite](economy/residents/CLIENT-TERRAIN.md).

Costume rendering, normal-account transactions, pricing balance and owner
[in-game QA](economy/QA.md) remain open. [Resident QA](economy/residents/README.md)
includes all six appearances, Trift's OOC story and offered ring landings.
Source promoted to **main** at the owner's explicit request; this is not manual
acceptance or a new deployment. [Promotion scope](releases/main-promotion-20260920.md).


## East Commonlands hub QA candidate

The approved tunnel hub is active on the development server and its source is
promoted to **main**. It moves22existingservices, adds ten paired Classic travel routes
and a PoK bridge, sets new starts, and repairs Ancient Attunement in place.
Existing player state, binds, merchant stock and original travel doors are preserved.
World and all eight zones have verified hashes and clean checked startup logs.
Signed client release **2026092002** is required. Its20files and actual startup
passed on the separate QA client copy. Close the old launcher and use the new
release executable listed in [activation evidence](releases/ecommons-hub-20260920/ACTIVATION.md).
The usual launcher executable is awaiting replacement because Windows has it open.
Owner [in-game QA](releases/ecommons-hub-20260920/README.md) remains open after the
explicitly authorized source promotion.

## Three-pet QA candidate

The server candidate supports one permanent summoned pet per held class, shared
ordinary pet controls and separate eight-slot armor loadouts. The 36 native
class/summon permutations, attack/range cases, migration cases and transactional
failure checks pass. [Evidence and exact owner QA](releases/multiclass-pets-20260919/README.md).
The QA candidate is active: world and all eight zones have verified hashes,
with a fresh backup and clean checked startup logs. [Activation evidence](releases/multiclass-pets-20260919/ACTIVATION.md).
Source is promoted to main; manual acceptance remains pending. The pet feature itself needs
no new client hook; the current EC hub requires release2026092002 above.

The [East Commonlands tunnel proposal](pok/ecommons-tunnel-proposal.md) was approved
and implemented in the September20QA candidate above. Historical proposal findings
remain dated evidence.

## September 19 gameplay release

Signed release 2026091906 installs the client-only silent UI repair: login and
pet armor requests bypass local slash-command echo/history. The usual launcher
now contains 1906. Original-client installation, all 13 file hashes, and actual
startup with proxy 0.4.2 / all 12 features pass; in-game silence QA remains open.
[Delivery and exact QA](releases/client-silent-ui-20260919.md).

The seven requested client/server changes are implemented. The matching world
and all eight zones are now running the verified September 19 build; pet armor
schema and the compact exotic PoK hub are applied. The full backup, fresh guarded
migration/rollback rehearsal, running binary hashes, retained rules and merchant
stock are recorded in [live activation evidence](releases/client-gameplay-live-20260919.md).
The owner explicitly authorized live activation and main promotion before manual
acceptance. [Exact in-game QA and limitations](releases/client-gameplay-20260919.md)
remain open.

Signed client 2026091905 repairs an actual skin-load failure found in owner QA:
the generator's namespace rewrite made RoF2 reject Nightcap and fall back to
Default. The repaired package retains automatic skin selection, preserves the
native schema header, and rejects the old invalid assets during packaging.
[Repair evidence and current delivery](releases/client-skin-repair-20260919.md).
Release 1905 established the repaired skin baseline; 1906 supersedes that launcher.
Installation and startup passed on both the separate QA copy and, after the
owner's explicit folder override, the normal original client. All 13 signed files
and all 12 runtime features were verified. The launcher is ready for owner login;
native character UI loading and gameplay acceptance remain unverified.
Unknown AA title strings remain an open catalog issue (#16); no abilities or owned
ranks were removed to hide them.

## Local QA launcher

The owner confirmed the delivered QA launcher works on September 15, 2026.

A signed offline QA package installs/repairs the 13-file client inventory and
launches the separate supported RoF2 copy with verified runtime health. Use
[the QA executable path and instructions](releases/launcher-qa-20260915.md).
The normal development preview remains unconfigured. Hosted production updates,
Windows signing and full in-game client acceptance remain open.

## Test branch consolidation

After the owner merged PR #52 into dev, all committed source work was consolidated
through dev into test; the owner then requested promotion of that consolidated
source to main (2d18e10). The client implementation is unchanged from the reviewed
phase-20 build; historical branch reconciliation introduced no code changes.
[Exact promotion scope and native/in-game QA](releases/test-consolidation-20260915.md).
This source promotion does not deploy a client or enable the default preview.

## Deployed for live QA

| System | Current state | Remaining acceptance |
|---|---|---|
| PoK hub | Compact 22-service exotic hub; 16 class merchants, 1,747 listings / 1,229 unique items | Grounding, paths, Find, shop and quest interactions |
| Class guidance | Primary/Second/Third on login, hail and commands; both extra slots selectable from level 1 | Normal-account selection, confirmation, release and persistence |
| Bags | 22 positive prices, base 10â€“7,500 platinum; flags/stock retained | Quotes, wallets, restrictions, resale refusal and economy |
| Earned AAs | Purchases/grants/refunds and atomic native class release; paired binary/plugin | In-game counters/effects, reconnect, failure recovery and rendering |
| Five server fixes | Held-class weapon damage, extra-pet ownership/orders, direct-AA duration and owned-AA profile handling | Exact per-build gameplay matrix |
| Skills | Canonical 58,359-row caps; value-1 unlock policy, existing held-Monk slice | Full class/slot coverage and client Skills/trainers |
| AA XP | Minimum level 1 survives matching world startup | Actual XP award/allocation and persistence |
| Waypoints | Marker discovery quest and relocated PoK travel service | Discovery, recall, safe arrivals and Explorer completion |

[Exact live QA checklist](releases/live-qa-20260915/QA.md) Â·
[Deployment and rollback](releases/live-qa-20260915/README.md).
The server release entered dev/test in PR #49. The owner subsequently authorized
all gameplay to move to main for live testing; [promotion record](releases/main-live-qa-20260915.md).
Manual gameplay acceptance remains pending. The September 15 deployment did not
include the new client patch or permanence policy; the September 19 release above
supersedes those portions of the live baseline.

## Issue disposition

**14 open issues** at the latest September 15 query. Six completed issues closed after evidence publication:
#8, #9, #12, #21, #24 and #25. Three reports were administratively consolidated:
#38 â†’ #13 (equipment), #39 â†’ #36 (trainers), #20 â†’ #19 (song landing).
Their unresolved acceptance was preserved; consolidation did not fix the bugs.

| Open issue | What remains |
|---|---|
| #4 | Native AA Class column implemented in September 19 release; in-game acceptance pending |
| #10 | Full multiclass/client/launcher release contract and owner acceptance |
| #11 | Original best-of-stat/AC/stat-cap and heroic-regeneration acceptance |
| #13 | Caster/equipment parity, including off-base client equip submission |
| #14 | Branded launcher, asset manifest and clean-install experience |
| #15 | Hardening, self-update and release pipeline |
| #16 | Missing client titles; preserve owned/system AAs while selecting a remedy |
| #17 | Hub vendor routing awaits QA; global tooltip widening/per-character solution remains |
| #19 | Both movement speed and song landing while running remain unverified/unfixed |
| #22 | Deployed bag prices need economy and in-game purchase acceptance |
| #23 | HTML complete; GitHub plan rejects Pages for the private repo (422); hosting choice required |
| #26 | Approved augment design; no deployed content |
| #32 | Restored waypoint baseline is on main for live QA; full discovery/Explorer acceptance remains |
| #37 | Level-1 AA XP rule now durable; in-game XP proof pending |

#36 is now closed in GitHub, but its body retains unchecked Skills/dual-wield/
trainer acceptance. Those requirements remain part of #10; tracker closure is
not additional gameplay evidence.

Numbers are a dated snapshot. [Live issue tracker](https://github.com/frank-grimes-jr/nightcap/issues).

## Website and documentation

The owner explicitly approved updating and publicly publishing the HTML through
GitHub Pages. The standalone site uses Home, Features, Major Changes and FAQ tabs.
It identifies the release as live testing and contains player-facing information.
Publication verification is recorded in [the website runbook](ops/player-website.md).
The static payload is committed on `gh-pages`, but GitHub rejected activation
with HTTP 422 because this plan does not support Pages for the private repository.
The public URL is not live. A hosting choice remains, independent of the
owner-authorized gameplay promotion.

## Operational lessons

World deletes rule names absent from its compiled catalog. Build/deploy matching
world and zone when rules change; verify `Character:AAExpMinLevel=1` after boot.
PoK cached NPC state overrides fresh spawn placement. The release rehearsed and
removed exactly 17 stale custom states, preserving 245 others. Current backups
and binary/file manifests are retained under `artifacts/live-qa-20260915/` locally.

## Client delivery development (not deployed)

Merged PR #52, now included in test, contains signed manifest verification, full asset staging, guarded
Windows installation/recovery, a Wails/Vue launcher preview and native controller,
a shared configuration/patch-site preflight gate, and a scoped
equipment-submission DLL candidate. The proxy now consumes configuration and
emits process-bound health through synchronous first-export initialization.
The launcher validates that protocol. A new native entrypoint bootstrap passes
disposable-process tests, including actual candidate rejection before main.
Go session orchestration now joins the signed launch lease to native health
approval. Wails now dispatches that backend with serialized Play/Stop state. Production
release policy and supported-game startup acceptance remain required before
enabling the default preview.
Automated fixture tests and independent reviews pass; no new client binary has
been deployed. Native launcher QA, release signing/hardening, remaining client gates
and in-game acceptance stay open. Current [development plan](ops/client-delivery-plan.md)
and [bootstrap evidence](milestones/phase-15-report.md) preserve these gates.

### Verified launch preparation candidate

The launcher now prepares a cached signed release through retained Windows read
locks, including exact executable/config/catalog preflight and validated PE
entry/initializer metadata. The locks allow execution while excluding updates
and path replacement. The native x86 helper now passes private-pipe approval and
owned-session failure tests. Go now requires signed helper inventory, validates
actual process-bound health and retains lease/job ownership through session exit.
Wails Play/Stop wiring and cached offline discovery now pass controller/browser
tests. Production release policy and native supported-game acceptance remain
pending; default Play remains disabled.
[Current evidence](milestones/phase-20-report.md).
