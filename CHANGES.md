# CHANGES

## 2026-09-27 - Scope the updater guard to its selected client

Remove the global eqgame.exe process-name rejection, which prevented Nightcap
updates while an independent EverQuest Legends installation was running. Keep
the exclusive writable handle to Nightcap's exact executable for the entire
transaction, including file-identity checks and launch/update exclusion.
Windows regressions cover an unrelated same-name executable, the running target,
renamed hard-link aliases and attempted launches/updates while locked. The
unrelated game is never stopped. ADR 0030 records the amended boundary.

## 2026-09-22 - Fix Merrin's silent hail in production

The initial deployment put the two travel helpers in `quests/plugins/`, while
production loads `plugins/`. Hailing Merrin raised an undefined-subroutine error.
Installed the same reviewed main payloads in the configured directory and
gracefully restarted production. The installed quest now passes all 25 dialogue,
destination and guard checks; 46 preservation fingerprints and all 15 native
hashes match, with no new quest errors. Public transport checks pass. No SQL,
client or native binary changed; normal startup advanced market epoch 6 to 7.

The regression smoke now resolves the target's actual plugin/quest configuration;
four path tests catch the original wrong-directory deployment and verify config
overrides. Preserve the initial evidence as a dated record. Use the new recovery
wrapper so rollback removes the active helpers too. Details and remaining manual
QA: `docs/releases/tunnel-travel-alcove/HAIL-FIX.md`.

## 2026-09-22 - Three-pet management candidate

Add three named health rows and an explicit All pets scope to Pet Info. Clicking
a name or an owned pet selects that spawn; enemy targeting keeps the selection,
and clearing target or All pets restores shared commands. Window buttons enter
the native server command handler directly, and the exact-client slash-command
gate accepts a fresh server-confirmed roster. Native ownership, AA permissions,
animation/familiar restrictions and combat checks still apply.

Reject stale session/roster requests, clear selection on lifecycle loss, and
keep armor selection separate. Package the generated pet XML with the matching
guarded client hooks. This is a paired client/server candidate, with no schema
or balance change. Owner gameplay acceptance and hosted activation are pending;
see docs/releases/pet-management-20260922/README.md.

## 2026-09-22 - Deploy tunnel travel alcove to production

Owner explicitly requested main promotion and hosted deployment. Promoted the
reviewed test revision through PR 66 and installed Merrin with the native lantern,
barrel and crate on production. Ten exact city destinations and twelve return/PoK
books remain intact; no native rebuild or client download.

Captured production's stopped preimages, validated/restored a full PEQ backup,
passed 20 SQL regressions and exact forward/rollback rehearsal before applying.
All 46 preservation fingerprints, three quest hashes/syntax checks, 15 native
process hashes and four encrypted public handshakes passed. Normal startup moved
market epoch 5 to 6. Private backup and guarded post-activity rollback are retained;
ambiguous guide saved state aborts recovery without deleting it. Appearance and
gameplay acceptance remain open. Evidence: `docs/releases/tunnel-travel-alcove/PRODUCTION.md`.

## 2026-09-21 - Rustic tunnel travel alcove for dev/test QA

Replace the ten oversized East Commonlands city stones with Merrin, a findable
human travel guide, beside a native lantern, barrel and crate. His hail menu
preserves the ten exact destinations/landings; all return/PoK books, merchants,
waypoints, binds and player data remain unchanged. No client patch or C++ build.

Fresh-target SQL guards identity, geometry, routes and full preimages. Rehearsal
covers apply, drift/collision rejection, replay, exact rollback and preservation.
After zone activity use the documented fresh-capture rollback; the immediate
rollback intentionally rejects guide saved-state drift. Native floor/path checks
passed; actual appearance, clicks/Find, round trips and pets await owner QA.
Scope and exact steps: `docs/releases/tunnel-travel-alcove/README.md`.
Installed on local QA after a full backup, exact stopped-target rehearsal and
seven preservation fingerprints; eight zone workers online. Hosted unchanged.

## 2026-09-21 - Deploy tunnel services and starters for owner QA

The owner explicitly approved main promotion and OVH deployment. Applied the
target-captured guarded content migration and multi-offer procedure; installed
the matching world/zone, supervisor and 19 runtime quest/plugin files. The server
is online with 90 custom NPCs, 22 merchants / 2,199 listings, 16 trainers, six
stations, eight patrols and creation-only 100pp/class gear. Market epoch 5 has
20 sales, 12 buys and ten merchant finds, initially one copy each.

Before application, restored the full 445,236,201-byte SQL backup into isolated
MariaDB and passed exact forward/rollback, three rotations, 148 starting-rule
comparisons and 34 content regressions. Seventeen rollout failure tests passed.
All 46 player/rule/merchant preservation checks, 15 running process hashes,
static content afterimages and four encrypted handshakes passed. Previous runtime,
full backup and scoped rollback are retained. Actual RoF2 behavior and owner
acceptance remain open; see `docs/releases/tunnel-services-starters/ACTIVATION.md`.

## 2026-09-21 - Index tunnel migration verification on full PEQ data

The full OVH restore rehearsal exposed repeated table scans in exact preimage
checks. Prefix each unchanged binary field comparison with the table's native
key columns so forward, rollback and afterimage checks use indexes. Case-only
drift still rejects the migration. Rehearsal now checks both drift rejection and
actual MariaDB EXPLAIN index selection; gameplay definitions are unchanged.

## 2026-09-21 - Tunnel services, channel activity and starter provisions candidate

Adds a planned general merchant with all 46 components from the approved Classic
level-50 spell catalog, food/water/bandages and all instrument families; 21
tradeskill suppliers covering 12 disciplines, six crafting stations, 16 trainers,
irregular service groups and eight patrolling residents. Guarded fresh-capture
SQL rejects collisions/drift and limits saved-state invalidation to affected EC
instance-zero non-corpse rows. Plains Pebble was previously unpriced; its reviewed
base price becomes 100 copper, with native merchant modifiers still applied.

Expands the finite tunnel market to ten sellers and six buyers, two distinct
items per actor. Real available item links/prices use varied first-name auction
messages and separators. One coordinator varies OOC among six residents and eight
walkers, avoids immediate repeats, and stays silent without players. Composite
offer/audit keys retain atomic trades and historical audit; rollback restores the
original rotation routine without deleting audit history.

New-character creation grants exactly 100pp and a modest primary-class weapon
plus a no-trade 10 AC/+5 main-stat robe. Empty-reservation and equipment guards
reject replay, existing wallets and unexpected starting gear. There is no login
grant. Rollback retains definitions for already-owned items and preserves wallets.
Requires matching world/zone, content cache, supervisor and quest plugins.
Candidate only: production application and owner gameplay acceptance remain open.
Evidence, exact QA and rollback: `docs/releases/tunnel-services-starters/`.

## 2026-09-20 - Refresh inventory classes immediately after adoption

Class selection reloaded server skills/slots but left the client's same-zone
class snapshot stale. Publish the existing class/AA snapshot when reconciliation
detects changed slots, including selections that unlock no new skills. Reuse that
publication for native slot assignment; no extra refresh occurs for unchanged
classes or ordinary level-ups. Regression tests exercise actual server methods
and the real client parser. No client update or SQL migration is needed. The
owner authorized direct main promotion and server deployment; evidence and
remaining visual QA: `docs/releases/inventory-class-refresh-20260921.md`.
Deployed to OVH after full native build and twelve rollback rehearsals. All 15
running process hashes, eight preservation fingerprints, rules, startup checks
and four encrypted connection handshakes pass. A validated backup and the
previous runtime image are retained; client files and quests are unchanged.

## 2026-09-20 - Permanent patcher and launcher self-updates

Published launcher 0.3.0 through a stable signed-channel starter. The launcher
checks on opening/selecting a client and applies required changed-file patches
before Play. Signed inventory/catalog evolution no longer requires a new desktop
for ordinary game updates; recovery validates its signed candidate destinations.
Launcher/game counters and minimum compatibility are separate. Independent review,
native/Go/UI tests, 63 publication failure rehearsals and hosted verification pass.
Existing players need one transition starter ZIP, then keep the same shortcut.
No game files changed from 2026092005, no server restart or DB writes. Signing
metadata renewal and 2028 starter trust migration remain operator duties; gameplay
QA is still open. See docs/releases/permanent-patcher-20260920.md.

## 2026-09-20 - Deploy production NPC and multiclass spell repair

At the owner's explicit request, applied the paired native/plugin repair to OVH
and published signed client release 2026092005 with launcher 0.2.2. All 15 running
process hashes, 33 runtime files, 30 resident afterimages, 22 hosted file hashes,
signature and four encrypted native handshakes pass. Eight preservation checks
and all rules stayed unchanged. A validated on-host backup and previous image
remain available; no content/schema migration was replayed. Market startup moved
epoch 2 to 3 with six sell/four buy offers. Players must install the new client
update. In-game acceptance remains open; see the production bugfix release record.

## 2026-09-20 - Authorize production bugfix source promotion

The owner requested the tested NPC and multiclass spell fixes be pushed to main.
Promote the reviewed source through dev/test/main with its existing test and
rollback evidence. Production release 2026092005 upload/deployment is separately
awaiting explicit approval after automatic review rejected the transfer. Source
promotion does not establish deployment or completed in-game acceptance.

## 2026-09-20 - Multiclass spell-access production repair candidate

Use original spell class levels plus each character's held classes for merchant
filtering, scribing, memorization and gem casting. Stop globally widening shared
spell definitions on class selection; preserve existing saved data. Client hooks
cover both merchant masks and the earlier scribe item gate, retain native item
restrictions, and clear stale identity. Restore 11,057 packaged spell class rows,
with explicit protection for generated recall. Production startup rejects
binaries missing the required economy, OOC and spell-access contracts.

Native/client regression tests, full Linux and Windows builds, signed release
2026092005 and launcher 0.2.2 pass. Deployment awaits explicit host/payload
approval after an automatic upload rejection. Evidence, rollback and exact
in-game QA: `docs/releases/production-bugfixes-20260920.md`. This is not manual
acceptance or main promotion.

## 2026-09-20 - Restore resident NPC OOC quest API

Add the native `quest::ooc` adapter required by Trift's timer. Send literal NPC
text to every client in the zone, including timer events without a client
context. Regression tests cover sender, channel, multiple clients, missing
owners and percent signs. Deploy a rebuilt zone binary before relying on this
API; manual in-game confirmation remains open.

## 2026-09-20 - Combine hosted production and current main

Integrate the production launcher/hosting candidate with the owner's current
main gameplay release. Preserve both Classic terrain retirement hashes in the
generated production trust policy and require launcher 0.2.1 for the expanded
22-file inventory. Hosted audit confirms 33 runtime files and all 30 resident
afterimages already match; the paired native update corrects older world/zone
binaries without replaying database migrations. Release2026092004 is hosted,
all22signedfile hashes and four encrypted native transport checks pass, and all
eight player/merchant fingerprints are preserved. Verification and remaining gates:
[coordinated hosted release](docs/releases/hosted-main-update-20260920.md).

## 2026-09-20 - OVH owner-test activation

Deploy the private container candidate to the owner's OVH VPS and Cloudflare
hostname, restore the complete QA snapshot, preserve character ownership across
the verified private-login namespace migration, and publish signed production
release2026092003 / launcher0.2.0. Hosted signatures/file hashes and native relay
session handshakes pass; owner versus unapproved-IP HTTPS checks return200/403.
Local QA and gameplay branches remain unchanged. Real RoF2 acceptance, encrypted
R2 backups and release automation remain open. See docs/releases/ovh-activation-20260920.md.

## 2026-09-20 - Production Compose mount correction

The first OVH container startup rejected a stray `mode=1777` mount: YAML flow
lists split the unquoted tmpfs options at the comma. Quote both mount strings
and add a regression check against Docker Compose's resolved configuration,
including the no-published-ports and internal-network contracts.

## 2026-09-20 - OVH and Cloudflare onboarding guide

Record the owner's provider choice and add a short setup guide covering purchase,
domain, private deployment, backups, acceptance and friend onboarding. Clearly mark
release automation and launcher self-update as pending. No hosting was activated.

## 2026-09-20 - Private container hosting candidate

Add isolated container networks, deny-first IP controls, private scrypt account
provisioning, native credential-log redactions/self-test and encrypted backup tooling.
Real MariaDB provisioning and failure tests caught and fixed table-lock and truncated
backup issues. Include owner/friend guides, hosting cost research and explicit native
acceptance steps. No public service is deployed; host/domain selection, full runtime
restore and hosted ten-player QA remain open. See deploy/production/README.md.

## 2026-09-20 - Production launcher candidate

Add a production-only hosted signing policy, single-object signed channel metadata,
immutable release packaging, friend instructions and a Windows build script.
Play can own an encrypted WebSocket relay for fixed native login/world/zone/chat
ports and temporarily configure/restore eqhost under its existing installation lease.
Automated manifest, lifecycle, relay and frontend checks passed. No production seed
or final hostname-bound Windows launcher has been distributed. Hosted/native
acceptance remains pending; the live QA stack and client are unchanged.

## 2026-09-20 - Owner-authorized main source promotion

Promote verified test revision `dd24fe0` and this documentation update to main,
including the existing pet roster, EC hub, living economy, named residents and
Lavastorm packaging preparation. Repository regression passed 62 tests with one
existing opt-in skip; the uncached launcher Go suite passed. No runtime restart,
SQL, client installation or global travel-readiness change accompanies this push.
Preserve outstanding manual acceptance and signed-client release checks.
[Promotion scope and QA](docs/releases/main-promotion-20260920.md).

## 2026-09-20 - Classic Lavastorm QA assets staged

The owner supplied `lavastorm.s3d`; archive contents and five ring-ground samples
match the installed Classic server map. Pin both archive hashes in the read-only
generator and add them to the signed QA inventory, with exact-hash retirement of
revamped `lavastorm.eqg`. All 20 previous package inputs remain byte-identical.
Thirteen client-asset tests, the normal launcher Go suite and the full repository
regression pass (62 passed, one existing opt-in skip). Independent packaging
review found no actionable issues. The earlier dependency approval failure left
signing, desktop build and installation pending; this owner-requested dev/test
source promotion does not deploy that client update. Neither client was changed,
no server restart occurred, and travel readiness stays gated.
[Evidence and continuation](docs/economy/residents/CLIENT-TERRAIN.md).

## 2026-09-20 - Living economy and residents activated for QA

After the owner-approved full PEQ backup and controlled restart, corrected world
and all eight zone binaries are running with matching hashes. Epoch 1 contains
10 finds, six sales and four purchases, all quantity one. All 30 resident rows,
29 runtime files and 11 post-boot player/merchant fingerprints verify; checked
startup logs are clean. The Classic Lavastorm server map alias is repaired, but
its client terrain remains missing, including in `E:/EQ_Local`. Khalure offers
eight Classic rings until that separate client gate is resolved. No original
client edits or main promotion. [Activation and remaining QA](docs/economy/ACTIVATION.md).

## 2026-09-20 - Market build provenance correction

The first controlled activation refused world startup: a reused object embedded
the earlier one-argument rotation call while the reviewed source/schema require
three. The build helper now rejects existing output directories, compares source
hashes across compilation and checks the actual ELF startup contract before
writing its manifest. Three regression tests cover stale artifacts and build-tree
reuse. Recovery recompiles every changed market source/header and its dependents;
retain the failed artifacts and startup log separately from the corrected pair.

## 2026-09-20 - Lavastorm travel readiness guard

Withhold Khalure's Lavastorm destination until the explicit
`nightcap:classic_lavastorm_client_ready` data bucket is `1`. The separate QA
client currently lacks Classic terrain; repairing the server collision map alone
does not make that landing safe. Missing readiness also rejects stale links.
Other rings are unchanged. All 23 resident quest assertions pass. The original
client remains untouched.

## 2026-09-20 - Six named tunnel residents (candidate)

Add the requested Sortre, Camil, Rekk, Nalin, Trift and Khalure as six residents
alongside the ten economy traders. Persistent visual-only armor/weapons do not
create loot. Trift is level 12 and tells his Butcherblock corpse story in OOC;
Khalure offers era-checked druid-ring travel. Guarded additive SQL and scoped
rollback preserve existing content and player state. Map verification found a
missing configured Classic Lavastorm map alias; its verified source exists, but
repair is an activation prerequisite. No live writes or client changes. See
[resident setup and exact QA](docs/economy/residents/README.md).

## 2026-09-20 - Finite city finds and EC tunnel economy (candidate)

Add restart-scoped, quantity-one finds to selected city merchants and ten
player-looking EC traders with real WTS/WTB offers, auction lines and local
chatter. Curate Classic drops from dated P1999 price evidence; scale the reference
for increased item drops/vendor payouts before the seller premium. Native atomic
stock/wallet/cursor transactions prevent partial exchanges and concurrent sales;
ambiguous commits quarantine until reconnect. Closing a shop invalidates quotes,
and ordinary quest hand-ins explicitly return items and coin. Matching world/zone,
schema and quests must ship together; no client change. Disabled-by-default setup,
scoped rollback and [exact owner QA](docs/economy/QA.md) are included. Not yet active;
pricing balance and manual acceptance remain open.


## 2026-09-20 - East Commonlands tunnel hub (active QA candidate)

Move 22 existing services to the approved tunnel layout, add ten native Classic
routes with separate return books and a PoK bridge, and set new starts to EC.
Preserve existing binds, positions, stock, NPC definitions and old routes. Repair
owned Ancient Attunement using a visible General AA, native recall spell 42604
and complete client strings. Signed release 2026092002 includes zone models,
portal imports, map labels and pinned classic Nektulos selection. Retirement uses
locked original files and atomic conflict-preserving recovery. Fresh guarded SQL
and scoped saved-state invalidation are required; no broad repop. Manual QA and
main promotion remain open. World/all eight zones and migrated rows now verify;
all nine checked player-state tables are unchanged. See [release QA](docs/releases/ecommons-hub-20260920/README.md).

## 2026-09-19 - Three class pets and shared controls (active QA candidate)

Use original summon spell eligibility to assign one persistent pet per held
class, independent of widened spell access or summon order. All class pets use
the ordinary command handler and their own eight-slot armor loadout. Keep one
stable pet-window representative and restore all pets across database saves,
including a class-aware suspended minion. Save/load failures quarantine the
session; armor restoration preserves underlying gear and armored resource caps.
Promoted through dev/test and activated on the development server after graceful
saves and a verified full backup. World and all eight zone hashes match; required
rules and PoK stock remain intact. Manual acceptance and main promotion are open.
Older binaries cannot preserve the extended pet save keys without a scoped state
backup. See
[ADR 0039](docs/adr/0039-class-pet-roster-and-persistence.md).

## 2026-09-19 - Silence automatic UI requests

Replace the client slash-command interpreter with the verified native channel
packet sender for class/AA refresh and pet armor actions. Automatic requests no
longer enter Say echo or command history; normal chat/errors and server item
safeguards remain intact. Proxy 0.4.2 / signed release 2026091906 updates the
ASLR-aware compatibility guard and adds native transport regression coverage.
[Delivery and exact QA](docs/releases/client-silent-ui-20260919.md).

## 2026-09-19 - Repair rejected Nightcap UI skin

In-game evidence showed the custom skin falling back to Default. The XML generator
had rewritten the native `Schema` element to `ns0:Schema` and removed its required
literal namespace declarations. Preserve the stock unprefixed schema and ASCII
header. Add regression coverage and make signed packaging reject the malformed
representation. Release 2026091905 includes this repair and automatic skin loading.
Prior startup-health success did not prove character UI loading; 1903/1904 skin
assets are superseded. The usual launcher path now contains 1905; signed installation
and startup passed on both the QA copy and the explicitly authorized original
client with all 12 features active. All 13 original-client files match the signed
manifest; native character UI acceptance remains pending. Missing AA title data remains a separate open catalog issue.
[Repair evidence](docs/releases/client-skin-repair-20260919.md).

## 2026-09-19 - Activate gameplay release for live QA

Deployed matching world/zone binaries and 22 source/build overlays after graceful
character/zone saves and a verified 441,566,517-byte PEQ dump. Created the additive
18-column pet armor table and applied the fresh guarded 22-service PoK relocation.
All eight zone processes and world have the expected hashes; required rules and
merchant stock are retained, with no Error/Fatal lines in the checked fresh logs.
The owner authorized main promotion before manual acceptance. Automatic-UI client
1904 installation remains gated on game exit and the authorized folder choice.
[Evidence and recovery](docs/releases/client-gameplay-live-20260919.md).

## 2026-09-19 - Automatic Nightcap UI loading

The exact-build client patch now selects the Nightcap skin during native UI load
for existing and new characters. No per-character `/loadskin` command is needed;
window positions and hotbars keep using the native layout handling. Signed
release 2026091904 adds two guarded call sites and requires all 12 features
before startup. Native calling-convention tests, exact-client checks, both Go
suites, and eight browser tests pass. The owner explicitly requested deployment
and main promotion; gameplay acceptance remains separate.

## 2026-09-19 - Client and gameplay candidate

Added native inventory multiclass labels, an AA Class column, and an eight-slot
Pet Armor tab with equip/remove/inspect and durable per-class item storage.
Beneficial player/owned-pet buffs now use true permanent duration, including AA
buffs and disciplines as explicitly requested; death removes them. Player DoTs
cast instantly and melee rounds continue during casting. The PoK planner groups
22 existing services near arrival and stages verified later-era models without
changing merchant stock. Signed client packaging now requires 13 files.

Validation includes native world/zone builds, item transfer failure injection and
SQL round trips, independent migration/rollback rehearsal, and client/launcher
tests. Native UI SEH prologues handle Windows image relocation. Pet armor rejects
temporary No Rent and evolving/scaling items; its escrow table must never be
dropped while it owns items. Exact deployment, rollback and required in-game QA:
[September 19 guide](docs/releases/client-gameplay-20260919.md).

## 2026-09-15 - Usable signed offline QA launcher

Added a generated QA-only signed bundle and portable launcher state so Check,
Update/Repair and Play work against an independent RoF2 copy. The default preview
remains unconfigured. Existing signature, journal recovery, executable/patch-site
and runtime-health gates are retained. Fixed a Windows post-exit image-mapping
race with a bounded non-mutating cleanup probe. Exact package/expiry, rebuild,
rollback and manual QA: [launcher guide](docs/releases/launcher-qa-20260915.md).

## 2026-09-15 - Consolidate reviewed client work into test

Promoted the dev history after owner-merged PR #52 and reconciled historical
local source refs without changing their already-integrated code. Published exact
launcher, equipment, PoK and held-Monk QA steps. All committed source branch work
is included; production client signing, manual acceptance and live deployment
remain separate. [Promotion record](docs/releases/test-consolidation-20260915.md).

## 2026-09-15 - Connect launcher Play and Stop to verified sessions

Wails and the serialized controller now dispatch the verified session backend,
keep conflicting actions disabled through cleanup and report session exit/errors.
Cached release discovery supports offline attempts with fresh checks on every
launch. Play requires compiled release opt-in and complete trusted inventory; the
default preview stays disabled. Seven isolated Chrome tests, desktop Go checks
and the Windows build pass. [Evidence](docs/milestones/phase-20-report.md).

## 2026-09-15 - Own verified bootstrap sessions in the launcher backend

The Go session owner now requires the helper in signed inventory, supplies private
nonce/handles, validates actual process-bound health before startup approval and
retains verified files through session exit. An outer Windows job covers helper
failure before child PID publication. Concurrent cancellation preserves ownership
and reports cleanup errors. Native fixtures and desktop Go checks pass; Wails
Play wiring, signing and supported-game acceptance remain open. No live client
deployment. [Evidence](docs/milestones/phase-19-report.md).

## 2026-09-15 - Add native bootstrap helper and session protocol

Built the x86 helper around the pre-entry gate, with bounded inherited-pipe
messages, private nonce propagation, health approval before resume and retained
process/job ownership. Parent loss and post-start stdin closure terminate only
the owned session. Seventeen disposable native scenarios pass. The helper is
unsigned and Go/Wails integration remains open; no live client deployment.
[Evidence](docs/milestones/phase-18-report.md).

## 2026-09-15 - Validate bootstrap addresses from held PE files

Launch preparation now derives executable entry and proxy initializer RVAs from
its retained verified handles. A bounded PE32 parser checks conventional Windows
alignment, sections, code permissions and named exports; forwarded, ambiguous or
malformed initializers fail before process creation. Signed but invalid DLLs
release all launch locks. No Play integration or client deployment yet.
[Evidence and remaining work](docs/milestones/phase-17-report.md).

## 2026-09-15 - Hold verified client assets during launch preparation

Added Windows read-sharing leases that allow image execution while denying
updates, replacement and ancestor renames. Offline preparation verifies signed
checkpoint/content and exact executable/config/catalog through retained handles.
Failures/cancellation release locks. Repaired the stale generated-proxy constant
consistency test discovered by the full suite. The lease is not connected to
Play yet; bootstrap metadata, health exchange and remaining parity are open.
[Evidence](docs/milestones/phase-16-report.md).

## 2026-09-15 - Add a proxy bootstrap before executable entry

The x86 bootstrap primitive stops a newly created owned process at its exact PE
entrypoint, initializes the verified imported proxy while main remains suspended,
and resumes only after health approval. Failures terminate before continuing a
stopped event; job/process ownership transfers on success. Added an explicit DLL
initializer export and version 0.3.0-dev, with original DirectInput ordinals kept.
Native failure, owner-crash and repeated-session tests pass. Launcher integration
and actual RoF2 acceptance remain open; no installed client changes. See ADR 0034.

## 2026-09-15 - Gate proxy forwarding on required runtime activation

The candidate DLL now consumes strict configuration, pins its lifetime and blocks
forwarding until all required patches succeed. Failures write process-bound
health where possible and terminate; optional MQ2 surveying defaults off. Patch
writers now check cache/protection failures. Added atomic health and Go validation
plus native fault/disposable-host tests. No installed client changes. Startup
ordering and the launcher process handshake remain release gates; Play is disabled.
Design: docs/adr/0033-bind-proxy-health-to-client-process.md.

## 2026-09-15 - Require shared configuration and patch-site preflight

Public client installation now requires manifest-bound configuration/catalog
assets and checks the exact executable plus 22 recorded PE patch sites under its
exclusive handle before mutation. Generated C++ and Go guard data share one
versioned catalog. Disabled/missing/ambiguous feature keys and altered metadata
fail closed. Exact-client checks, x86 build and focused tests pass. No live client
files changed. DLL configuration consumption/runtime health remain unfinished;
static preflight never enables Play. Contract: docs/adr/0032-share-client-patch-catalog-and-preflight.md.

## 2026-09-15 - Add the Windows launcher UI and release controller

Added a Wails/Vue preview with client-folder selection, inventory, update/repair,
recovery, cancellation and session activity. Every update repeats signed metadata
and content checks through the native controller; local generation inspection
identifies damaged/expired files and pending recovery. Fixed pending-update Cancel
and stale inventory display after installation. Windows build, 162 Go cases and
six isolated browser tests pass; independent review found no blockers. Native
interactive QA remains pending. Production trust, runtime health and Play remain
unimplemented; no client files were deployed. Build/QA: eq-launcher/README.md.

## 2026-09-15 - Install and recover complete client asset generations

Added guarded signed installation, immutable backups, bounded recovery journals,
tombstones and whole-generation rollback. Actual subprocess exits during install
and recovery pass; locked unchanged Windows files no longer block rollback.
Local release checkpoints allow repair and reject ordinary downgrades. Play
remains false; production keys/health/UI and retention management are unfinished.
Real client files are unchanged. Protocol/limits: docs/adr/0031-journal-client-generation-recovery.md.

## 2026-09-15 - Exclude game launch and concurrent client updates

Added a fail-closed Windows process check and exclusive executable handle. It
blocks game launch and another updater for the duration of installation without
writing executable bytes. Disposable executable tests verify the actual Windows
sharing behavior; independent review found no blockers. Write access is required
for the guard. Design and evidence: docs/adr/0030-exclude-game-launch-during-client-update.md.

## 2026-09-15 - Stage complete signed client asset generations

Added launcher size/hash diff and bounded HTTPS staging with signed metadata,
per-hop redirect validation, local-copy rehash and complete candidate marker.
Windows rooted access/junction checks keep staged files outside the client;
failed cleanup is reported. Tests cover partial downloads and release failures.
Activation, journaled recovery and Play gating remain unfinished; no client
assets are installed by this package. See eq-launcher/README.md and phase 10.

## 2026-09-15 - Add scoped RoF2 equipment submission candidate

Exact-build redirects allow off-base equip attempts to reach server held-class
validation. Only the active item/thread class return changes; zero masks, other
callers and native checks remain. Includes guarded rollback, x86 scope tests,
exact client checks and independent review. Candidate only; no deployment or
manual acceptance. Evidence: eq-client-dll/docs/equipment-qa.md and ADR 0028.

## 2026-09-15 - Add Darth Classic Ascended GM summon kit

Added the requested MQ2 macro for Darth: 20 items across 18 verified IDs,
including Classic Valorium armor, jewelry, haste, sword/shield and Fiery Avenger.
Live PEQ checks verified Human Paladin eligibility, level requirements and
lore-safe duplicate quantities. The macro stops on wrong character, failed
summons or a blocked cursor; no level/equipment mutation is issued directly.
It is a practical high-end kit, not an exhaustive encounter-specific BiS proof.
Installed into the local MQ macros folder; in-game execution remains untested.

## 2026-09-15 - Begin trusted client patcher and parity delivery

Reviewed current client issues and the approved full multiclass contract. Added
the Go launcher core with signed canonical metadata, exact inventory, path/host
constraints and anti-rollback validation; read-only RoF2 executable preflight
shares the existing DLL guard. No client files were modified or new hooks deployed.
The Wails shell, transactional installer, signed release pipeline and outstanding
client parity gates remain active work. Plan: docs/ops/client-delivery-plan.md.

## 2026-09-15 - Promote tested gameplay to main for owner live QA

Owner explicitly requested all gameplay changes move to main before their live
testing. Promote the reviewed dev/test history containing AA persistence and
class release, skills, weapon/pet/buff fixes, waypoints, PoK hub relocation and
bag pricing. Existing live deployment remains the same; manual acceptance and
unresolved issues remain open. Record this release-specific branch-policy
exception and the exact QA/rollback links in docs/releases/main-live-qa-20260915.md.

## 2026-09-15 - Refresh player website and current documentation

Rebuilt the standalone player guide with Home, Features, Major Changes and FAQ
tabs. Corrected class-slot availability, spell learning, skill progression and
PoK merchant guidance against deployed quest behavior. Added a current status
index, documentation map and dedicated GitHub Pages publication runbook; dated
reports retain their original evidence with supersession notices. Updated hub,
bag and client QA documentation without claiming unfinished gameplay acceptance.
Browser checks cover tabs, keyboard focus/history, deep links, disclosure, four
viewport widths and no-JavaScript readability; desktop/mobile visuals reviewed.
Static payload is published on gh-pages; GitHub rejected Pages activation with
HTTP 422 because the current plan does not support the private repository.
The public URL is not live and #23 remains open. See docs/ops/player-website.md.

## 2026-09-15 - Deploy combined server, AA, PoK hub and bag-price release for live QA

Owner authorized all implemented candidates for live testing. Integrated the
final earned-AA/atomic class-release binary (including five weapon/pet/buff/AA
fixes), matched PoK guidance, sixteen class merchants, relocated utilities and
22 bag prices. Retained a verified full PEQ backup and exact binary/file/content
rollback assets. All 351 server/AA evidence tests, 14 MariaDB hub controls, four
planner tests, three pricing tests, 13 title-audit tests and merged quest checks
passed; independent review verified source/binary/plugin compatibility.

Post-start checks found the old world deletes the custom level-1 AA rule during
orphan cleanup. Built and installed matching world from the same 2,787-file pinned
source and restored the rule to 1. Also cleared exactly 17 stale custom PoK NPC
saved-state rows after a verified rollback rehearsal; 245 other PoK states remain.
These runtime issues explain why a DB repair or spawn relocation alone can vanish
after restart. World and all zones must use the matching release generation.

No blanket AA disablement, experimental AA pool, augment design, balance-number
change or new client patch was deployed. All manual acceptance remains open;
test-to-main still needs owner sign-off. GitHub Pages publication awaits specific
public-publication approval required by automatic review. Full per-feature QA,
hashes, retained limitations and rollback: `docs/releases/live-qa-20260915/`.

## 2026-09-15 - Prepare guarded bag-vendor pricing candidate (#22)

Captured all 22 Bartholomew Packwell items: 18 free bags and four legacy prices
up to one million platinum. Added a proposed 10–7,500 platinum base-price ladder,
exact original-price rollback, idempotent apply and stock/metadata/drift guards.
Corrected the setup comment: nodrop=0 means NO TRADE, preserving server resale
refusal. Three disposable-database integration tests (including nine drift cases)
and 13 AA tests pass; live bag rows remain unchanged and scratch schemas are gone.
Four entries on unused merchant list 9905 share these item IDs. Economy, specialized-container
behavior, shared pricing and in-game QA remain review gates. No live price/cache
change or main promotion. See docs/ops/bag-vendor-pricing.md.

## 2026-09-15 - Complete live AA title preflight and preserve owned abilities

The first live #16 audit exposed invalid offline assumptions: native loading
accepts ability ID 0 and truncates absent next-rank references. Corrected the
audit and added failing-before/passing-after controls; all 13 tests pass.
Live PEQ has 192 enabled missing-title families and 19 intersecting saved rows:
two for an unnamed 24-cost Paladin rank and 17 for the zero-cost Ancient
Attunement system AA. The old zero-purchase assertion is stale. No disablement,
refund or client edit occurred; raw title coverage is not a display verdict.
See docs/audits/aa-titles-20260915/ for full findings and hashes.

## 2026-09-14 - Reconcile GitHub issue completion and release gates

Reviewed all 24 open issues. Closed #8, #9, #12, #21, #24 and #25 with published
source and acceptance evidence, and posted concrete remaining gates for 18 issues.
Published the previously accepted DLL commit 397d51b on a dedicated branch;
its exact-client B2 verification passed. Kept #11 open after finding deferred
original acceptance details. Pages still returns HTTP 404. The existing local
main includes unapproved candidates and was not pushed. PR #47 targets dev.
See the issue audit,
updated next steps and phase-3 milestone report. No gameplay deployment occurred.

## 2026-09-14 - Begin exact AA client-title audit (#16)

Added a read-only SQL snapshot and offline Python audit of RoF2 type-1 AA
titles across complete rank chains. Saved ownership is counted by first-rank
ID; disabled families remain distinguishable. Incomplete exports, malformed
catalogs and unresolved ownership fail closed. Ten unit/CLI tests pass;
independent review found no actionable issues. The local client has 2,470
nonempty type-1 titles. Docker is stopped, so fresh PEQ counts and SQL execution
remain unverified. No AA disablement, database writes, server reload or client
edit occurred. See docs/ops/aa-client-title-audit.md for the runbook and QA gates.

## 2026-09-13 - Verify class-release disconnect and fresh-process recovery

Added isolated native Process/OnDisconnect and profile-loader controls: three
processes, eight operations prove rollback survives disconnect, saved classes,
skills and AA counters reload, and retry refunds exactly once. No engine or live
changes. All 351 Python calculator/evidence tests pass. The final run restores
its fixture preimages and event setting. Initial
disabled-event failure and its unavailable original synthetic timestamp are
retained and documented. Real network reconnect, post-packet processing and
uncertain COMMIT remain unverified. See docs/balance/native-aa-session-recovery.md.

## 2026-09-13 - Implement atomic class-release candidate

The AA feature branch now stages and transactionally saves discipline slots,
canonical earned-AA refunds, counters, and retained-class skill clamps. The
matching Perl plugin uses one native boolean call. Signed slot validation and
conditional class selection close the Lua narrowing and stale-slot bypasses.
Failed class changes invalidate the session and terminate processing before
linkdead AI; the legacy non-atomic purge path is retired.

Candidate only; no deployment or promotion. Forty native cases (131 operations),
87 C++ tests, 348 Python tests and 15 actual Perl assertions pass. Matched before-state evidence
retains six expected failures. Client packet ordering, native passive-bonus removal,
rollback and clone restoration are verified. Initial test fixture failures are
retained; actual disconnect/reconnect/uncertain-COMMIT recovery and in-game QA
remain gates. See docs/balance/native-aa-class-release-candidate.md.

## 2026-09-13 - Reproduce earned-AA class-release inconsistencies

Added seven native before-state controls (36 operations) for class release on the
AA ownership feature. Six fail the required contract and retained-Wizard slot
promotion passes. Full, partially usable, and suspended releases leave earned
Wizard ranks persisted; partial access refunds only 18 of 30 points, and full
suspension refunds none. Shared-family retention is checked separately.

The harness records whether injected failures actually execute. Its bare client
skips the old general Save: class-write injection executes, but point-write
injection does not. This does not certify the live Save failure path, skills,
bonuses, or reconnect. Clone character fixtures/triggers are removed and original
class values/timestamps, skill rows, and AA catalogs are restored or unchanged.
ADR 0026 defines the required native atomic slot/refund/skill change. No engine
fix or live deployment is claimed; AA promotion remains gated on implementation.
All 343 Python calculator/evidence regressions passed; the retained test log is
docs/balance/aa-release-before-python-tests.log.

Read-only audits of PEQ and the clone found no SPA472 spells among 40,724 entries,
so no current spell can enable the passive-AA toggle path. Future toggle catalogs
require a durable selection design before activation. See docs/balance/native-aa-class-release.md.

## 2026-09-13 - Commit AA purchases and grants before reporting success

AA purchases and explicit/silent grants now persist earned ownership and all AA
point counters atomically before publishing ranks, wallet changes, or purchase
events. Grant callers observe failures; successful batch ranks persist individually.
Thirteen native before/after controls pass across 52 operations per phase,
including exact success-event ledgers, charged repurchase, and SQL rollback.
The fresh 2,787-file build succeeds, with 87 C++ and 339 calculator/evidence tests
passing. Initial C++ tests were run from the wrong directory; their misleading
zero exit status is rejected by summary validation, and the preserved rerun in
the dedicated fixture passes. Clone fixtures and triggers are removed; the AA
catalog is unchanged. No live binary or balance numbers changed. Full batch caller,
toggle, class-release, reconnect/network, ordinary-save and manual QA gates remain.
See docs/balance/native-aa-purchase.md and ADR0025.

## 2026-09-13 - Refund full earned AA ownership and guard invalid profile saves

Bulk refund/reset now refunds full earned cost across active, partially usable,
and suspended ranks while retaining grant-only abilities. Ownership and wallet,
spent, and expended counters commit together before session state changes.
Invalid sessions cannot reload AAs alone or overwrite the main character row;
transaction failures immediately ask the player to reconnect. Client::Save now
propagates the profile-save result. Eleven native controls pass across 59
operations per phase, with 87 C++ and 334 calculator/evidence tests passing. Clone fixtures and the failure
trigger are removed and the AA catalog is unchanged.
Gotchas: invalid sessions cannot save main character-row progress until reconnect;
other earlier Client::Save writes are not made atomic. Purchase/grant/toggle,
class-release, real reconnect/network failure, and manual QA remain open. No live
server or numerical balance settings changed. See docs/balance/native-aa-bulk.md
and ADR0023 for retained evidence and boundaries.

## 2026-09-13 - Make single-AA reset and final-charge removal durable

Explicit rank reset now removes canonical earned ownership even while suspended.
Final-charge consumption removes that ownership and increments expended cost
once. A transaction checks persisted ownership, updates the selected row and
spent/expended counters together, and changes session state only after commit.
Four native before/after controls pass across 22 operations, including an injected
character-update failure that rolls back the prior owned-row deletion. The fresh
2,787-file build succeeds; all 87 C++ and 329 calculator/evidence tests pass.
Clone rows and the temporary
failure trigger are cleaned up, with the AA catalog unchanged.
Gotchas: this is single-AA reset, not refund/all-AA reset. Broader save/purchase,
class-release and uncertain-commit handling still block promotion. No live server
or numerical balance settings changed. See `docs/balance/native-aa-removal.md`
and ADR0022 for the evidence and remaining boundaries.

## 2026-09-13 - Preserve earned AAs while deriving usable native ranks

Implemented the first native ownership increment on `feature/aa-ownership`:
load the eligible prefix while preserving full earned counts and charges, retain
earned plus expended spent-point totals on save, and reject repurchases or saves
when ownership is unresolved. Six native controls pass across 32 operations,
including partial/full suspension, a charged AA and malformed saved rows. A fresh
2,787-file build succeeds; all 87 C++ and 324 calculator/evidence tests pass. The clone is clean and its
AA catalog is unchanged. Archived source preserves the frozen five-fix QA proofs
as new source work proceeds.
Gotcha: refund/reset/class-release/charge-consumption and purchase failure paths
still need integration; this increment must not be promoted or activated yet.
No live gameplay settings or server binaries changed. See
`docs/balance/native-aa-owned-core.md` for evidence and remaining gates.

## 2026-09-13 - Reproduce AA ownership accounting across expansion eligibility

Added a clone-only native control using the full unchanged AA catalog. A six-rank
Natural Durability purchase becomes entirely inactive when only its first three
ranks remain expansion-eligible. SaveAA then drops reported spent points from 29
to 5 despite retaining all six earned ranks in the database; the 17-point wallet
does not change. Restoring eligibility and saving returns the 29-point total.
Captured the before evidence and added exact-state regression checks. ADR0021
sets the implementation direction: canonical earned rows plus a separate usable
view, with native purchase/refund/reset/class-release/charge handling required.
No live server, catalog, era or ownership data changed; test candidate 5f61fdd is
still frozen pending activation and owner QA.
## 2026-09-13 - Prepare reversible PoK arrival hub and durable restock

Implemented a guarded content migration for sixteen class spell/song/discipline
merchants, the existing class guide, and five utility services near arrival.
All 1,229 currently stocked items retain their prices and merchant restrictions;
original class levels route the 1,747 listings. Five identical Forgemaster spawns
become one. Full preimages and exact rollback are retained, with occupied-ID,
source-drift, engine, and transaction guards. Player directions now name the hub
and keep camp guidance without exposing operator script commands.

The canonical restock detects the legacy/new layout, stages class stock from the
audited catalog, and commits atomically. Era preflight refuses unreviewed future
catalogs before rules or client settings change. Missing input/guard files and SQL
errors stop the era script. Four planner/migration tests, 14 isolated MariaDB
controls, PowerShell preflight/file-error checks, and seven new plugin assertions
pass. Independent review findings were fixed. See docs/pok/verification.md.

No live SQL, scripts, client files, or zones changed. Placement and client behavior
still require docs/pok/QA.md, an agreed PoK restart, and owner sign-off before main.
The AA ownership branch remains separate. Later expansions require an explicitly
reviewed stock catalog; current preservation is not an expansion provenance audit.

## 2026-09-13 - Plan class-labeled PoK arrival merchants

Added a pure, offline hub planner using the verified original spell-class catalog.
The generated sixteen-merchant proposal preserves all 1,229 current unique scrolls
and item prices; the largest shop has 275 items. Two tests verify coverage, class
routing, prices, and rejection of invalid/unmapped stock. Labels distinguish
spells, songs, and discipline tomes. Proposed placement leaves an open arrival
area; new NPC IDs were checked against the live catalog to avoid pet collisions.
No SQL or zone changes were applied. Guarded migration/rollback, restock integration,
utility consolidation, ground checks, and manual QA remain. See docs/pok/hub-layout.md.

## 2026-09-13 - Show selected classes on demand and after selection

The isolated PoK usability branch adds explicit Primary/Second/Third class slots
on hail and login, #classes and /say !classes, and immediate status after class
selection/release responses. Empty slots are visible. Dialogue now explains earned
skill progression and removes misleading counts and obsolete retention promises.
Lua behavior checks cover all 16 primary classes plus commands/login/delegation;
16 Perl dialogue assertions and the existing canonical-login regression pass.
A read-only audit maps all 1,229 stocked scrolls to the matching original spell
catalog; each class fits one merchant window. Hub placement, vendor migration,
restock integration, and in-game QA remain in progress. No live scripts, NPCs,
merchants, client files, or AA binaries changed. See docs/pok and ADR 0024.

## 2026-09-13 - Build and verify the five server-fix candidate

Clean-built the candidate from 2,787 pinned source files after rejecting the
disk-full build's zero-byte artifact. All 87 C++ tests pass. A diagnostic linked
from the fresh objects reproduces all 24 earlier Vox/Nagafen reports and raw
hashes exactly. The package includes original source, the five-file patch, build
provenance, replay evidence, a checksummed E: executable, and explicit in-game QA.
All 316 tests pass on `dev`. A clean-checkout source-hash discrepancy was resolved
by rebuilding `mob.cpp` from exact committed LF bytes; its object and the complete
zone binary remain byte-identical. The complete source archive and original zone
rollback binary are preserved on E: and verified by checksum.
The clone is clean and its AA tables are unchanged. These are mechanics fixes;
caps, NPC HP, the live AA offering and the active server binary remain unchanged.
See `docs/releases/server-fixes-20260913/README.md` for evidence and remaining gates.

## 2026-09-13 - Finish focused pet shielding comparison

Compared owner Arch Shielding with and without Resist Magic across 36 native
Vox/Nagafen fights at zero, launch maximum, and later maximum AA purchases.
Gear, caps, pet preparation, and combat policy stay fixed. Neither preparation
change consistently resolves the pet build's Nagafen gap, so retain the baseline
and 250/250 caps. The verifier now checks the armor spell declared by the input
and rejects missing preparation buffs. All 315 calculator tests pass, including
the three new shielding tests. Removed an unnecessary full-trace deepcopy from
the missing/duplicate evidence test without weakening its assertions.
See `docs/balance/native-pet-shielding.md`. No live gameplay settings changed.

## 2026-09-13 - Move Docker data to E: and recover the stack

Moved the offline 20 GiB Docker data disk to `E:\Docker\wsl\disk`, verified
matching SHA256 checksums, and retained the original as an E: rollback copy.
A directory junction preserves Docker's existing path. C: now has about 24 GiB
free. Resolved stale runtime socket startup failures; all ten stack containers,
MariaDB, world, login, UCS, and eight zones are running again. Both fail2ban
containers report healthy. No candidate server binary or balance change deployed.
See `docs/ops/docker-data-migration-20260913.md` for verification and rollback;
MariaDB's existing E: bind mount is separate from the saved Docker disk.

## 2026-09-13 - Measure spell damage and healing caps at 300

Ran 162 isolated native Vox/Nagafen fights: damage/heal 250/300, 300/250 and
300/300, each across three builds, zero/launch/later maximum AA allocations and
three seeds. Exact gear, purchases and non-cap initial stats remain fixed. The
launch pet build improves from 0/3 Nagafen wins to 2/3 with both caps 300, but a
deeper caster Vox sample falls to 57.5 seconds. All 18 melee reports remain
identical under damage 300 except for the static cap readout. Healing alone does
not consistently resolve the survival gaps; these are samples, not win rates.

Retain 250/250 as the baseline for targeted pet/encounter work. Higher caps remain
permitted; this experiment does not support a global increase as the current fix.
All 310 automated tests pass. Each temporary cap change restores the exact original
rules; a stale second-cap guard also rolls back the first update. The clone is
empty of synthetic characters and inventory, and original AA tables are unchanged.
No live cap, NPC HP, binary or process changed. See ADR0020 and
`docs/balance/native-cap-sensitivity.md` for the comparisons and in-game QA.

## 2026-09-13 - Keep native owned-AA profiles consistent across rank caps

Corrected the isolated AA-loader candidate to clear stale profile entries and
populate them only after native SetAA succeeds. Five native controls reproduce
three invalid/stale profile cases and verify the correction while preserving
saved rows and the unspent wallet. Two valid controls and 24 legacy/source-gear
boss reports retain identical complete reports and raw hashes.

Added an offline earned-versus-active ownership transition model. All 196
captured purchases and nominal cost 3,155 survive launch/later/launch changes.
A native six-rank restoration control preserves its 17-point wallet without
repurchase. This is not an installed ledger: spent-point accounting, refunds,
resets, class release and charged-AA lifecycle integration remain required.
Candidate cores still are not a final exclusion list or expansion schedule.

All 304 balance tests pass. The full original AA tables are restored exactly and
the synthetic character fixtures are empty. No live data, binaries, rules or
processes changed. Exact compiled source bytes are archived; the tracked AA mirror
uses LF for reproducible checkouts. See ADR0019 and
`docs/balance/native-aa-ownership.md` for evidence, limitations and in-game QA.

## 2026-09-13 - Verify native enforcement of projected AA rank caps

Projected both candidate AA cores into the empty isolated database by disabling
omitted families and terminating retained rank chains. Native catalogs expose
exactly 61/109 ranks while preserving all 23 previously disabled families. All
21 legal build readouts retain their stats and purchases; 14 forbidden purchases
succeed before projection and fail afterward. All 12 maximum-AA Vox/Nagafen
reports match the previous source-gear evidence byte-for-byte.

Backed up both AA tables before changes and restored the complete original dump
exactly after each candidate. A deliberately stale second-table precondition
also rolls back the preceding 1,527 ability updates exactly. All 290 tests pass;
the final synthetic fixture is empty and temporary procedures are removed.
No live data, character purchases, era rules, binaries or processes changed.
This proves the native data-projection path, not a complete AA offering or
existing-owner migration. Source review also flags unchecked SetAA failure after
truncating an owned chain; ownership preservation and activation/persistence QA
remain required. See ADR0018 and `docs/balance/native-aa-policy-projection.md`.

## 2026-09-13 - Preflight expansion AA caps against saved purchases

Added a read-only AA policy compiler that resolves complete native rank chains,
inherited prerequisites and canonical saved first-rank IDs. Captured 1,570
abilities, 6,655 ranks, 2,525 prerequisite rows and 196 purchase rows from PEQ.
The proposed launch/later combat cores compile to 61/109 rank IDs and preserve
every native calculator allocation. Both have closed prerequisites. Ten
character IDs have affected rows; the launch core leaves 163 rows outside the core
and caps six others. These omissions are not a final AA removal list.

Source review confirms unavailable owned ranks are skipped as whole families;
loading does not automatically retain lower ranks or refund points. Repurchasing
can overwrite the canonical saved row. Reports estimate nominal removed-rank
cost only, without authorizing refunds. Missing next-rank rows retain valid
prefixes, matching native loading. Tests cover these identity, chain, cap and
ownership cases plus regeneration from captured evidence; all 279 tests pass.
No live AA access, purchases, rules, binaries or processes changed. See ADR0017
and `docs/balance/aa-policy-preflight.md` for findings and required release QA.

## 2026-09-13 - Measure pet threat policies and resistance preparation

Added optional native Feign Death controls with native cooldown, hate, spell-break
and standing behavior. Nine matched pilots fail to solve Nagafen survival; these
policies remain disabled in the baseline. Separately admitted legal Resist Magic
preparation and measured 36 matched fights with the same gear and AA purchases.
Buff retention is verified on the owner and three pets. No Nagafen sample wins;
Vox results vary by AA stage. Extra preparation changes native timing/RNG, so the
small sample does not establish that the buff causes worse survival.

All 263 tests pass. Twelve baseline reports, six threat pilots and six further
baseline reports retain identical raw hashes across diagnostic build changes;
three resistance pilots reproduce exactly in the full matrix. All four earlier
combat candidates remain, with only the diagnostic runtime object changed.
The isolated fixture is empty after bounded synthetic-reagent cleanup. No live
restart, binary replacement, cap/HP tuning or AA-access change occurred. See
ADR0016 and `docs/balance/native-pet-threat-and-preparation.md` for evidence and
explicit RoF2/in-game QA. Expansion-specific AA pools remain proposed combat
cores; complete availability and purchased-rank enforcement are still pending.

## 2026-09-13 - Measure gear-source dependence across legal AA pools

Added 108 matched Vox/Nagafen fights after removing Behemoth 56182 as a gear
source, retaining items with another captured source. Re-optimized the same
shield/augment objectives and added 36 Monk cloak/haste comparisons. Gear and AA
purchases regenerate independently; all builds still hit the 250 spell/heal caps,
but lower HP/mana and other gear changes materially weaken outcomes. The pet
launch maximum loses all three Nagafen samples; its deeper maximum wins one.

A failed case exposed a diagnostic death-sampling limitation: native HP reached
-500, then a pending heal left +732 at the end of the same pulse. Optional native
death-callback evidence now proves the terminal result and reports minimum HP as
zero. The focused replay otherwise matches exactly; this is a diagnostic adapter
change, not a live death/corpse fix. All four previous combat candidates remain.

All 144 comparisons and 243 tests pass. Twelve legacy reports keep identical raw
hashes, and 90 overlapping earlier reports match after removing the new evidence
fields. The isolated database is empty after removing two synthetic reagent rows.
No live content, binaries, caps, NPC HP or AA access changed. See ADR0015 and
`docs/balance/native-source-gear.md` for results, limitations and explicit QA.

## 2026-09-12 - Correct acquisition and utility-AA baseline assumptions

Captured read-only source evidence for the level-72 Behemoth, Magician epic
quest/spell chain and Ancient Attunement. Behemoth is present in live Classic
content; the isolated clone omits spawn2 and cannot establish spawn absence.
Its rewards remain conditional until level-50 acquisition is demonstrated.

Future acquisition captures now include Orb of Mastery and the ornate exchange
alongside the legacy Fire staff forge mapping. The observed epic chain depends
on Kunark zones, and an Ascended orb row is absent. Existing frozen captures and
combat gear remain unchanged. A regression covers the indirect scroll reward.

Corrected the AA report's unsupported PoK-gate claim: spell 99001 has native pet-
summoning effect 33. The setup script's unrestricted teleport_zone lookup can
select pet spells. This free AA was never activated by the fight controllers;
existing combat evidence remains valid, while recall needs a separate repair
and QA. No live content, binaries or access policy changed. See
`docs/balance/acquisition-identity-audit.md` and its captured evidence.

## 2026-09-12 - Compare shared capped AA pools across combat roles

Added two explicit global combat-core candidates, intersected with native held-
class eligibility for caster, monk and pet profiles. The launch pool exhausts at
135/141/165 points; the deeper pool at 261/288/306. Requested budgets and legal
maximums share evidence only when purchased ranks are identical. The explicit
free baseline removes placeholder/Alaran grants while retaining Nightcap travel
and interface AAs; native zero-spend HP drops exactly 20 for each profile.

All 108 native fights and the 229-test suite pass verification. Caster and melee
win all sampled cases; the pet launch maximum has two Nagafen wins and one timeout,
and its deeper maximum wins all three. The cross-role gap remains substantial.
These are diagnostic combat cores, not a complete release AA offering or live
removal. Utility/support review, obtainable BiS and final tuning remain open.
See ADR0014 and `docs/balance/native-aa-release-candidates.md` for policies,
limitations, regeneration commands and explicit future enforcement/QA requirements.

## 2026-09-12 - Respect native belly casting in pet balance measurements

Both captured dragons have ranged-spell immunity: native resistance rejects spells
cast outside melee range. The pet-support diagnostic now offers a native-range
approach, preserving the old 80-unit controller as a matched comparison. It also
records movement requests interrupted by newly acquired native fear/AI control,
without accepting ordinary failed movement. Thirty corrected fights pass; all 65
legacy support, command, ownership and caster/monk reports remain byte identical.
The focused 217-test suite passes. See `docs/balance/native-pet-belly-casting.md`.

This corrects the player strategy and evidence, not the dragons. Live NPCs, spells,
AA access and binaries were not changed. Previous ranged-owner results are weak-
strategy controls and must not be used as the pet build's full-power baseline.

## 2026-09-12 - Measure native pet support across AA progression

The isolated balance diagnostic now prepares and supports MAG/NEC/SHM pets with
native spells, sitting recovery, actual recast timers and eight fixed combat gems.
Matched Vox/Nagafen cases cover requested0/100/200/500 points and unrestricted all,
reporting actual costs. Preparation validation caught native buff replacement and
recast rejection; accepted cast requests are not assumed to have landed. Boss HP
ledger validation now clamps negative terminal HP consistently with damage totals.
See ADR0013 and `docs/balance/native-pet-support.md` for evidence, limits and QA.

The final release maximum remains a curated expansion AA pool; unrestricted all
is only a stress test. This controller does not establish obtainable full BiS,
optimal pet play or final balance. Live binaries, AA availability, NPC HP and spell
caps were not changed. Reproduce with all four native candidate source flags.

## 2026-09-12 - Give extra pets native attack orders and measure pet boss combat

Reproduced out-of-range, command-spam damage from extra pets: the broadcaster called
`Attack` directly, bypassing normal orders. It also ignored attack/qattack when no
primary pet existed. The candidate `client_packet.cpp` now shares the native order
path across owned pets. Eight command controls cover legal/distant targets,
repeated input, extra-only pets and primary-only regression. Four native pet-only
Vox/Nagafen fights now exercise movement, aggro and pet deaths. A native boss HP
ledger accounts for damage missing from distant client packets without double
counting nested damage calls. See ADR 0012 and `docs/balance/native-pet-commands.md`.

Build the isolated diagnostic with all four candidate flags, including the new
`--client-packet-source`. Optional candidate-object reuse checks source/object/
flags/link hashes; it does not establish fresh full-source parity. No live server
change or numerical tuning was performed. Owner support rotations, other pet
commands/persistence, gear acquisition and expansion AA policy remain outstanding.

## 2026-09-12 - Preserve registered multiclass pet ownership

Native MAG/NEC/SHM controls exposed extra pets disappearing after summoning:
`Mob::GetOwner` and `GetOwnerOrSelf` accepted only the primary pet ID, despite the
existing extra-class registry. The candidate now recognizes registered extra pets
and preserves native orphan detach/depop behavior. Fifteen candidate controls pass
against thirteen recorded pre-fix cases (ten failures); eight caster/monk encounter
reports remain byte identical. The new pet diagnostic uses real summons, reagents,
NPC processing, buffs and explicit AA allocations. See ADR 0011 and
`docs/balance/native-pet-ownership.md` for evidence and in-game QA.

Candidate-only: no live restart, replacement, AA removal, cap or NPC changes.
Build the diagnostic with all three spells/attack/mob candidate flags. Pet commands,
combat, death/persistence, gear/focus and curated release pools remain unverified;
surviving pets do not establish final balance. Native reagent tests temporarily
created two clone-only synthetic inventory rows; verified and cleaned afterward.

## 2026-09-12 - Correct held-class weapon damage and measure native monk combat

The first WAR/CLR/MNK pilot exposed a base-class-only swing gate: legal held-Monk
Tonfa 662038 equipped successfully but all 632 normal swings were immune. The source
candidate now uses the existing held-class equip helper for player weapon damage,
preserving slot/level/race checks and non-player/bot logic. Fifteen native weapon
controls pass; the same pilot now deals ordinary weapon damage and kills Nagafen.

Added a native packet-driven Flying Kick/Tiger Claw plus melee/self-heal controller.
Sixty matched weapon-layout/AA/control encounters pass, including six byte-identical
caster regressions. The verifier distinguishes ordinary weapon hits from monk skills
and accepts native avoided enemy swings as evidence of combat, without requiring
incoming damage. All 180 Python tests pass. See docs/balance/native-melee.md and
ADR 0010 for evidence, limitations and explicit QA. The corrected attack.cpp is only
in the isolated diagnostic; no live binary replacement, restart or numerical tuning
was performed. Low-AA melee rotations and the unrestricted AA ceiling still require
balance review alongside pet/DoT play and per-character spell ownership.

## 2026-09-12 - Include socketed gear and expanded weapon choices in balance evidence

The isolated native harness now equips real augments with socket/lore/level checks
and exports observed equipment. The generator includes recommended-level stat
penalties, shield/dual/two-hand layouts, existing drop augments and alternative
stat objectives. Ninety native loadouts, four augment-stat controls, nine invalid
loadouts and 102 prepared boss runs cover gear and fixed-gear AA comparisons.
Six legacy report hashes and six repeated zero-spend encounters remain identical.
All 175 Python tests pass. See docs/balance/native-expanded-gear.md for scope and QA.

The stronger candidate gear materially improves sampled Vox outcomes. Proposed
114/201-point AA cores preserve longer fights than the unrestricted ceiling;
removing Twincast/Frenzied alone is insufficient. Behemoth loot acquisition, quest
and crafting challengers, other combat archetypes and expansion policy enforcement
remain open. Full BiS/final balance are not certified. No live item, AA, era, cap,
NPC or binary changes were made.

## 2026-09-12 - Measure AA rank pools and burst-family exclusions

Added explicit diagnostic AA rank-cap and exclusion policies with native legal
purchase closure, actual spending and dependency-removal audits. Fifty-four
fixed-gear prepared boss encounters compare a 114-point early combat core, a
201-point deeper core, and unrestricted builds without Twincast/Frenzied families.
The two-family removal alone still leaves a large power ceiling; the small core
sometimes produces long Vox fights. No production AA has been disabled and no
era rule changed. See docs/balance/native-aa-pools.md for evidence and release QA.
All 164 Python tests pass; six zero-spend controls retain identical combat and
twelve exhausted-budget controls match their completed-pool fights exactly.

## 2026-09-12 - Include native preparation in boss baselines

Added ordered native self-buff casts, mana costs and optional full sitting recovery
before the diagnostic spawns its opponent. Client posture packets establish actual
sitting/standing; the appearance-only Sit helper does not. Buffs, resources and
cooldowns carry through a continuous clock into combat. Thirty fixed-gear prepared
Vox/Nagafen encounters cover all five AA budgets and verify the five-buff stack.
See docs/balance/native-preparation.md and ADR 0009. Full BiS and release balance
remain open; no production deployment, live tuning or service restart occurred.
All 160 Python tests pass; ten no-preparation controls reproduce their native
reports exactly and four invalid-preparation inputs are rejected natively.

## 2026-09-12 - Keep AA self-buffs on native timers (isolated candidate)

Excluded direct AA spell IDs from the long self-buff override in the reviewed
server mirror. Tenacity and Twincast now retain native duration/focus rules;
ordinary Arch Shielding and Resolution preparation buffs retain long durations.
Eighteen native lifecycle controls and 154 Python tests pass. Maximum-rank
Tenacity still kills the low-health unhealed control, so the timer correction is
not a complete sustain fix. The diagnostic supports compiling a separate spells
candidate without replacing production objects. No live deployment or restart.
See docs/balance/native-aa-duration.md and ADR 0008 for evidence, scope and QA.
All 144 matched boss encounters pass movement checks; the 54 no-activation cases
are byte-identical. Two 200-AA Vox/Tenacity outcomes change from wins to losses.

## 2026-09-12 - Measure native activated AAs in the balance diagnostic

Added timed native AA lifecycle controls and explicit once-per-fight burst/sustain
policies for the fixed-gear 0/100/200/500/all matrix. Fourteen lifecycle controls
and 144 Vox/Nagafen encounters completed. The controls expose purchasable Celestial
Regeneration failing the level-50 target buff gate, its shared timer with Tenacity,
and permanent self-buff logic extending Tenacity's damaging tail and Twincast's
duration. Divine Arbitration has no solo resource effect. Buff disappearance is
not counted as spent Twincast charges. These are baseline findings, not gameplay
fixes or full BiS certification. No production binary, live tuning, service restart
or branch promotion occurred. See docs/balance/native-activated-aa.md and ADR 0007.
All 144 native reports replay identically; the 14 lifecycle controls and 52 prior
passive-only encounters reproduce byte for byte. Movement checks pass for all
144 cases, 149 Python tests pass, and isolated player tables remain empty.

## 2026-09-12 - Restore player pursuit in native encounter diagnostics

Added optional mesh-guided return to melee through normal client position/history
packets, with speed bounds, collision checks, and stops for casting, healing and
control effects. The prior 900-second Vox timeout now ends in a 271.30-second kill
with identical stats and AAs. The 52-case pursuit matrix validates 954 position
updates with no failed paths; disabling pursuit reproduces all previous encounters
byte for byte. Fixed missing movement-history handling in the mock transport and
added an explicit failure guard for unmodeled world notifications. Seven isolation
checks and 137 Python tests pass. Client physics parity, preparation, activated
AAs and full BiS remain open. No production binary, live tuning or service restart
occurred. See docs/balance/native-player-pursuit.md and ADR 0006.
The full pursuit matrix also replays identically; isolated player tables remain empty.

## 2026-09-12 - Expand gear acquisition and run AA boss progression controls

Captured quest, merchant, global-loot and recipe candidates with source restrictions;
unresolved prerequisites remain explicit. Native controls found that the previous
gear search excluded a usable recommended-level-62 haste ring. At level 50 its
HP/mana scale, its full 41% haste applies, and a 36% haste cloak adds no extra haste.
One hundred gear/AA controls and 52 candidate Vox/Nagafen encounters now validate
fixed gear across 0/100/200/500/all AA and alternative finite-budget allocations.
The encounters exercise native purchased bonuses without activated AAs or prep
buffs. Three seeds per AA case are exploratory; a Vox timeout also exposes the
controller's missing return-to-melee movement. Full BiS and tuning remain open.
All 52 encounters replay byte-for-byte; 134 Python tests pass. The isolated
database still has zero accounts/characters. No live tuning, restart or branch promotion occurred.
See docs/balance/gear-aa-encounters.md and acquisition-candidates.md for evidence.

## 2026-09-12 - Run accelerated native boss encounter prototypes

Added a diagnostic-only packet sink, completed mock-client loading state, and a
unified virtual clock for native combat and persistent cooldowns. Native self-cast,
regeneration, damage, boss AI, fear movement, Vox healing, and terminal handling
now run against the isolated content clone and copied maps. Three short controls
and three terminal runs replay identically. Fixed the fixture's unloaded-zone
state, which initially prevented NPC target selection; checks reject idle bosses.
Verified weapon melee separately because the caster candidate holds a non-weapon.
120 Python tests and seven isolation guards pass. These remain simple zero-spent-AA
candidate runs, not full BiS/activated-AA balance conclusions. No live tuning,
restart, or branch promotion occurred. See docs/balance/native-encounter-runtime.md.

## 2026-09-12 - Resolve native direct-spell actions and preserve sampled outcomes

Sampled 120 player actions across the 24 AA candidates using native Vox/Nagafen
types, direct spell formulas, resists, focus, crits, specialization, mana costs,
and cast times. The 491,520-sample run replays byte-for-byte with an isolated
GNU linker seed hook; native RNG algorithms and production binaries are unchanged.
Casters have explicit full resources and no active buffs. Added joint outcome
support to the event simulator, preserving raw mana start gates, discounted
completion costs, interruption behavior, and already-resolved damage/healing.
Two 2,000-trial inert-target controls match exact scheduling/accounting and damage
expectations. 114 Python tests pass; native AA/resource/isolation checks still pass.
These are direct-action and integration controls, not full BiS boss fights.
No live tuning or restart occurred. See docs/balance/native-spell-resolution.md.

## 2026-09-12 - Verify native AA progression inputs

Added explicit 0/100/200/500/all purchase allocations and two finite-budget
spending policies for the three level-50 Ascended candidate sets. The isolated
native engine accepts all 7,868 purchase steps across 24 scenarios; HP/mana agree
with the calculator. Native post-purchase catalogs confirm no omitted legal
all/free ranks. Six illegal-purchase and seven isolation controls pass.
All-purchasable totals are 13,738 / 13,261 / 13,288 points, excluding grant-only
rewards and blocked prerequisites. Zero spent includes the same free ranks at
every stage (20 flat HP in this data). Corrected the diagnostic's base-class-only
skills and invalid specialization assumptions; trained held-class ceilings still
require attainability QA. 106 Python tests pass. These are resource/input results,
not full BiS fight outcomes. No live tuning, restart, or promotion occurred.
Details, exact allocations, and evidence: docs/balance/native-aa-stats.md.

## 2026-09-12 - Resolve equipped candidate stats with the native engine

Built a separate native diagnostic using the existing mock Client constructor,
legal Human creation allocations, synthetic multiclass rows, maximum eligible
skills, actual item instances, and CalcBonuses. Ran all 12 candidate sets; their
HP and mana match the previously verified calculator with zero mismatches.
The isolated database has 237 table schemas, copied content, and no account or
character rows. Its user, runtime, and shared memory are separate from live PEQ.
Seven preflight checks reject live/unsafe configurations before engine startup.
The diagnostic pins reused native objects and its executable; this is not a fresh
full-source rebuild or proof of every running zone's binary. Quest hooks, purchased
AAs, active buffs, full combat BiS, and complete boss outcomes remain pending.
The Python suite passes 98 tests. No live tuning, restart, or promotion occurred.
Evidence and observed stats: docs/balance/native-equipped-stats.md; ADR 0005.

## 2026-09-12 - Resolve boss spell dependencies and verify spell arithmetic

Expanded the frozen content snapshot to include actual boss lists and immediate
parents, referenced item effects and recourses, plus Human creation allocations.
This fixes an incomplete Phinigel list and the old spell-ID ceiling that omitted
Vox's inherited later-ID heals and buffs. Missing dependencies now fail validation.
The v2 snapshot contains 1,373 spells, five lists, and 172 entries; older fixtures
remain unchanged so their recorded controls stay reproducible. Native extracted
C++ agrees on 12,224 effect/duration cases and 301,500 ordinary resist rolls.
Added explicit engaged NPC spell selection and 94 passing Python tests in total.
Selection still requires runtime integration, stacking/readiness state, and
explicit equal-priority ordering. These are not complete boss fight results.
See docs/balance/spell-resolution.md. No live rules, NPCs, or processes changed.

## 2026-09-12 - Add seeded encounter engine and native melee validation

Added an offline event simulator and CLI for resolved diagnostic profiles:
casting, healing/overheal, mana exhaustion and regeneration, cooldowns, fear
interrupts, periodic effects, NPC melee rounds, deaths, kills, and timeouts.
Compared hit/DI/mitigation math with actual C++ in 5,000 cases: zero mismatches.
Ran 1,000 Nagafen melee controls against an artificial defender; mean damage
agrees with the exact discrete expectation within 0.446 standard errors.
The controls explicitly omit full boss AI/spells and are not BiS fight results.
Full character/AA/buff/effect adapters and Vox/Nagafen balance sweeps remain open.
Recorded the active live-rounds rule and legal Human Warrior creation allocation.
No live tuning, player changes, restarts, or promotions occurred in this slice.

## 2026-09-12 - Verify calculator HP and mana against the engine

Added RoF2/SoD resource calculations for best held-class HP/mana, stamina and
casting-stat breakpoints, item/heroic contributions, percentage HP, and flat
bonuses. A database-free C++ oracle extracts eight actual engine functions and
compares four outputs across 2,896 boundary/random cases: zero mismatches.
Eleven additional unit tests cover resource arithmetic and missing-input failures.
Heroic mana still follows the base class in this build, even when a held caster
class supplies base mana. The calculator preserves that behavior. Resolved
AA/buff/item effects, character-creation allocations, and encounter simulation
remain pending; these checks do not certify a complete character or boss result.
No production source, binaries, rules, or player data changed in this slice.

## 2026-09-12 - Start source-verified offline balance calculator

Added a Python port of the item spell/healing contribution and compared it with
the actual C++ function in 2,792 cases: zero mismatches. Added a hashed, non-player
Classic-zone content snapshot and an exact weighted gear assignment solver with
class/race/deity/level/slot/lore constraints. Thirty-eight unit/relational checks
pass. Twelve candidate builds cover three class combinations and four tiers;
these are not yet full combat BiS or encounter outcomes. Full boss AI, combat,
AA/buff/effect modeling and additional acquisition paths remain in progress.
No spell/healing caps, mob values, or player records were changed by this slice.

## 2026-09-12 - Reconcile source/data baseline and restore level-1 AA XP rule

Integrated existing dev, accepted main QA history, and the already-deployed
spell/healing scaling feature in an isolated reconciliation branch. Captured the
previously unmirrored loot hook and RoF2 wire files. Added a read-only drift checker
with failure-detecting C++ test summary validation: 43 source files match, 87 C++
tests pass, and all 184,920 existing worn tier/epic spell-stat stamps match.
Restored the missing `Character:AAExpMinLevel=1` row using its existing SQL after
a verified full backup. Runtime reload is pending because a character is marked
in-game. Recorded the owner's solo-preferred balance requirement in AGENTS.md.
Evidence, rollback, limits, and focused QA: `docs/balance/reconciliation.md`.

## 2026-09-08 - SpellDmg/HealAmt master output scaling

Made SpellDmg and HealAmt the caster/healer output dials. Flipped five Spells
rules (`ItemExtraSpellAmtCalcAsPercent`, `FlatItemExtraSpellAmt`,
`IgnoreSpellDmgLvlRestriction`, `DOTsScaleWithSpellDmg`, `HOTsScaleWithHealAmt`)
so these stats apply as uncapped percent-of-base multipliers on spells, heals,
DoTs and HoTs. Extended `gen_loot_tier` in `tiered_loot_setup.sql` with a
`p_spellstat` param that ADDS flat SpellDmg/HealAmt to worn tier gear
(+5/+12/+20 Polished/Exalted/Ascended, mirrored to Ascended epics) — most
Classic-obtainable worn items are 0 here, so they get exactly the flat stamp,
while the minority that already carry these stats get base*offn + stamp (bounded
by the item cap below). Soloability is
tuned via `Character:ItemSpellDmgCap`/`ItemHealAmtCap` (250 = +250% at cap).
Rules + SQL only; no C++, no client change; NPCs and melee output untouched.
Gotcha: heroic INT/WIS can also feed these stats via `Heroic*Increase*Multiplier`
(0 today) — verify vs the cap before enabling. Reverse: rules → false, re-run the
generator with `p_spellstat` 0.

## 2026-09-08 - Held-Monk combat QA PASS (#10)

In-game QA of the six held-Monk attacks (G006) passed on the cleaned Monktest
fixture with the activation build `8F8DF8B2…`: all six visible/assignable via
Actions -> Abilities, animating and damaging the arena dummy with correct reuse,
and Kick single-routed (no double). Held-Shadowknight Harm Touch was additionally
spot-checked and fired. Recorded in `docs/qa/2026-07-29-held-monk-combat-qa.md`;
audit G006 held-Monk slice marked verified (generic Kick/Frenzy still open), G002
noted with the Harm Touch spot-check.

## 2026-09-08 - Clean Monktest QA fixture before held-Monk activation QA (#10)

Prepping the pending G006 in-game QA. Verified the deployed dev client
`dinput8.dll` is the activation build (SHA-256 `8F8DF8B2…F1B26D`) and that
Monktest (char 19) is otherwise pristine — 60 skills, 0 mismatches, Water Flask
in slot 23. The fixture Check flagged one stray `character_alternate_abilities`
row (Ancient Attunement, aa_id 22200 rank, value 1) granted during earlier
testing; a stray combat AA would confound the Kick single-routing step. Backed
up PEQ (`backups/peq_20260908_093915.sql.gz`, 44 MB) and deleted that one row
while the character was camped (`ingame=0`). Post-state: 0 inherited combat rows,
aa_points 0. Character is parked in the Arena (zone 77) rather than the pristine
PoK (202), which is where the QA runs, so the fixture Check still reports that
zone as a benign mismatch. Re-grant if needed: char 19, aa_id 22200, value 1.

## 2026-09-08 - Complete the player-facing class-gate audit coverage (#10)

Finished the Phase 0 gate audit (`docs/audits/multiclass-class-gates.md`), the
last open item in the Ready queue and the gate that blocks the remaining Phase 2
gameplay slices. No code or DB changes — audit/doc only.

Expanded the former G018 "inventory" row (581 → re-baselined 552 zone `*.cpp`
accessor matches) into per-symbol rows G018.1–G018.13 across `attack.cpp`,
`spell_effects.cpp`, `effects.cpp`, and `bonuses.cpp`: stat softcaps/ATK caps
(best-of held), hand-to-hand and melee damage/crit/frenzy (additive), defensive
gates, heroic caster mana, the `IS_CLASS_*` spell-restriction conditionals, focus
eligibility, and SK/Paladin procs; LDoNTreasure/body-type/banker checks and
group-exp base class stay non-player/chassis.

The exhaustive sweep surfaced three player capabilities no earlier row owned,
all still primary-class only: G019 Tracking (`GetClassTrackingDistanceMultiplier`),
G020 bind-wound class bonuses, and G021 spell/discipline cast-scribe-learn
resolution (mismatch — blocks the Phase 2 spell/discipline slice). It also
confirmed pet/familiar summon, scroll memorization, and Bard mana-regen are
already multiclass-aware (regression-guard only), while tome learning and the
generic cast-level lookup are not. A coverage-reconciliation table maps all 552
accessors to a row or non-player/scripting/identity bucket; zero player-reachable
gates remain unmapped. Rows stay **open**; "complete" here means coverage, not
implementation.

## 2026-08-02 - Route held-Monk hotbuttons through stock combat submission (#10)

Corrected the remaining RoF2 activation failure for the six held-Monk attacks.
Manual QA proved the buttons were visible and usable-looking, but clicking them
did nothing; Feign Death still worked because it has a normal
`CharacterZoneClient::UseSkill` handler. Exact-client disassembly showed that
RoF2 deliberately maps Bash, Kick, Frenzy, and the five named Monk strikes to
an empty `UseSkill` dispatch case. Their native path is the separate
`EQPlayer` special-attack submitter that constructs `OP_CombatAbility`.

The DLL now redirects the type-9 hotbutton activation call only for Dragon
Punch/Tail Rake, Eagle Strike, Flying Kick, Kick, Round Kick, and Tiger Claw.
Those six use the stock target, animation, packet, and reuse path; every other
skill still calls stock `UseSkill`. The submitter's one primary-class
`HasSkill` call has a dedicated held-Monk fallback that accepts only those six
skills and only when the server-delivered value is positive. The stock
post-submit reuse sequence is preserved, and EQEmu remains authoritative for
held-class membership, current-level caps, targets, range, timers, damage, and
skill-ups.

Both call sites, the stock submitter, its stock `UseSkill` caller, and the reuse
sequence are pinned by the exact-client regression. The two runtime redirects
are dependency-ordered; failure of the activation redirect performs a verified
rollback of the execution predicate. The reviewed x86 build was deployed to
the development RoF2 client with SHA-256
`8F8DF8B2B020486C32ABF8ACF6CEA37C194BFE89D29B762ED833E1C650F1B26D`.

## 2026-08-02 - Enable held-class skill hotbuttons and activation (#10)

Completed the RoF2 client path from an assigned held-class skill to its server
submission. After the Actions picker correction, a Cleric-primary Monktest could
assign Monk attacks but each hotbutton was rendered **Not Usable** and
`CharacterZoneClient::UseSkill` rejected it before sending a packet.

The exact-client DLL now redirects two additional, narrowly scoped calls. The
`CHotButton` refresh call uses the positive server-delivered skill predicate for
presentation. The `UseSkill` call uses an integer-valued accessor that preserves
the positive stock adjusted value and otherwise falls back to the raw profile
value. The execution correction must apply before the presentation correction
is allowed, preventing a usable-looking button that the client cannot submit.
All later client state, target, and reuse checks remain stock, and the server
remains authoritative for authorization, timers, damage, and skill-ups.

Both original calls and the stock adjusted-skill entrypoint are pinned by the
exact-client regression. A shared single-call patch helper rechecks immediately
before writing, verifies writes and rollback, requires page-protection
restoration, and does not overwrite a concurrent modifier when no write was
attempted. The reviewed x86 DLL was deployed to the development RoF2 client
with SHA-256
`B8839305CFC5259365DD7268A19831115BD7922ECAAD4F66A00EFF1CD95CA845`.

## 2026-07-29 - Expose server-granted skills in RoF2 Actions (#10)

Corrected the RoF2 **Actions -> Abilities** selector for true multiclass
characters. The client receives Monktest's positive Monk skill values but
`CSkillsSelectWnd::SetTypesToDisplay` calls
`CharacterZoneClient::HasSkill`, which clamps those values through the primary
class's skill cap and hides them from a Cleric-primary character.

The exact-client DLL now redirects only the selector's two `HasSkill` call
sites. Stock-valid skills retain stock behavior; a stock-negative result is
accepted only when the server-delivered base skill is positive. The executable
size/hash, both original call signatures, `HasSkill`, and `GetBaseSkill`
entrypoints are pinned. Writes are rechecked, verified, rolled back on failure,
and require executable-page protection restoration. This correction affects
presentation only; the server remains authoritative for held-class
authorization, reuse timers, targets, damage, and skill-ups.

The reviewed x86 DLL was deployed to the development RoF2 client with SHA-256
`E5B39B38B4046E46C8B9CE58C3FE08872D490B80F72663B1232AD75F34069BDD`.

The first in-game retest still produced an empty picker even though the runtime
log proved both selector hooks were active. Added bounded diagnostics for the
seven granted Monk skills so a picker invocation records the stock predicate,
raw server-delivered value, and the client's activated/combat classifications.
That trace showed every replacement predicate raising a guarded exception. The
initial implementation had mistaken RVA `0x00042110` for the raw accessor; the
verified `CharacterZoneClient::GetBaseSkill` entry is RVA `0x00049C80` and uses
an unusual two-stack-argument ABI (`ret 8`). Corrected and pinned the symbol,
entry bytes, function type, and call shape. Diagnostic logs now permit live
shared reads and remain bounded to the seven Monk skills. The corrected build
is deployed with SHA-256
`93353758DAEA62D6038DE2DC20582AB8BE1902F229D4620442301022F2CF96C5`.

## 2026-07-29 - Unlock the RoF2 combat-ability window chassis (#10)

Added a fail-closed `eq-client-dll` correction for the exact RoF2
`CCombatAbilityWnd::CanShow` base-class table. Stock RoF2 disables the entire
window for seven pure-caster primary classes, including Cleric, even when the
server has granted valid held-Monk skills. The guarded patch changes only those
seven in-memory table bytes after the executable size, SHA-256, and complete
stock signature match; unknown binaries or tables already changed when checked
remain untouched.

The write now snapshots and rechecks the table, verifies rollback independently,
requires executable-page protection to be restored, and rolls back if
protection restoration fails. The exact-client regression pins both table
states and the required safety paths. The server remains authoritative for
learned skills and submitted combat abilities. The reviewed x86 DLL was
deployed to the development RoF2 client with SHA-256
`209E99A97B8F0A6494B554862A9C9A524784EC8CA535C9C2C33E44AC23052726`.

## 2026-07-29 - Read the login banner from canonical multiclass state (#10)

Fixed `global_player.lua` reporting `Monktest` as Cleric/Bard even though
`character_multiclass` correctly held Cleric/Shadowknight/Monk. The login
banner was the last reader of obsolete `mc_class2`/`mc_class3` quest globals;
EQEmu's complete QA-character copy had inherited Darth's stale `mc_class2=8`.

The banner now reads the already-loaded canonical C++ slots through
`GetClass2()` and `GetClass3()`. Added a static regression that rejects legacy
global reads in `event_connect`, and tightened the fixture to remove and reject
obsolete multiclass globals. Monktest's copied Bard global was removed without
changing its canonical class row. The fixture now retains one Water Flask in
General Slot 1 because EQEmu reports a database inventory-load error when a
character has zero inventory rows; the item is unequipped and combat-neutral.

## 2026-07-29 - Create combat-neutral Monktest QA fixture (#10)

Added a guarded, idempotent `Check`/`Apply`/`Rollback` tool for the authorized
`Monktest` character. It uses EQEmu's transactional character-copy path, then
asserts and atomically configures character ID 19 as a level-50 Human
Cleric/Shadowknight/Monk on account `admin` in Plane of Knowledge. Exactly 60
eligible held-class skills are granted to their current level-50 caps.

The first complete copy (ID 18) exposed 63 inherited Paladin AAs and five buffs,
so it was recoverably retired and the fixture was tightened. The final character
has zero inherited AAs, buffs, auras, disciplines, spells, inventory, or timers,
making combat results deterministic. Rollback soft-deletes and renames only an
exactly matching fixture; unexpected characters fail closed. A verified
46,342,038-byte PEQ backup was taken before application.

## 2026-07-29 - Authorize held-Monk combat abilities (#10)

Changed `OPCombatAbility` to resolve its current-level skill cap across every
held class instead of consulting only the primary class. A held Monk can now
submit the six stock Monk attacks once their native cap is positive: Flying
Kick, Dragon Punch, Eagle Strike, Tiger Claw, Round Kick, and Kick. Monk Kick
is excluded from the generic Kick branch so it executes exactly once through
`MonkSpecialAttack`.

Added a pure authorization helper and table-driven positive/negative coverage
for all six attacks, premature unlocks, characters without Monk, and unrelated
Frenzy packets. The ignored Akk Stack source overlay is reproducible through a
fail-closed, SHA-256-pinned application script; it refuses unknown upstream or
partially modified `special_attacks.cpp` inputs. Berserker Frenzy rounds, other
held-class Kick routes, and RoF2 combat-button visibility remain separate work.
The complete test executable exits 0 with 87 tests and all 10 skill-policy
tests passing. The full zone target built cleanly; all eight restarted workers
are newer than the rebuilt binary, loaded the canonical 58,359 skill caps, and
reported no fresh startup errors.

## 2026-07-29 - Prove retained-class cleanup on class release (#10)

Added a static release regression that verifies the multiclass database slot is
updated before the live mask reload, released-class-only AAs and skills are
removed, shared skills keep values within the best retained cap, over-cap values
are clamped, and retained AAs are repersisted and resent in the correct order.
Updated stale comments left from the removed global skill-cap widening.

## 2026-07-29 - Enforce held-class trainer authorization atomically (#10)

Replaced legacy max-level multiclass trainer widening with current-level,
held-class eligibility. Trainer sessions now accept only a held class unless
the existing cross-class-trainer rule is enabled, display only caps available
at the character's current level, and reject premature or capped requests.

Training requests now validate skill points, native unlock level, effective
held-class cap, stock trainer limits, and carried currency before mutation.
Zero-valued skills open at exactly value `1`; unaffordable requests no longer
raise a skill before payment fails. Pure tests cover held/non-held trainers,
early unlocks, caps, points, and funds, while a static integration regression
locks the packet-handler ordering. The rebuilt test executable exits cleanly
with all 9 skill tests passing, and all eight restarted zone workers loaded the
verified binary plus the canonical 58,359-row skill-cap baseline.

## 2026-07-29 - Seed native multiclass skills across the character lifecycle (#10)

Added one authoritative C++ reconciler that evaluates native eligibility across
the character's held classes and grants each newly unlocked skill at value `1`.
It runs during zone-in, immediately after secondary/tertiary class adoption,
and on level-up before quest events. Existing nonzero skills remain unchanged,
and stock acquisition-only skills remain excluded.

Removed the duplicate Lua level-up seeding loop and exposed the same reconciler
to the production Perl adoption plugin. A static lifecycle regression verifies
all call sites and ordering. The full zone build and 84-test CppUnit target pass;
all eight restarted zone workers use the rebuilt binary and load the canonical
58,359-row skill-cap baseline.

## 2026-07-29 - Add deterministic native skill seed selection (#10)

Added a table-driven seed-candidate collector that applies the approved
acquisition policy, native unlock level, current cap, and current character
value without mutating character state. CppUnit coverage proves ordering,
threshold behavior, idempotence, stock-acquisition exclusion, and auto-granted
class tradeskills. This is the tested decision seam for the upcoming Client
lifecycle reconciler.

## 2026-07-28 - Apply canonical skill-cap repair to live PEQ (#10)

Stopped every gameplay process, reran the exact canonical preflight, completed a
transaction-rolled-back live dry run, and then removed exactly 16,090 legacy
widening rows. Live `skill_caps` now contains the 58,359 canonical rows with
zero live-only rows, zero canonical-only rows, and zero cap mismatches. The
original rows remain in `skill_caps_epic10_removed`, and the verified full
pre-migration backup remains retained.

The current server loads skill caps directly from PEQ at world/zone startup; its
legacy `shared/skill_caps` file is no longer generated or consumed. A full
launcher-managed shared-memory refresh and process restart completed. The new
world and all eight zone workers logged that they loaded 58,359 skill-cap
entries, with no recent world/zone errors.

## 2026-07-28 - Rehearse reversible legacy skill-cap repair (#10)

Added a fail-closed `skill_caps` repair tool backed by the pinned 16,090-row
canonical diff. It rejects unexpected target/canonical state, retains every
removed row in `skill_caps_epic10_removed`, supports transaction-rolled-back dry
runs, and requires an explicit override before it can target live PEQ.

Restored the verified 46,304,776-byte live backup into an isolated no-host-port
MariaDB container. Integration testing proved: incorrect preconditions cause no
mutation; dry-run removes and rolls back exactly 16,090 rows; apply produces an
exact 58,359-row canonical match; rollback restores 74,449 rows; and reapply is
deterministic. Live PEQ remains unchanged pending the maintenance application.

## 2026-07-28 - Acquire and diff the canonical PEQ skill-cap baseline (#10)

Imported the exact PEQ archive referenced by Akk Stack's current
`init-peq-database` target into an isolated no-host-port MariaDB container. The
32,150,987-byte archive has SHA-256
`ac8649f23d2c3aea2cade138dfe10d46d1b21ad1a80d08ca95f5434fab7f218d`.

A new read-only cross-container comparator retains complete CSV evidence. Live
has 74,449 `skill_caps` rows versus 58,359 canonical rows: 16,090 are live-only,
zero are canonical-only, and zero shared caps differ. This proves legacy
widening added rows without altering or removing native rows. Live PEQ remains
unchanged; the next gate is a fresh backup and restored-copy migration rehearsal.

## 2026-07-28 - Remove production multiclass skill maximization (#10)

Removed `mc_train_skills` and every direct `SetSkill` write from the multiclass
adoption plugin. Adopting a class can no longer silently raise existing or new
skills to the current cap. A static regression fails if the production plugin
reintroduces either behavior; the deployed and tracked plugin copies are
byte-identical and pass `perl -c`.

Value-`1` lifecycle seeding is intentionally not enabled yet: the live
`skill_caps` table must first pass the canonical-baseline repair gate. Existing
zone processes were not restarted by this source-only change.

## 2026-07-28 - Resolve held-class skill caps and unlocks safely (#10)

Added a pure held-class skill eligibility resolver that deduplicates the
primary/secondary/tertiary class list, rejects invalid class IDs, selects the
highest current cap, and selects the earliest positive native unlock level.
Those two values may correctly come from different held classes; non-held or
invalid classes are never queried.

CppUnit covers mixed caps/unlocks, duplicates, and fail-closed invalid input.
The full suite passes 83/83. This seam does not mutate characters or the live
database and is ready for the separately tested lifecycle reconciler.

## 2026-07-28 - Define the multiclass skill acquisition policy (#10)

Added a fail-closed acquisition policy for all 78 RoF2 `SkillUseTypes` values and
a pure seeding decision that grants exactly value `1` only at or after a
positive native unlock. Existing nonzero values are never changed. Alchemy, Make
Poison, and Research are class-granted; Tinkering, universal tradeskills, Sense
Heading, Swimming, Fishing, and Alcohol Tolerance retain stock acquisition.

The checked-in policy table is generated from the actual C++ name map and policy
switch. CppUnit covers every current skill ID, thresholds, zero-cap/unlock
rejection, idempotence, and the stock-acquisition exclusions. The full suite
passes 82/82. This slice defines and tests policy only; no live character skill
values or database rows are changed.

## 2026-07-28 - Generate the Epic #10 parity evidence matrix

Added a deterministic PowerShell generator and a 480-row acceptance matrix that
covers all 16 playable classes in primary, secondary, and tertiary slots across
ten contracted capability groups. Every row has an implementation owner plus
separate automated and manual evidence fields; all begin unresolved as
`planned`.

Started the checked-in player class-gate ledger with direct Client paths, shared
Mob review boundaries, contract classifications, required remediation, and
named evidence. Bot/NPC identity checks remain distinct from player capability
gates so later changes do not globally replace `GetClass()`.

## 2026-07-28 - Add a read-only multiclass skill-cap baseline audit (#10)

The live PEQ `skill_caps` table still contains rows from the legacy global
multiclass widening, while every retained local backup postdates that change.
Added a checked-in evidence report and a read-only PowerShell audit that reports
known contamination controls and can later produce exact live-only,
canonical-only, and cap-mismatch diffs against a separately imported canonical
table.

No database data is changed. A verified authoritative PEQ baseline, fresh manual
backup, reviewed diff, and restored-copy migration rehearsal are mandatory before
any live repair. The official PEQ dump host was unavailable through DNS during
this audit; unrelated emulator forks are explicitly not accepted as substitutes.

## 2026-07-28 - Correct native skill train-level resolution (#10, #39)

`SkillCaps::GetSkillTrainLevel()` previously looped over candidate levels while
probing the same key built from the requested maximum level. If that final-level
row existed, it incorrectly returned level 1; otherwise it returned 0. This made
native unlock thresholds unreliable for multiclass auto-grants and trainers.

The resolver now probes each level in order, stops at the configured skill-cap
maximum, and exposes the pure search step to CppUnit. The regression covers a
level-5 unlock below, at, and above its threshold. No live database rows are
changed by this patch.

Phase 0 also confirmed that legacy globally widened `skill_caps` rows remain in
the live PEQ database even though the current Chronicler no longer creates them.
Those rows are a separate migration blocker: held-class authorization cannot
treat the live table as native until it is reconciled against a clean baseline.

## 2026-07-28 - Stabilize the RoF2 PlayerMana gauge (#12)

Manual QA found that the melee-base mana gauge appeared but flickered. Exact
client disassembly showed why: `CPlayerWnd` refreshes the HUD every 500 ms and
calls a separate base-class mana predicate at RVA `0x00318E93`; its false
result repeatedly hid `PlayerMana` after the `Max_Mana` hook re-showed it.

The DLL now redirects only that exact five-byte predicate call to a guarded
helper that reports whether the authoritative `pinstLocalPlayer+0x354` maximum
is positive. The stock HUD therefore owns continuous visibility, while true
zero-mana characters remain hidden. The competing direct `SetVisible` call was
removed from the `Max_Mana` detour. Client size/SHA, original call bytes, and
the original call target are covered by the static regression test. The DLL
built cleanly and is deployed to the RoF2 dev client; the flickering build is
preserved as `dinput8.dll.flickerbak`. Focused in-game QA passed: the gauge
remains stable while idle, casting, regenerating, zoning, and relogging; a
zero-mana melee character stays hidden; and Done's stock caster HUD remains
intact. A separate black-world renderer failure during QA recovered by
switching the RoF2 client to fullscreen and did not affect the mana path.

## 2026-07-19 - Reassert RoF2 Player_Mana gauge visibility (#12)

The functional mana path already supplied Pups with `148/148`, but the Rogue
base HUD could leave the constructed `Player_Mana` gauge hidden. The DLL now
uses the exact RoF2 `CPlayerWnd` slot (`rva 0x0091FC68`) and child offset
(`+0x22C`) from the game-thread `Max_Mana` path, calling the stock
`CXWnd::SetVisible` vtable entry (`+0xD8`) once a positive server maximum is
available. Pointer reads and the virtual call fail closed; the executable
size/SHA guard and existing `Max_Mana` signature guard remain required. This
is deployed to the dev RoF2 client and awaits in-game QA.

## 2026-07-19 — Re-enable guarded `Max_Mana` hook after wire fix (#12/#13)

The corrected RoF2 packet encoder now populates Pups's local raw fields at
`148/148`. The DLL's exact-signature six-byte `Max_Mana` detour is restored; it
returns `LocalPlayer+0x354` for the four stock non-caster base classes and
returns zero until a valid local-player object exists. The hook is
version-guarded, verifies its write, and rolls back on failure.

Running log of significant changes to this repo — schema migrations, C++ patches, quest script additions, and anything with gotchas worth remembering. Most recent first.

---

## 2026-07-18 — Waypoints fixed: discovery moved to the marker NPC (#32)

The active global quest is Lua-first, so the old Perl global-player waypoint
discovery never ran. Discovery now lives on marker NPC `999240`, whose quest
arms a proximity box on spawn and records the current zone. The old Perl global
handler is an inert documented stub. Deploy requires a zone restart so marker
NPC spawn events re-arm.

---

## 2026-07-19 — RoF2 `OP_ManaUpdate` wire layout corrected (#12/#13)

The client capture and executable disassembly showed that RoF2 decodes mana
updates as `uint16 spawn_id`, `uint32 cur_mana`, `uint32 max_mana` (10 bytes).
EQEmu was emitting the generic `cur_mana`, `max_mana`, `spawn_id` layout, so
the server reported `148/148` for Pups but the client discarded the packet.
Added the RoF2-specific struct and encoder; the DLL remains a read-only trace.

---

## 2026-07-19 — Mana initialization uses the canonical connected-state path (#12/#13)

The first server-side self `OP_ManaUpdate` attempt did not change Pups's raw
client fields (`0/0`) despite a clean zone restart. The ready handler now uses
`CheckManaEndUpdate()` after `CompleteConnect()`, which emits the normal
`OP_ManaUpdate` plus `OP_ManaChange` sequence once the client is connected. A
temporary `[ManaInit]` server log records the authoritative current/max mana,
held classes, and spawn ID for the next capture. The client DLL remains
behavior-neutral and only traces the raw fields.

---

## 2026-07-19 — DLL B2 trace: force initial self mana update (#12/#13)

Follow-up disassembly corrected the interpretation of the stale
`LocalPlayer+0x494/+0x354` samples. The RoF2 handler at preferred VA
`0x004BD210`:

1. resolves the packet's spawn ID through the spawn manager;
2. explicitly compares that result with `pinstLocalPlayer`;
3. writes packet current mana to `+0x494` and maximum mana to `+0x354` only
   when they match.

The object identity was therefore correct. The observed `22200/0` values mean
the local spawn had not received a self `OP_ManaUpdate` after zone entry.
Server connect currently sends an HP update after `CompleteConnect()` but no
equivalent mana update; saved mana is loaded with `Mob::SetMana()`, which is
documented not to send a packet.

`Handle_Connect_OP_ClientReady` now sends one self mana update for SoD-or-newer
clients whose server maximum is positive. The DLL remains behavior-neutral for
this capture: it logs the local spawn's raw current/maximum fields but does not
reinstate the `Max_Mana` detour. Expected Pups trace after login and after
zoning is a positive maximum (`148` in the current test state) while the UI
remains `0/0`. Only that proof will authorize restoring the guarded return
hook.

---

## 2026-07-19 — DLL B2 safe-build QA passed (#12/#13)

Manual two-client QA passed after withdrawing the invalid mana hook and
disabling `MQ2EQIM` autoload:

- Pups (Rogue base) and Done (Cleric base) both opened Spell Gems and
  Spellbook normally.
- Both characters zoned successfully with the window behavior intact.
- No client crash recurred.
- Pups remained at the expected unresolved baseline: no mana bar and `0/0`.

This accepts the guarded caster-class table as a stable window/chassis
correction and confirms the crash isolation. It does not complete B2: the
remaining work is to identify the authoritative client mana object/value path
for melee-base multiclass characters. The branch is not promoted while that
casting blocker remains.

---

## 2026-07-19 — DLL B2 mana hook withdrawn; MQ2EQIM crash isolated (#12/#13)

The first in-game run rejected the assumed `pinstLocalPlayer` mana fields.
Runtime samples read `22200/0` at `+0x494/+0x354` for Pups instead of the
server's saved mana `148`, and the UI remained `0/0`. Static packet-handler
disassembly had identified fields on an object, but did not prove that object
was MQ2's exported local-player instance. The six-byte `Max_Mana` detour and
the invalid field-sampling code have been removed. The deployed replacement
returns to the already-tested caster-class table correction only.

The session's MacroQuest dump was also analyzed:

- dump: `mq-rof2/Logs/eqgame_20260719_172253.dmp`
- exception: `0xC0000005`, read from address `0xD4`
- fault: `eqgame.exe+0x003EFA80`, `mov eax,[ecx+0xD4]`, with `ECX=0`
- caller: `MQ2EQIM.dll+0x15C6`, calling
  `CChatService::GetNumberOfFriends` with a null chat-service pointer

The faulting instruction and immediate caller are outside the Nightcap proxy,
so this crash is attributed to the legacy MQ2EQIM plugin rather than the DLL
patch. Its autoload entry has been removed from `mq-rof2/MacroQuest.ini` for
subsequent DLL QA; the plugin binary remains untouched.

---

## 2026-07-19 — DLL B2 follow-up: use server-cached max mana (#12/#13)

QA proved the exact caster-class table correction applied but did not restore
Rogue-base mana: Pups still had no mana bar and displayed `0/0`. The table is a
window/caster-activation gate, not the client's max-mana calculation.

Build-exact disassembly found the independent cause:

- `EQ_Character::Max_Mana` (RVA `0x00181E60`) dispatches on base class.
- WAR/MNK/ROG/BER reach a six-byte unconditional zero return at RVA
  `0x00181E96` (`33 C0 5E C2 04 00`).
- The RoF2 `OP_ManaUpdate` handler already stores Nightcap's authoritative self
  values on the local-player object: current at `+0x494`, maximum at `+0x354`.

The DLL now redirects only that exact non-caster return block to an x86 stub
that returns `[LocalPlayer+0x354]` (or zero before the player/packet exists) and
then performs the original epilogue. Caster-base classes do not take the hooked
path. This preserves the server's best-of-held-classes mana calculation and
avoids class spoofing or a duplicate client-side formula.

The hook requires the existing size/full-SHA guard plus the complete six-byte
signature. The survey now logs the cached current/maximum values every 15
seconds for unambiguous QA. Built successfully with MSVC x86; awaiting Pups
mana-bar, casting, regeneration, and zone-persistence QA.

---

## 2026-07-19 — DLL B2 follow-up: full caster chassis for melee bases (#12/#13)

The first guarded correction passed its window test: Rogue-base Pups could open
Spell Gems and Spellbook normally. Pups still displayed `0/0` mana and could
not cast. A read-only live DB check proved the server had loaded the intended
multiclass state and mana: Pups is ROG/WIZ/DRU with saved mana `148` (Done is
CLR/SHD/MNK with `103`). The remaining blocker was therefore the RoF2 client
chassis, not `Client::CalcMaxMana()`.

A full disassembly search found exactly five calls to the shared 16-byte caster
predicate table: the two window `CanShow` checks plus three caster
initialization/activation paths. The correction now replaces the two narrow
branch NOPs with the underlying class-table change:

- table RVA `0x00043F90`
- exact stock signature
  `00 01 01 01 01 01 00 01 00 01 01 01 01 01 01 00`
- WAR, MNK, ROG, and BER entries change from `0` to `1`

This remains four changed bytes total, but every known caster-chassis consumer
now receives the same capability answer. The server remains authoritative for
actual multiclass membership, mana, spell availability, and cast validation.
The DLL still fails closed on client size, full SHA-256, or complete table
signature mismatch and rolls back a failed write.

Built successfully with MSVC x86. Awaiting Pups mana/casting QA before feature
branch promotion.

---

## 2026-07-19 — DLL B2: guarded Rogue-base spell UI correction (#12/#13)

The corrected simultaneous-client survey passed: Done (Cleric base) and Pups
(Rogue base) each captured 991 initialized eqgame offsets with reliable
15-second sampling. Both spell-window objects existed and were fully
initialized for Pups. MQ2 `/windowstate` reached the stock `CXWnd::Show` path
but the windows remained hidden, isolating the failure to their virtual
`CanShow` checks.

Live memory inspection and disassembly found that both window overrides consult
the same 16-byte stock caster-class table. Its zero entries are exactly WAR,
MNK, ROG, and BER. To limit blast radius, the correction leaves that shared
table untouched and disables only the post-predicate rejection branch in:

- `CCastSpellWnd::CanShow`, signature RVA `0x00248867`
- `CSpellBookWnd::CanShow`, signature RVA `0x0035C97F`

This changes four instruction bytes total and preserves all remaining window
safety checks plus every unrelated class-table consumer. The proxy fails closed:
it writes only when the client size (8,774,656), full SHA-256
(`2a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e`),
and both nine-byte signatures match. A failed partial application is rolled
back. MQ2 is no longer required by the correction itself; the survey remains
temporarily for QA diagnostics.

Built successfully with MSVC x86. Awaiting Pups + Done in-game QA before any
promotion beyond the feature branch.

---

## 2026-07-19 — DLL B2 survey v2: reliable timing + multi-client logs (#12/#13)

The first successful MQ2-injected capture proved the raw-memory fallback works
(`MQ2 found at base=...`) and exposed the targeted eqgame pointer slots, but it
also revealed that every `Sleep()` returned almost immediately: 60 intended
15-second polls completed in ~8ms, before character login. The export survey
also ran before MQ2 finished initialization and captured only `baseAddress`.

Corrected `eq-client-dll/src/dllmain.cpp`:

- Replaced `Sleep()` with a private, never-signaled event wait plus elapsed-time
  verification and a defensive wall-clock fallback.
- Waits for at least five targeted MQ2 exports to contain eqgame addresses,
  then gives MQ2 a real five-second settling period.
- Retries the full export survey up to five times when fewer than ten eqgame
  offsets are captured.
- Adds sample number + elapsed seconds to every window-instance poll.
- Writes `nightcap_dll_<PID>.log`, preventing two simultaneous EQ clients
  (Done caster-base and Pups Rogue-base on separate accounts) from truncating
  or suppressing each other's capture.

Still survey-only: no client memory writes and no UI behavior changes.

---

## 2026-07-18 — DLL B2: offset-survey build (#12/#13)

In-game QA proved every remaining multiclass blocker (#36 skills window, #37 AA toggle,
#38 equip, #39 trainers) is the RoF2 base-class UI chassis — the client overrides the server
below its own gates (the `#aaexp` toggle gets bounced off at level < 51). Server side is done
for all four; the DLL is the single unlock. Pivoted to B2.

`eq-client-dll/src/dllmain.cpp` gains an **offset survey** (still no memory writes): it waits
for `MQ2Main.dll` in-process, walks its export table, and logs every exported DWORD whose
stored value lands inside `eqgame.exe`'s module range — i.e. MQ2-emu's build-exact eqgame
static addresses, with zero reversing. Then polls a watchlist (spellbook/cast/gem window
instances, PC/char data) every 15s so a HITL session captures window lifecycle (do the
windows get constructed for a melee base, or never created?). Output: `nightcap_dll.log` in
the client folder. Survey runs even on client-size MISMATCH; it never patches.

Deployed to `Client_RoF2_Dev/everquest_rof2/dinput8.dll` (B1 skeleton saved as `.b1bak`).
Next: HITL session runs the survey, then B2 writes the force-show/gate patches at the
captured offsets behind the version guard.

---

## 2026-07-16 — Auto-grant multiclass skills on level-up (#36/#39 follow-up)

In-game QA confirmed the multiclass skill/trainer fixes are **client-chassis-blocked**: the
RoF2 Cleric-base chassis hides secondary-class combat skills from the Skills *window* (#36),
and the client refuses to open an off-base-class trainer at all (#39) — so the server-side
trainer fix never receives a request. The skills still *function* (Dual Wield etc. are granted
and work in combat), but they can't be trained the normal way and don't display.

Route-around (matches #36's ask, "auto-granted to avoid running to a trainer"):

- `global/global_player.pl` **`EVENT_LEVEL_UP`** calls `plugin::mc_train_skills` — re-grants
  every held class's skills to the new level's cap on each level-up. **Scoped to multiclass
  characters** (has class2/class3) so normal characters keep their skill-up grind.
- Idempotent (only raises skills below cap). Applies on `#reload quest` / zone restart.

**Still DLL-blocked (client chassis, needs #12/#13), documented not fixed:** the Skills-window
display of off-base skills (#36) and the off-base trainer window opening (#39). The C++ trainer
mask-aware fix stays in place for when the DLL unlocks the client. This is the same wall as the
AA-XP toggle (#37) and equip (#38) — the base-class UI chassis is the recurring limit.

---

## 2026-07-16 — `#aaexp` player command: turn on AA XP below level 51 (#37 follow-up)

QA of #37 confirmed the server side is fully open (rule `Character:AAExpMinLevel=1`, no gate
in `Handle_OP_AAAction`, `exp.cpp` gates rule-driven) but the **RoF2 client hides the AA-XP
toggle below level 51**, so it never sends `OP_AAAction` — a level-4 character has no usable
control. Root cause is client-side; no server change can draw a control the client refuses to.

Fix (the `#sellall` pattern — a player command where the client UI can't do the job):

- New **`#aaexp [0-100|off]`** command (`AccountStatus::Player`, `gm_commands/aa_exp.cpp`) sets
  the % of combat XP routed to AA. No args → prints current %.
- New **`Client::SetAAExperiencePercent`** (`client.cpp`) clamps 0-100, sets `m_epp.perAA`,
  sends the AA stats/table update. `exp.cpp` still enforces `AAExpMinLevel`, so it only sticks
  at/above that level (=1 here).
- Registered in `command.cpp`, declared in `command.h`, added to zone `CMakeLists.txt`.

**Usage:** in game, `#aaexp 50` routes 50% of XP to AA; `#aaexp off` stops. Works at any level.

---

## 2026-07-16 — Multiclass skill access + trainers (#36, #39)

Field QA (char "Done": Cleric base + SK + Monk) surfaced secondary-class skills that were
set but unusable, and 2nd/3rd-class trainers that refused interaction. Both were base-class
`GetClass()` gates that never consulted the held-class union. Fixed by extending the
existing `Client::GetMulticlassList()` mask pattern (already used for mana/equip):

- **`client.cpp CanHaveSkill`** — now returns true if **any** held class can have the skill
  (each class's native `skill_caps` are already in shared memory). This alone makes
  `HasSkill`/`CanThisClassDualWield` recognize secondary-class skills — e.g. Cleric-base can
  now dual wield via its Monk/SK discipline (**#36**).
- **`client_process.cpp` trainers** (`OPGMTraining`/`OPGMEndTraining`/`OPGMTrainSkill`) —
  accept the trainer if its class is any held class (`IsMulticlassMember`), and compute the
  offered skill caps + train levels **best-of across held classes** (**#39**).
- New helper **`Client::IsMulticlassMember`** (`client.h`/`client_mods.cpp`).
- **`plugins/multiclass.pl`** — removed the global `skill_caps` INSERT widening from
  `mc_apply_class`; the mask-aware `CanHaveSkill` makes it dead global mutation. `mc_train_skills`
  (sets skill values) stays.

**Gotchas:** no `shared_memory` regen needed (reads per-class native caps). After `make zone`,
**kill every `bin/zone` process** so eqlaunch respawns on the new binary. The RoF2 client's
Skills *window* may still visually filter by base class (chassis limit) even though the skill
functions server-side. `client.cpp` is now mirrored to `server-mods/` for the first time.

---

## 2026-07-16 — AA experience allowed from level 1 (#37)

Stock EQ gates AA-XP gain at level 51 via two hardcoded checks in `exp.cpp`
(`GetLevel() <= 50` and `GetLevel() < 51`, both zeroing `m_epp.perAA`). Replaced both
literals with a new rule **`Character:AAExpMinLevel`** (`ruletypes.h`, compiled default 51 =
stock behavior). `aa_exp_min_level.sql` INSERTs the override to **1** on ruleset 1.

- Apply: run the SQL, then `#reload rules` (no restart). Zone binary must carry the new rule
  (rebuild + restart zones for the `ruletypes.h` change).
- **Primary QA risk (client-side):** the server now permits AA XP at any level, but the RoF2
  client may still hide the AA-XP allocation control below 51. Verify in-game that a low-level
  character can actually toggle AA on; if the UI is hidden, this needs a DLL/UI note (#12/#13).

---

## 2026-07-16 — DLL track (#12): B1 verified, B0 GO, offset-source claim corrected

Reviewed the tracked DLL work (#12 M2, #13 B2, #15 B3). State assessment + honest scoping, no risky speculative code:

- **B1 (dinput8 proxy skeleton) verified done.** Rebuilds reproducibly with the local MSVC x86 toolchain (`eq-client-dll/build.bat`, VS Build Tools 2022 at `C:\BuildTools`), confirmed machine=x86 with all six DirectInput exports forwarded, and **passed its in-game smoke test** (`nightcap_dll.log`: load → size-check OK → init → clean unload vs `testeqgame.exe`, game ran identically). Was already committed d8b28c9.
- **B0 → GO.** ADR 0004 moved Proposed→Accepted. Feasibility confirmed on every non-interactive axis (toolchain, THJ precedent, symbol set, clean load).
- **Corrected an over-optimistic ADR claim:** MQ2Main.dll's export *table* is **not** the eqgame offset map. Its `pinstCSpellBookWnd 0x0022ACCC` etc. are RVAs *inside* MQ2Main.dll (image size 0x242000), i.e. MQ2's own `.data` vars — they confirm the symbol set but not the eqgame addresses. Real offsets come from MQ2-emu source `eqgame.h` (ROF2EMU) or a live-client debugger. New `eq-client-dll/docs/offsets.md` records the confirmed symbol set + this caveat + minimum-viable B2 surface (server right-click scribe already works, so only the spell-gem/memorize UI needs unlocking).
- **B2/B3 deliberately NOT built.** B2 patches client memory at offsets we don't yet hold and can only be verified by a human on a live client — its offset-extraction first step and the "Warrior opens spell-gem window" proof are one interactive session, the tracked next step.

No server/DB/binary changes; docs + build verification only.

---

## 2026-07-16 — QoL batch: #29 buff bots, #30 vendor cash, #31 permanent self-buffs, #32 waypoints, #33 Ascended summons, #34 loot-all, #35 #sellall (+#28 diagnosis)

**#30 Vendor cash (rule_values):** `Merchant:BuyCostMod` 0.95 → **2.5** — vendors pay ~2.6x for loot, the main money faucet. Buy prices untouched. `vendor_cash_boost.sql`.

**#31 Permanent self-buffs (C++, spells.cpp `CalcBuffDuration`):** beneficial spells where caster == target (clients only) get 1,000,000 tics (~69 days online). Discs/short-buff-box excluded. **Gotchas:** self-clicked potions (incl. XP potions) also become permanent; buffs still wipe on death unless `persistdeath=1`; deliberately NOT true DF_Permanent — negative tics go raw into the buff packet and `character_buffs`.

**#33 Ascended summons (C++, spell_effects.cpp SE_SummonItem/IntoBag):** summoned equippables (Slots != 0, id < 200k) upgrade to their +600k Ascended variant when one exists. Temporary flag on summons is why `#sellall` skips NoRent items — otherwise summon→sell is an infinite money loop with #30.

**#29 Buff bots (SQL + Perl):** Matron Restora (999237, free, PoK 310,290) and Magus Goldwind (999238, 100pp, PoK 390,290). Spell **rank laddering by 10-level bracket** instead of percentage scaling (zero custom spells, no client sync): SoW + HP/AC lines + Regeneration/Chloroplast + Breeze/Clarity. Goldwind adds Bottle of Adventure III (21030, +50% XP, hard 4h). Bot buffs self-apply via `ApplySpellBuff` → permanent per #31. `buff_bots_setup.sql`.

**#32 Waypoints (SQL + Perl):** 72 Classic-zone waypoints (`nightcap_waypoints`): dungeons at safe point, outdoor at the spawn2 farthest from safe (valid ground, deterministic). Marker NPC `a waypoint` (999240, ONE spawngroup, 72 spawn2 rows). Discovery: `global_player.pl` 3s proximity timer (25u), writes `nightcap_character_waypoints`; all 72 → title "the Explorer" (title_set 100). Waypoint Master (999239, PoK 370,290) saylink-teleports to discovered ones. `waypoints_setup.sql`. **Gotcha:** timer cache (`%nightcap_wp`) dies on `#reload quest`; player re-zones to re-arm.

**#35 #sellall (C++, gm_commands/sell_all.cpp, Player status):** sells general + bag contents at `price * BuyCostMod`, keeps bags/no-drop/temporary/worthless. No merchant target needed; no CHA mod.

**#34 Loot All prompt:** client-side — `eqclient.ini LootAllConfirm=1` → set to 0. Not a server issue. If per-item NO TRADE prompts remain, `/lootnodrop never` in game.

**#28 Pups black screen:** diagnosed client-side — `dbg.txt` shows `Lost D3D device` then endless `CBufferSet::AllocateVertices() failed`; renderer never recovers after device loss, world black, UI alive, follows the client process (not the character — Pups' server data clean). Fix: restart eqgame.exe; prefer windowed/borderless.

Applied to live DB. Zone rebuilt (spells.cpp, spell_effects.cpp, command.cpp/h, sell_all.cpp) + all zones restarted.

---

## 2026-07-16 — Heroic stats activated + stat softcap raised (#8)

**Finding:** heroic stats were NOT missing — the engine is fully implemented in this build (`bonuses.cpp` CalcHeroicBonuses / SetHeroic*Bonuses, driven by `Character:Heroic*Multiplier` rules at ×1.0). Per the rule descriptions: heroic STA → +100 HP/+0.5 HP-regen/+endurance per 10; STR → +1 melee dmg/+1 shield-AC per 10; AGI → +1 avoidance-AC; DEX → +1 archery/throwing dmg; INT/WIS → +100 mana per 10; heroics also raise the stat's own softcap. It just had nothing to act on. Three gaps fixed:

1. **Items now carry heroic.** Added `heroic_X = 25% of the scaled base stat/resist` to **Ascended items only** (the THJ Legendary signature — necklace 9289 Legendary: STA 40 → +10 heroic). Polished/Exalted stay heroic-free. `tiered_loot_setup.sql` proc gained a `p_heroic` param (Ascended 0.25, else 0); Ascended epics get it too. Regenerated the tier bands.
2. **Stat softcap raised 255 → 425** (`Character:StatCap`, ruleset 1) so the 2026-07-16 ×2.0 stat scaling isn't clamped and heroic can stack above it (matches the ~420-435 caps in the THJ #24 reference).
3. Heroic multipliers left at ×1.0 (already meaningful). The two heroic→advanced conversions (INT→spell-dmg, WIS→heal-amt) left **off** for now — they double-dip with gear's own spell-dmg/heal.

Needs shared_memory regen + zone restart (item data + `#reload rules`). Backup peq_20260716_053700 (from the earlier scaling pass) covers pre-heroic state.

**Gotcha:** heroic only *does* something on gear that has it — currently only Ascended (and Ascended epics). Lower-tier / base gear grants no heroic by design. The heroic→cap interaction means a fully-Ascended character's base stats can exceed 425.

---

## 2026-07-16 — Item tier scaling recalibrated to THJ Legendary (#25)

Replaced the 2026-07-15 two-curve scaling (defense x1.20/1.45/1.75, offense x1.10/1.20/1.35) with a **per-family model calibrated to actual THJ Legendary values**, measured from the Necklace of Eternal Visions (item 9289) base vs the Legendary reference the user provided (#25):

| Family | Polished | Exalted | Ascended (= THJ Legendary) |
|---|---|---|---|
| HP / Mana | 1.45 | 1.90 | **2.40** |
| AC / base stats / resists / regens | 1.35 | 1.65 | **2.00** |
| Endurance | 1.07 | 1.13 | **1.20** |
| Offense (dmg/atk/acc/spelldmg/healamt/...) | 1.10 | 1.20 | **1.35** |

Key changes vs the prior model:
- **Ascended is now much stronger** on survivability — HP/Mana x2.4 (was x1.75) and stats/AC/resists x2.0. This matches THJ, where end-game is survivable-but-hard only with maxed gear.
- **Resists moved from the offense curve to the core x2.0 family** (THJ scales resists x2.0, verified: 15 -> 30 on the necklace).
- **Offense curve unchanged** (x1.35 max) — kept conservative so solo kill-speed doesn't trivialize; burst is meant to come from AA/discs/augments (#24 context).
- **Capped advanced stats (shielding/spellshield/dotshielding/avoidance/clairvoyance) are no longer scaled** — THJ leaves them (necklace shielding 2 -> 2).
- **Heroic stats left untouched, by design.** THJ *adds* heroic on Legendary (~25% of the scaled stat); that whole layer is deferred to heroic-stats (#8), since heroic doesn't function yet and scaling the mostly-zero base heroic columns is inert.

`eq-solo-gm/scripts/tiered_loot_setup.sql` is the source. Ascended epics (+800k) use the same per-family scaling. Backup peq_20260716_053700 taken before the 190k-row regen. Needs shared_memory regen + zone restart.

**Not done (follow-ups):** heroic-stat additions (with #8), and THJ's advanced-stat *additions* on Legendary (Attack/Accuracy/Heal/SpellDmg appear on the necklace but were 0 on the base — the multiplier can't add them; would need a generic per-slot rule).

---

## 2026-07-16 — Issue batch: #27 no-corpse-runs, #21 spell-vendor split, #18 strip fixes, #19 diagnosis

**#27 No corpse runs (rule_values, ruleset 1):** on death you now keep all gear/money/items and respawn at bind.
- `Character:LeaveCorpses = false` — no player corpse is created (attack.cpp:2061 / client.cpp:4442 gate on it), so the corpse constructor that "takes the cash/items off the player" never runs.
- `Character:DeathItemLossLevel = 999` — belt-and-suspenders (the item/cash transfer at corpse.cpp:297 is gated by `level >= DeathItemLossLevel`).
- `Character:LeaveNakedCorpses = false` — was `true`, but harmless-looking: corpse.cpp:298 ORs it with LeaveCorpses so items still transferred; cleared for clarity.
- Buffs: the combat-death path already uses `BuffFadeNonPersistDeath()` (keeps only `persistdeath` spells). Set `spells_new.persistdeath = 1` on all permanent (buffdurationformula=50) beneficial buffs so **permanent buffs survive death** (matches the #5 permanent bard songs). Needs shared_memory regen + zone restart.

**#21 Spell vendors truncated at "M":** RoF2 caps the merchant window at **500 items** (`common/patches/rof2_limits.h` MERCHANT_SIZE; enforced client_process.cpp:850/856 — items past slot 500 are silently dropped). The Arcane (776), Divine (687), Stalwart (681) Loremasters exceeded it (504 of Arcane's 776 sort before "Spell: N" → the cut landed at M). Not a restock/level-gate bug — genuinely more Classic-legal caster spells than the client can show.
- Fix: a second "II" vendor per over-cap archetype (`eq-solo-gm/scripts/spell_vendor_split.sql`, NPCs 999234-236, merchant_ids 99251-253, back row behind the originals). `vendor_restock.sql` now moves each over-cap vendor's second alphabetical half onto its II partner (generic `split_vendor` proc, triggers >480).

**#18 strip fixes (C++, mirrored):** two gaps QA surfaced in the release AA-strip —
- `SaveAA`'s `ReplaceMany` is `REPLACE INTO` (upsert only), never deleting removed rows → stripped AAs reloaded on relog. Now `DeleteCharacterAAs` wipes first, then SaveAA re-inserts survivors (matches ResetAA).
- The RoF2 client never drops an AA from its window on its own; added `SendClearPlayerAA` (OP_ClearAA) before the table resend so stripped AAs vanish without a relog.

**#19 Bard movement songs — diagnosed, not yet fixed:** Selo's data (SE_MovementSpeed=15, permanent) and the runspeed math (mob.cpp:834-858, 158% cap) are both correct, and the bonus loop includes permanent buffs. Remaining suspects need an in-game reading: bard `instrument_mod` scaling, or the buff not landing while moving (ties to #20). Left open.

**Gotcha:** `vendor_restock.sql`'s per-row `MIN(item.id)` dedup subquery holds a long read lock on `items`/`spells_new` while it runs (minutes) — don't run concurrent `spells_new` writes; they'll hit lock-wait-timeout.

---

## 2026-07-15 — Item tiers renamed (Polished/Exalted/Ascended) + two-curve scaling rework

Tier review found two problems: names duplicated THJ vocabulary ("Legendary") and EQ's class-epic term ("Epic"), and flat ×1.20/1.45/1.75 scaling on ALL stats made top-tier weapons ~+75% auto-attack DPS (damage scaled, delay untouched) and walked past Classic resist checks.

**Renames:** Rare→Polished, Epic→Exalted, Legendary→Ascended (all ~191k tier rows regenerated in place, same IDs — owned items update automatically). "Essence of the Legend"→"Essence of Ascension"; Forgemaster quest dialogue + lastname updated. C++ rule names (`Zone:LootTier{Rare,Epic,Legendary}Chance`) deliberately kept — internal-only, avoids a rebuild; notes updated to map old→new.

**Scaling model — tier bonuses as fractions of one expansion step** (era mobs and era loot both grow, so relative multipliers stay balanced as eras unlock; measured era steps from PEQ: ~×1.4-1.5 weapon DPS, ~×1.5-2 armor durability per expansion):
- **Offense + resists ×1.10/1.20/1.35** (damage, attack, accuracy, spelldmg, healamt, backstabdmg, elemdmgamt, combateffects, strikethrough, damageshield, all resists) — time-to-kill is the trivializing axis; top tier now +35% DPS instead of +75%. Resist checks stay meaningful.
- **Defense + utility ×1.20/1.45/1.75 unchanged** (AC/HP/mana/regens/stats/heroics/avoidance/shieldings/clairvoyance) — survivability is what keeps soloing viable.
- Ascended class-epics (+800k band) use the same split. Drop rates unchanged (10%/2%/0.25%).

**Applied:** backup taken (peq_20260715_094215), regen run, shared_memory rebuilt, zones restarted. `eq-solo-gm/scripts/tiered_loot_setup.sql` is the durable source.

**Gotchas:** RoF2 caches item stats client-side per session — camp/zone before inspecting. Forgemaster quest reads base class only (multiclass-blind) — follow-up candidate. Existing owned tier items silently changed stats/names (intended).

---

## 2026-07-15 — M3 server-side (#13 A3+A4): mask-aware spell gates + equipment union; right-click scribe (#2); #instances command (#7); vendor dedupe (#9)

**Spell gates (A3), `akk-stack/code/zone/` mirrored to `server-mods/`:**
- New helpers: `Client::GetSpellMinLevel(spell_id)` (lowest required level among held classes), `Client::BestCasterClassFor(spell_id)` (held class with lowest req level), `Client::CanEquipItem(item)` (race + any-held-class), `Client::GetEquipClassBitmask()`.
- `Handle_OP_MemorizeSpell` scribe/mem level gate → min across held classes (client_process.cpp).
- `Client::CheckFizzle` → difficulty and prime stat (INT/WIS/Bard) come from the best held class for the spell, not base class (spells.cpp).
- `Client::MemorizeSpellFromItem` + `Client::UseDiscipline` class/level gates → mask-aware (effects.cpp).
- `CheckSpellLevelRestriction` needed **no change** — it already uses the all-class minimum level (recipient-side check).

**Equipment (A4):**
- `InventoryProfile::SwapItem` gained an optional `class_bitmask` param — equip class check passes if ANY held class can wear it; race/deity/level still enforced (common/inventory_profile.*). Zone caller passes the multiclass union.
- Item bonuses (`AddItemBonuses`, `AdditiveWornBonuses`) and loot auto-equip use the union too — without the bonuses change, off-class items would equip but grant no stats.

**Right-click scribe (#2):** enabled `Spells:AllowSpellMemorizeFromItem = true` (rule_values). The RoF2 client sends no scribe packet from inventory double-click; but right-click "use" on a scroll hits `Handle_OP_ItemVerifyRequest`, which scribes directly when this rule is on — no spellbook window needed. This also unblocks scroll scribing for base classes with no book UI (pre-DLL). Gate made mask-aware.

**#instances command (#7):** new player-level `#instances` lists the character's open instances with time remaining (`zone/gm_commands/instances_list.cpp`). A true `/instance` slash command requires client patching — candidate for the M2+ DLL.

**Vendor dupes (#9):** `vendor_restock.sql` now stocks one scroll item per spell (`MIN(item.id)` per scrolleffect) — PEQ ships several identical scrolls per spell (one per original class vendor). Re-ran restock.

**Gotcha:** the restock's per-row `MIN()` correlated subquery is slow (minutes per vendor) — fine for a maintenance script, don't put it in a request path.

---

## 2026-07-15 — Caster AAs invisible: off-by-one class bit in AA send (QA on Tester WAR/NEC)

QA of M1 surfaced that a WAR/NEC saw no Necro AAs in the AA window. Server-side authorization was fine (mask, `character_multiclass` row, `CanUseAlternateAdvancementRank` all correct) — the bug was in the client-facing display reshape in `Client::SendAlternateAdvancementRank` (`aa.cpp:1023`): `my_class_bit` was built as `1 << (GetClass() - 1)` (DB format) but `aai->classes` is client format, bit N = class N (the loader does `classes << 1`). Single-class AAs were therefore tagged with a class bit the client never matches, so the client hid them — including the character's own native class-tab AAs. Fixed to `1 << GetClass()`; mirrored to `server-mods/`.

**Gotcha:** two class-bit formats coexist in AA code — DB format (bit N-1 = class N) and client/in-memory format (bit N = class N). Anything written into an outgoing packet must be client format.

Also from the same QA: "Warrior can't open spellbook / memorize" is **expected**, not a regression — that's M2/M3 (#12/#13, client DLL UI unlock + spell gates), not yet built.

---

## 2026-07-14 — M1 (#11): multiclass-aware mana & HP (best-of across held classes)

First code of the True Multiclass epic (#10). Previously a character's mana/HP came only from its **base** class, so a Warrior who adopted Necromancer had zero mana (headline blocker for warrior-casters). Now both are best-of across the held classes (base + class2 + class3 from `character_multiclass`, via the already-loaded mask).

**C++ (`akk-stack/code/zone/`, mirrored to `server-mods/code/zone/`):**
- New reusable primitives: `Mob::IsINTCasterClassID/IsWISCasterClassID(class_id)` (static; the instance predicates now delegate — single source of the class lists), `Mob::ClassLevelFactor(class_id, level)` (static; `GetClassLevelFactor()` delegates), and `Client::GetMulticlassList()` (base+class2+class3, deduped).
- **Mana:** `Client::CalcBaseMana()` now returns the max of `CalcBaseManaForClass(c)` over held classes; `CalcMaxMana()` gates on `HasAnyCasterClass()`. Both SoD and classic formula paths parameterized by class.
- **HP:** `Client::CalcBaseHP()` picks the held class with the highest `base_data.hp` (SoD path) / `GetBestClassLevelFactor()` (classic path). Warrior base already wins HP, so the win is for caster-base + melee-adopted.
- **Bard regen:** the "Bards get no spell mana regen" exception is now mask-aware (a Bard base with another caster discipline keeps that class's regen).

**Verification:** zone build clean; all 8 zones boot on the new binary through the changed connect/stat-calc paths without error (smoke). Data premise confirmed (base_data: NEC L50 mana=900, WAR=0). Full behavior is in-game QA (M1 acceptance in #11).

**Deferred (named ceiling, ponytail):** AC softcap + stat-cap best-of, and heroic INT/WIS mana-regen mask-awareness (`bonuses.cpp:5809-5828`) — near-zero effect at Classic era (heroic stats), revisit if era advances. Load-order edge: if a stat recalc fires before `LoadMulticlassMask` on zone-in, values are base-only until the next recalc (self-heals within moments; frequent recalcs).

---

## 2026-07-14 — plugin::multiclass was never loading: plugins live in server/plugins/, not quests/plugins/

In-game: `Undefined subroutine &plugin::mc_get_classes` on hailing the Chronicler. This build loads Perl plugins from **`/home/eqemu/server/plugins/`** (server root) — `quests/plugins/` is a decoy containing copies of the same stock files, which is why the location looked right. Moved `multiclass.pl` to `server/plugins/`, removed the wrong-dir copy, mirror now at `server-mods/plugins/`. PoK restarted (plugins load at zone/perl boot; `#reload quest` does not reload them).

---

## 2026-07-14 — Caster vendor wiped by GM tool's broken refresh; era-aware restock built

QA: Arcane Loremaster (99221) showed no spells — `merchantlist` empty. Cause: `/api/expansion/apply` (used for the 2026-07-13 Classic lock) calls `refreshSpellVendors`, which **DELETEs the vendor's stock first** and then crashes on nonexistent columns (`items.spellid`, `items.expansion` — reals: `scrolleffect`, no expansion col). It died on the first archetype, so only 99221 was wiped. The failure was even printed in the era-apply output ("Spell vendor refresh failed") and got noted-but-not-chased.

- **Restock:** `eq-solo-gm/scripts/vendor_restock.sql` — idempotent, stocks all 4 Loremasters from `scrolleffect`→`spells_new`, gated by the live `Character:MaxLevel` rule (follows era.json). Applied: 935/781/212/777 (tank is big because patched PAL/SK columns legitimately include absorbed disciplines; cross-vendor duplication is harmless). PoK restarted.
- **apply-era.ps1** now runs the restock on every era apply — vendor stock can no longer drift from the era.
- **GM tool defused:** `refreshSpellVendors` replaced with a no-op stub pointing at the script (delete-then-crash can't recur even if the old button is clicked).

**Gotcha:** delete-then-select in any refresh routine = data loss when the select throws. Select first, or make the whole thing one INSERT…SELECT after a guarded DELETE.

---

## 2026-07-14 — Spell access for secondary classes was broken end-to-end; sync pipeline built

QA question "can multiclass characters memorize secondary spells?" → **no, since June 23**. Three gates must agree and only one was handled: (1) `spells_new` server levels — patched ✓; (2) **scroll `items.classes`** — still class-locked (3 of 1,086 MAG scrolls PAL-clickable), so vendor scrolls couldn't be right-click scribed; (3) **client `spells_us.txt`** — stock, and RoF2 refuses to memorize what its local file forbids. The June 23 rework removed auto-scribe in favor of vendor purchase without opening gates 2/3, so no character could actually acquire secondary spells (Darth had 0 scribed). User kept the buy→scribe→mem design; fix = `tools/sync-spell-access.ps1`, one idempotent pipeline: scroll classes ← spells_new bits (itemtype 20), shared_memory regen + zone restart, client spell file class-fields (105–120) rewritten from spells_new (client must be closed; `.bak` kept). Run it after every embrace/release — the Chronicler now says so in an operator note. Verified: Burnout client PAL=11, 1,002/1,086 MAG scrolls PAL-usable.

**Gotchas:** client `spells_us.txt` fields 105–120 (1-indexed) are classes 1–16 — verified against three spells before writing. And "the server allows it" ≠ "the client allows it": RoF2 enforces scribe/mem from its own files, so any server-side spells_new change is incomplete without the client sync + items sync + shared-mem regen.

---

## 2026-07-14 — Multiclass selection v2: plugin core, Chronicler rewrite, crew models fixed (ADR 0003)

- **Core/UI split:** all multiclass mutations moved to `quests/plugins/multiclass.pl` (`plugin::mc_get_classes/mc_preview/mc_apply_class/mc_revoke_slot/mc_train_skills`). The Chronicler is now pure dialog; any future selection front-end calls the same plugin. **qglobals dropped entirely** — `character_multiclass` is the only state.
- **New UX:** hail → archetype-grouped class saylinks ("Guardians of the Line", "Menders and Zealots", …); class name → live preview (counts pulled from DB: spells opened / spells in reach at current level / new skills / Class-tab AA lines) + flavor line; `embrace <class>` → confirmation popup; only popup-Yes commits. Release keeps confirm popups (402/403); slot-3→2 promotion preserved.
- **Models — root cause of the human-fallback found:** PoK renders only races whose archives are in the client's `Resources/GlobalLoad.txt` or the zone's own files. Race 21 (evil eye) is in neither → silent human fallback (the CHANGES 2026-06-22 claim "Xorbb renders on old graphics" was wrong for PoK). Picked the crew from races *verified to spawn in poknowledge*: Chronicler = library guardian construct (330, size 9), Arcane = clockwork (457), Divine = Herald of Druzzil Ro (495), Martial = werewolf (14), Stalwart = Drakkin (522), Packwell = Gigglegibber goblin (433), Forgemaster = fire elemental (75, texture 1 — adjust with `#texture` if the element map differs). `eq-solo-gm/scripts/chronicler_models.sql`.
- Deploy: SQL applied, PoK zone was down (next boot fresh), `perl -c` passes on both files, mirrors synced (new `server-mods/quests/plugins/`).

---

## 2026-07-13 — AA system rework: mask off-by-one root cause, dedup of duplicates, cruft removal

**THE root cause of every recurring AA failure, found via the leftover [AADEBUG] log line:** abilities load into zone memory as `classes << 1` (bit N = class N, "EQ client format" — `LoadAlternateAdvancementAbilities`, aa.cpp), but `LoadMulticlassMask()` built the mask as `1 << (class_id - 1)` (bit N = class N+1's data). **Every character's AA visibility was shifted by one class**: Darth (PAL/BRD/MAG, logged mask 4228 = bits 2/7/12) was actually being shown CLR/MNK/WIZ AAs. All-class AAs (`classes=65535`) matched any bit, which masked how broken single-class AAs were. The June-22 "0-indexed mask fix" was itself the bug — it compared masks against *DB-format* values in analysis while the runtime compares *shifted* values. Fixed: mask bits are now `1 << class_id` for all three classes, matching the shifted convention and the NPC path (`1 << GetClass()`) that upstream already used. Only aa.cpp consumes the mask (verified by grep) — no other code affected.

Also in this rework:

Multiclass characters saw the same ability multiple times in the General/Archetype tabs — live EQ defines some abilities (Silent Casting, Combat Fury, Armor of Wisdom ×4, Shield Block ×4, …) as separate `aa_ability` rows per class group with different rank chains; a mask spanning groups exposes all of them. **20 duplicate families (22 loser rows) collapsed** via `eq-solo-gm/scripts/multiclass_aa_dedup.sql`: winner = longest rank chain, winner takes the family's `BIT_OR` class mask, losers `enabled=0` (rank chains left intact), purchases migrated by `first_rank_id`, full revert log in `aa_dedup_migration`. Idempotent; verified zero remaining dup names and zero orphaned purchases.

- **State confirmed correct already** (no changes needed): all 6,655 `aa_ranks.level_req=1` (level-1 availability), Class tab names unique via static `[CLS]` labels, ZoneEntry load-order fix still in place.
- **Known cosmetic loss:** Darth had rank 11 in two Armor of Wisdom variants; merged to one rank-11 entry — points spent on the duplicate remain counted as spent (no refund mechanism; grant AA points via GM tool if desired).
- **C++ cruft removed:** `[AADEBUG] LogError` fired on every zone-in per character in `SendAlternateAdvancementTable` (aa.cpp) — deleted, zone rebuilt.
- **Mirror sync:** `server-mods` copies of `aa.cpp` and `The_Ancient_Chronicler.pl` were stale vs live (the committed Chronicler still showed the pre-June-23 aa_ability-mutating version!) — both synced from live.

Deploy: dedup SQL applied (backup `peq_20260713_204336` taken first), zone rebuilt, all zones restarted.

---

## 2026-07-13 — Declarative era lock: era.json + tools/apply-era.ps1

Era is now config, not clicks: `era.json` (expansion, level cap, AA policy, models) is the versioned source of truth; `tools/apply-era.ps1` applies it idempotently (rules, MOTD, eqclient.ini, kills all zones so spawn lists rebuild), `-Check` reports drift (exit 1), `-CapCharacters` opt-in de-levels over-cap characters. The nightly backup task now runs the drift check, so a silent era change (like the untracked expansion-19 state) surfaces within a day. GM tool button deprecated for era changes.

**Gotcha (PowerShell 5.1):** .ps1 files saved as UTF-8 *without BOM* are read as CP1252 — an em-dash becomes `â€”`, and the trailing `”` is treated as a real string delimiter by the tokenizer, producing baffling "missing terminator" parse errors pointing at innocent lines. Keep .ps1 files pure ASCII (or save UTF-8 *with* BOM).

---

## 2026-07-13 — Server locked to Classic (was expansion 19!); daily DB backups established

**Era:** `Expansion:CurrentExpansion` was **19** (RoF) — not 1/Kunark as earlier entries assumed — which is why era-gated content (e.g. `A_Legendary_Hill_Giant`, min_expansion 11, in commons) was live; 1,705 future-era spawn2 rows were eligible, per-zone by boot time. Locked to **Classic (0)** via the GM tool endpoint: level cap 50, 511 zones locked, 6,587 AA ranks hidden, MOTD set, Classic 2D models in eqclient.ini, AA visibility left open (multiclass). ALL zone processes killed so every spawn list rebuilt under era 0. **Pending:** Darth was online during the cap and re-saved at 85 — needs the recap UPDATE re-run after logout (user to confirm).

**Backups:** none existed anywhere. Added `tools/backup-peq.ps1` (in-container mysqldump|gzip → `backups/peq_<ts>.sql.gz`, docker cp out — PowerShell corrupts piped binary stdout — 14-day retention, logs to backups/backup.log) + Windows scheduled task **NightcapPeqBackup** daily 04:00. First two backups taken (43.8 MB each); `backups/` gitignored. Backup was taken BEFORE the era change, per the instance_list lesson.

**Direction note:** the eq-solo-gm "GM tool" is homebrew and not authoritative — per user, ignore it for server ops going forward; a future pass will revisit making server-wide changes accessible alongside Spire.

---

## 2026-07-13 — Instance Keepers were never in the live DB; setup SQL had an ID collision

QA found no keeper NPC in Befallen: `instance_keeper_setup.sql` (committed 2026-06-22) **was never applied to the live DB**. Worse, applying it as-written collided — its "unused" 998001–998007 npc_types ids belong to existing `a_swooping_bat` NPCs, and the script's `ON DUPLICATE KEY UPDATE` / `INSERT IGNORE` clauses silently corrupted them (bat lastnames overwritten, bat NPCs wired to dungeon-entrance spawns) instead of erroring. Reverted surgically (bat lastnames restored to '', my spawn2/spawnentry/spawngroup rows deleted), rewrote the script on **999227–999233** (verified free in npc_types AND spawngroup), with plain INSERTs so any future collision fails loudly. Applied; all 7 keepers verified in DB.

**Gotchas:** (1) a script in git ≠ applied to the live DB — verify rows exist, not files. (2) Never claim an ID range is free without checking every table it touches. (3) `INSERT IGNORE`/`ON DUPLICATE` in setup scripts turn collisions into silent corruption — use plain INSERT and let it error. (4) New spawn2 rows need `#repop` (placeholder coords — `/loc` and UPDATE spawn2 to fine-tune).

---

## 2026-07-13 — Client crash zoning into classic zones: missing s3d files, full audit + restore

"Crash zoning into West Commonlands" was a **client-side** failure, not a server bug: the RoF2 client bailed with `Unable to find specified world file [commons.s3d]` (see `Client_RoF2_Dev\everquest_rof2\Logs\dbg.txt` — always check this file first for zone-in crashes; the server-side symptom is just `kicked, reason [Dropped by world CLE subsystem]` ~40s after connect, with the zone process alive).

This RoF2 package ships classic `_chr.s3d`/sound files but had **lost the geometry (`.s3d`) and `_obj.s3d`** for several classic zones. Audited all 484 DB zones against the client: era-relevant gaps were `commons`, `highpass`, `misty`, `tox`, `hateplane`. Restored from github.com/GiverofMemory/NostalgiaEQ-Client (raw files, PFS headers verified, no overwrites of existing files). Post-audit: zero era-relevant gaps (remaining: `cshome` unused, `powar`/`qvicb`/`barter` beyond era lock). In-game verification pending.

**Gotcha:** `nektulos`, `lavastorm`, `highpasshold` exist only as post-revamp `.eqg` in this client — they load, but classic spawn coords may sit under the new terrain. Check on first visit.

---

## 2026-07-13 — Instance Keeper: fixed broken Perl DB API calls

`quests/global/Instance_Keeper.pl` used `$DB->prepare()` + `fetchrow_hashref()` — neither exists in this build (no `$DB` injection; the exposed class is `Database` with `fetch_hashref`). Effect: the helper died mid-event — on 'enter' the player was **assigned** to the instance (AssignToInstance runs first) but never teleported (`_safe_coords` died before `MovePCInstance`); 'join' died resolving the leader's char id. Fixed both helpers to `Database->new()` + `prepare`/`execute`/`fetch_hashref` with an undef-guard on prepare. Live file + `server-mods` mirror synced; `perl -c` in-container passes.

**Gotcha:** running zones cache Perl scripts — kill the dungeon-entrance zone processes (or wait for fresh dynamic boots) before testing.

**Second bug, same disease (found in QA, fixed same day):** the script also called `$client->GetCharacterID()` — the **C++** method name. The Perl binding is `CharacterID()` (`perl_client.cpp`). Symptom in-game: `Perl runtime error: Can't locate object method "GetCharacterID" via package "Client"` on hail. Rule: quest scripts must use the names registered in `perl_*.cpp` bindings, not C++ names — when in doubt, `grep '"MethodName"' akk-stack/code/zone/perl_*.cpp`. (`Group::GetMember` returns a `Client*` in Perl, so `$member->CharacterID()` works directly.) QA-verified working in-game.

**Third bug (QA): instances were empty — no mobs, no doors.** The script created **version 1** instances, but spawn2/doors rows only exist for version 0; non-zero instance versions load only their own version's content, i.e. nothing. Changed `$INSTANCE_VERSION` to **0** — a version-0 instance inherits the full base-zone population while the instance id keeps it private. Orphaned empty v1 instances purged from `instance_list`.

**Process note / mea culpa:** the purge (`DELETE FROM instance_list WHERE version=1`) was scoped too broadly and also removed 10 stale pre-existing instance rows (paw, nektulos, lavastorm, droga, citymist, nurga, skyshrine, sirens, bazaar, griegsend — ids 1–11, old artifacts, nothing referenced them; 1 orphaned `instance_list_player` row cleaned). No backups existed to restore from. Lesson: scope destructive SQL to exactly the rows you created (`AND zone=...`), and take a `make mysql-backup` before any DELETE. Also noted: **no DB backups exist on this server at all** — worth scheduling.

---

## 2026-06-23 — Multiclass AA rework: mask-only access, clean revoke, de-crufted aa_ability

The multiclass AA feature kept breaking because The Ancient Chronicler **mutated the global `aa_ability` table** on every class selection (OR-ing the base-class bit into secondary AAs + name prefixes) and **revoke undid none of it**. This accumulated irreversible cruft — on the live DB, 416 non-Paladin AAs had been falsely OR'd into "Paladin-usable" (670 vs the vanilla 254), plus 525 stale/duplicate `[XXX]` name prefixes.

**Root insight:** access is already granted by the per-character multiclass *mask* (`m_multiclass_mask`, see the load-order fix below). The `classes |= base_bit` mutation was redundant *and* the source of the cruft — it also broke labelling (the `(classes & base)=0` precondition was corrupted, so e.g. `[MAG]` never applied).

**Changes:**
- **One-time cleanup** (`eq-solo-gm/scripts/multiclass_aa_cleanup.sql`): restored every stock AA's `classes` + `name` from the pristine PEQ dump (`/home/eqemu/code/utils/sql/peq_aa_tables_post_rework.sql`) via a scratch DB joined on `aa_ability.id`. Only `classes`/`name` touched — `first_rank_id` left intact, so the `aa_ability`↔`aa_ranks` link and players' purchased AAs (which reference `first_rank_id`) are preserved. Custom AAs (not in the dump, e.g. PoK attunement) untouched. Result: 0 prefixes, vanilla class bitmasks.
  - Gotcha hit during this: `aa_ability.id` ≠ `first_rank_id`. id 194 is "Unfailing Divinity"; "Holy Steed" merely has `first_rank_id`=194. Don't confuse the two when sanity-checking.
- **Labels baked statically** (`eq-solo-gm/scripts/multiclass_aa_labels.sql`): per-selection name prefixing was abandoned — AA names are cached at zone boot, so a label only appeared after `#reload aa`, which public players don't have. Instead, every single-class AA is tagged once with its class (`[WIZ] Mana Burn`, `[BRD] …`; 1210 tagged, shared/general AAs untagged). Tags are permanent and global; the per-character mask decides which a player sees. **No per-player reload ever.**
- **Chronicler now touches `aa_ability` zero times** — `_apply_class` only writes `character_multiclass`/qglobals + the spells_new/skill_caps patches; `_revoke_slot` only clears `character_multiclass`/qglobals. Access and revoke are purely the mask. Purchased AAs aren't deleted (rows persist, reactivate if the class is re-added — lossless round-trip).
- **Selection gating** reads `character_multiclass` (not `%qglobals`, which isn't populated on this NPC) via `_get_classes`, so the NPC correctly caps at two extra classes.
- **Selection gating bugfix:** the Chronicler gated on `%qglobals` (`mc_class2/3`), which isn't reliably populated on this NPC → `$c2/$c3` were always 0, so players could select classes endlessly (each overwriting `class2`). Now reads current classes from `character_multiclass` (the authoritative table) via a `_get_classes` helper, with a defense-in-depth guard in `_apply_class`. Both extra slots full → selection refused.
- **Scope:** AAs only. The `spells_new` scribing patch and `skill_caps` expansion are unchanged (secondary spells/skills require global patches because RoF2 gates scribing client-side) — revoking a class does NOT remove its spell/skill access, by design.

Deploy: ran cleanup SQL, restarted zones (aa_ability loads per-zone from DB at boot — no shared-memory regen needed for AAs).

---

## 2026-06-23 — Tiered loot system (Rare / Epic / Legendary)

4-tier rarity across all equippable gear + bags. T1 = every existing item (unchanged); T2–T4 are stat-scaled copies that drop progressively rarer.

**Items** (`eq-solo-gm/scripts/tiered_loot_setup.sql`): ~63.7k copies per tier generated via a stored proc that clones rows through a temp table (items has 285 cols — can't enumerate). Packed ID scheme (see ID cap below): Rare `base+200000` ×1.20, Epic `+400000` ×1.45, Legendary `+600000` ×1.75. Positive stats only; haste/delay/req-levels/effects untouched; negatives left as-is. Bags get +2/4/6 slots, +25/50/100 WR, →Giant. Name tags ` (Rare|Epic|Legendary)`.

**RoF2 item-ID cap = 1,048,575.** Item *links* encode the id as `%05X & 0x000FFFFF` (`common/say_link.cpp`), so ids above that wrap and link to the wrong item (the original `+1,000,000` scheme failed in-client — link resolved to a different item). Inventory/summon use full 32-bit ids, but links are the binding constraint. All tier ids stay packed under the cap (max ~820k).

**Drop mechanic** (`akk-stack/code/zone/loot.cpp`, `NPC::AddLootDrop`): one hook at the chokepoint every dropped item passes through. Base items (id < 200000) that are equippable/bags roll `Int(1,10000)`; on a hit it swaps `item2` for `GetItem(id+offset)`. Zero loot-table edits; covers all current+future NPCs. Tunable via `Zone:LootTier{Rare,Epic,Legendary}Chance` rules (1000/200/25 = 10%/2%/0.25%), added in `common/ruletypes.h`.

**Class epics** are auto-Epic: excluded from tier generation (so the hook's `GetItem` returns null → no random upgrade). Legendary epics generated explicitly at `base+800000` ×1.75, granted only by the **Legendary Ascension** quest (`akk-stack/server/quests/poknowledge/Epic_Forgemaster.pl`, NPC 999226 in PoK): carry your epic unequipped + hand in 8× *Essence of the Legend* (item 900000, ~1% global drop on lvl 55+ via `global_loot`) + 100,000pp → epic removed, legendary granted. No-drop-safe (epic detected/removed from inventory via CountItem/RemoveItem; only the tradeable essence + plat are handed in — no-drop items can't be put in a trade window).

**Deploy:** run the SQL, rebuild zone, regenerate shared memory (`./bin/shared_memory` — items are served from a shared-mem cache, so new items need it), restart all zones.

**Open item:** the user wanted item-name *text* colored blue/purple; RoF2 has no per-item name-color field and the client is read-only, so rarity is shown via name tags instead.

---

## 2026-06-22 — AA-vanishes-on-relog: REAL root cause found (load-order vs multiclass mask)

The recurring "AAs I buy disappear on zone/relog, and the points are not refunded" bug — finally the actual cause, not a symptom. Affected **every character**, not just multiclass ones (reproduced with Origin, an all-class `classes=65535` AA).

**Root cause:** the multiclass mod changed `CanUseAlternateAdvancementRank()` (aa.cpp:1635) to gate on `GetClassMask()` (the multiclass mask `m_multiclass_mask`) instead of computing the class bit inline. But `m_multiclass_mask` is **0 until `LoadMulticlassMask()` runs**, and the connect order is:

1. `OP_ZoneEntry` handler → `LoadAlternateAdvancement()` (client_packet.cpp:1536) loads each owned AA, calling `CanUseAlternateAdvancementRank()` per AA. **Mask is still 0 here.**
2. `OP_ClientReady` → `CompleteConnect` → `SendZoneInPackets()` → `LoadMulticlassMask()` (client.cpp:841). Too late.

With a 0 mask, `a->classes & 0 == 0` → `CanUse` returns false for **every** AA → `LoadAlternateAdvancement` (aa.cpp:1511) silently skips it. The AA isn't loaded into memory; the `character_alternate_abilities` row survives (so the point still reads as spent) but the ability is gone and the point is never refunded. At *purchase* time the mask was already populated (player fully connected), so buying worked — the asymmetry that made it look intermittent.

**Fix:** call `LoadMulticlassMask()` immediately before `LoadAlternateAdvancement()` in the ZoneEntry handler (client_packet.cpp, right after `ReloadExpansionProfileSetting()`). Rebuilt zone, restarted all zones.

**Self-healing:** previously-dropped AAs were never deleted from `character_alternate_abilities` (SaveAA's `ReplaceMany` doesn't delete unlisted rows), so with the correct mask they reload on the next zone-in and the points reconcile.

**Latent issue left as-is:** `LoadAlternateAdvancement` still *drops* (rather than refunds) any AA that genuinely fails `CanUse` (e.g. a real expansion mismatch), losing the points. Not hit by normal play now that the mask is correct; revisit if an expansion-gated AA ever legitimately fails.

---

## 2026-06-22 — Multiclass vendors reworked: 4 archetypes, restocked, relocated, Sphinx Chronicler

Replaced the 3 "Keeper" spell vendors with **4 archetype vendors** clustered at the Crescent Reach stone in PoK, and gave the Chronicler a Sphinx model.

- **NPCs 999221–999224** redefined as Arcane / Divine / Martial / Stalwart Loremaster (Caster / Priest / Melee / Tank). 999224's `npc_types` row had been deleted in the earlier cleanup — recreated, plus its spawngroup/spawnentry/spawn2.
- **Placement:** all 5 NPCs (4 vendors + Chronicler 999220) moved to a cluster around (-118, 30, -156.87), Turd's loc by the Crescent Reach stone. PoK floor z = -156.87.
- **Chronicler model → race 21 (King Xorbb / Beholder eye)**, size 8. (First tried race 86 Sphinx, but it's invisible without Luclin models on; Xorbb is a classic model that renders on old graphics.)
- **Bag vendor** added: NPC 999225 "Bartholomew Packwell", merchant 99225 — stocks one container of each distinct slot size 8→40 (best per size: Giant bagsize, highest weight-reduction). 22 bags.
- Cluster final position: just south of Mister Magelo (202388) at y≈248–264, z=-125, clear of the tree.

**Vendor restock — root cause the vendors were empty:** the GM tool's `/api/vendors/refresh` (`eq-solo-gm/api/server.cjs`) queries `items.spellid` and `items.expansion`, **neither of which exists in this DB**. The scribable spell id is in `items.scrolleffect`; there is no `items.expansion` column. So the endpoint errored every call and never stocked anything. Restocked directly in SQL using `scrolleffect`, gated by spells_new scribe level ≤ 60 (server is expansion 1 / Kunark):

| Vendor | merchantid | classBits | items |
|---|---|---|---|
| Caster (Nec/Wiz/Mag/Enc) | 99221 | 15360 | 1113 |
| Priest (Clr/Dru/Shm) | 99222 | 546 | 685 |
| Melee (Mnk/Rog/Ber/Brd/Rng/Bst) | 99223 | 49608 | 358 |
| Tank (War/Pal/SK) | 99224 | 21 | 237 |

Pure-melee classes (War/Mnk/Rog/Ber) have no scribable spells at exp 1, so Melee stocks Brd/Rng/Bst and Tank stocks Pal/SK.

**Gotcha — merchant NPCs need class 41.** An NPC is only right-clickable to shop if `npc_types.class = 41` (Merchant); `merchant_id` alone just links the inventory. The vendors were initially given their archetype classes (12/2/7/1) and couldn't be opened — fixed to class 41. (Also: npc_types/merchantlist/quest scripts are cached at zone boot, so changes to them need a full zone *restart*, not `#repop`. And dynamic-pool zones run as a bare `bin/zone` with no zone name in the command line — find the live one via its log filename `<zone>_..._<PID>.log`, not `pgrep -f "zone poknowledge"`.)

Full reproducible setup is in `eq-solo-gm/scripts/multiclass_setup.sql` (rewritten sections 2/3/5/6). **`/api/vendors/refresh` in the GM tool is still broken** (wrong column names) — left as a separate TODO.

Apply: changes are live in the DB; `#repop` PoK to spawn/move the NPCs.

---

## 2026-06-22 — Moved ftp-quests passive port range off Hyper-V reserved range

`docker-compose.yml` — `ftp-quests` passive FTP ports moved `30000-30049` → `21000-21049` (both `FTP_PASSIVE_PORTS` env and the published port mapping; they must match). Control port stays 21, so FTP clients need no change.

**Why:** after a host reboot, Windows `winnat` reserved the dynamic range 29995–30194, which overlapped the old passive range. Symptom: `make up`/`docker compose up` aborts with `ports are not available: ... bind: An attempt was made to access a socket in a way forbidden by its access permissions` on a port like 30040, and the abort also skips any services compose hadn't started yet (phpmyadmin, peq-editor → their nginx proxies then crash-loop with `host not found in upstream`).

**Gotcha:** Hyper-V/WSL dynamic port reservations shift on every reboot and live in the ~29995–50000 area. Keep host port mappings below that (21xxx is safe). Check current reservations with `netsh int ipv4 show excludedportrange protocol=tcp`. Bouncing `winnat` (`net stop winnat && net start winnat`, elevated) frees them temporarily but the conflict recurs next reboot — moving the port is the durable fix.

---

## 2026-06-22 — AA-vanishes-on-relog: root cause was stale zone processes

The recurring "purchased AA disappears after I zone/relog" bug was **not** a code bug — the `LoadMulticlassMask` 0-indexed fix (`1 << (GetClass()-1)`) was already correct in source and in the latest zone binary (built 15:33). The problem: several zone processes (qeynos, commons, freporte, freportw, arena, + static pool) were still running from 15:28 — *before* the rebuild — so they served the old buggy binary with mask `1 << GetClass()`.

A process runs whatever binary existed when it started. Killing only *some* zones after a rebuild leaves the rest stale. Whether an AA survived a relog depended entirely on which zone process the player was in: for a Paladin (class 3), buggy mask = `8`, but Paladin AAs have `classes=4` → `4 & 8 = 0` → filtered out of `SendAlternateAdvancementTable` on every zone-in. The data was never deleted from `character_alternate_abilities` — it just stopped being sent to the client.

**Fix:** killed *all* zone processes so eqlaunch respawned every one against the current binary. No code change.

**Gotcha (reinforced):** after `make zone`, you MUST kill **every** `bin/zone` process, not just the zone you're testing in. Dynamic zones already booted keep the old binary until killed. Verify with `ps -eo pid,lstart,cmd | grep '[b]in/zone'` — every start time must be *after* the binary mtime (`ls -lL --time-style=full-iso /home/eqemu/server/bin/zone`).

---

## 2026-06-22 — Multiclass System

A system that lets characters learn up to 2 additional class disciplines beyond their primary. Gated at level 20 (2nd discipline) and level 50 (3rd discipline).

### NPC hub
- **The Ancient Chronicler** (NPC ID 999220) placed in Plane of Knowledge at (-80, -25, -157)
- Companion NPCs 999201–999224 removed — all redundant with existing PoK trainers/vendors; skill training is handled programmatically by the script
- Setup script: `eq-solo-gm/scripts/multiclass_setup.sql`

### Perl quest script
**`akk-stack/server/quests/poknowledge/The_Ancient_Chronicler.pl`** — new file

Key design choices:
- Uses qglobals (`mc_class2`, `mc_class3`, scope 5 = character-permanent) as the in-session source of truth, not direct DB reads. The `character_multiclass` table is the persistent store read by the C++ zone binary on zone-in.
- `_apply_class()`: inscribes spells from `spells_new`, patches `spells_new` so base class can memorize secondary spells, expands `skill_caps`, unlocks AAs via bitmask OR on `aa_ability.classes`, trains skills to cap.
- `_revoke_slot()`: removes only spells exclusive to the revoked class (not shared with base or kept class). Promotes slot 3 → slot 2 when revoking slot 2.

**Deleted `akk-stack/server/quests/poknowledge/999220.lua`** — this ID-based Lua script took priority over the name-based Perl script for all events. EQEmu loads `<npcid>.lua` before `<NPC_Name>.pl` — if both exist, the Lua wins.

### C++ changes (akk-stack/code/zone/aa.cpp + client.h)
- `LoadMulticlassMask()` — runs on every zone-in; reads `class2`/`class3` from `character_multiclass`, builds `m_multiclass_mask` for AA display filtering.
- `SetMulticlassSlot(slot, class_id)` — persists discipline choice to `character_multiclass` (called from Lua; currently unused since Lua script was deleted, but preserved for future use).
- `GetClass2()`, `GetClass3()`, `GetClassMask()` — Lua-exposed accessors.

**Bug fixed (same session):** `LoadMulticlassMask` built the mask with `1 << GetClass()` (1-indexed), but `aa_ability.classes` uses `1 << (class_id - 1)` (0-indexed, Warrior = bit 0 = value 1). For Warrior (class=1), the mask was `2` instead of `1`.

Symptom: purchased base-class AAs disappeared on every zone. Root cause: `AutoGrantAAPoints()` runs on every zone-in, calls `SendClearPlayerAA()` + `SendAlternateAdvancementTable()`. The bad mask caused base-class AAs to fail the class filter and never be re-sent after the clear.

Fix: `1 << (GetClass() - 1)` and `1 << (m_class2 - 1)` / `1 << (m_class3 - 1)`.

To rebuild after C++ changes: `docker exec akk-stack-eqemu-server-1 bash -c "cd /home/eqemu/code/build && make -j$(nproc) zone"`. The server binary is a symlink — no copy needed. Kill zone processes after build so they restart with the new binary.

### Database schema
**`character_multiclass`** table in `peq`:
```sql
CREATE TABLE character_multiclass (
    id              INT UNSIGNED NOT NULL AUTO_INCREMENT,
    character_id    INT UNSIGNED NOT NULL,
    class2          TINYINT UNSIGNED NULL DEFAULT NULL,
    class3          TINYINT UNSIGNED NULL DEFAULT NULL,
    applied_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    UNIQUE KEY uq_character_id (character_id)
);
```
The `id` auto_increment PK is required — `SetMulticlassSlot()` in the C++ does `SELECT id FROM character_multiclass WHERE character_id = ?` to check row existence before deciding INSERT vs UPDATE. Originally created with `character_id` as PK (missing `id`), causing error 1054 on every interaction. Fixed via `ALTER TABLE`.

### Bug fix — zone crash on NULL class2/class3
`LoadMulticlassMask()` in `aa.cpp` called `Strings::ToUnsignedInt(row[N])` without checking for null. When `class2` or `class3` is SQL NULL (valid state for a character with only one discipline set), `row[N]` returns `nullptr`, and constructing a `std::string` from null throws `std::logic_error` → `std::terminate`. Fixed with null checks: `row[N] ? Strings::ToUnsignedInt(row[N]) : 0`. Also patched existing rows: `UPDATE character_multiclass SET class3 = 0 WHERE class3 IS NULL`.

### Gotchas discovered
1. **EQEmu script priority**: `<npcid>.lua` always loads before `<NPC_Name>.pl`. If both exist for the same NPC, the Lua handles all events.
2. **`spawn2` has no `enabled` column** in this EQEmu version. Omit it from INSERTs.
3. **`character_spells` column is `spell_id`**, not `spellid`.
4. **`aa_ability.classes` is 0-indexed**: Warrior (class 1) = bit 0 = value 1; Cleric (class 2) = bit 1 = value 2. Use `1 << (class_id - 1)` in both Perl and C++.
5. **C++ zone binary auto-initializes `character_multiclass` rows** on player zone-in (via `LoadMulticlassMask` + `SetMulticlassSlot`). Table schema must match what the binary expects or every zone-in produces SQL errors.

---

## 2026-06-22 — AA window class prefix (issue #4)

`akk-stack/server/quests/poknowledge/The_Ancient_Chronicler.pl`

When a player learns a secondary/tertiary discipline, AA abilities that are newly unlocked for their base class get their names prefixed with the source class abbreviation — e.g., `[NEC] Lich Form`, `[WIZ] Mana Burn`. The prefix appears in the Title column of the AA window.

- Added `%CLASS_ABBREV` hash (traditional EQ 3-letter codes: WAR, CLR, SHD, SHM, etc.)
- In `_apply_class()`: prefix UPDATE runs **before** the classes bitmask expansion so the `(classes & base_bit) = 0` condition still identifies newly-unlocked AAs. `NOT LIKE "$prefix%"` guard prevents double-prefix on re-application.
- Prefixes are NOT stripped on revoke — the AAs remain accessible after revoke and the prefix still accurately indicates origin class.

The RoF2 client binary has no EQType or mechanism for a dynamic "Class" column, so modifying `aa_ability.name` is the only server-side path to surfacing class origin in the AA window.

---

## 2026-06-22 — Discipline login notification (issue #3)

`akk-stack/server/quests/global/global_player.lua` — added to `event_connect`

On every login, if the character has any secondary/tertiary disciplines set in qglobals (`mc_class2`, `mc_class3`), a yellow chat message lists all active disciplines:
`Active disciplines: Warrior (Primary) | Necromancer (Secondary) | Wizard (Tertiary)`

No client XML changes required — uses existing qglobals set by The Ancient Chronicler. The character window in RoF2 has no EQType binding for secondary/tertiary class data; the client binary is fixed and can't be modified, so a login message is the cleanest non-invasive alternative.

---

## 2026-06-22 — Instance system (issue #1)

`eq-solo-gm/scripts/instance_keeper_setup.sql` — NPC types, spawngroups, spawn2 for 7 starter dungeons (befallen, unrest, highkeep, najena, cazicthule, permafrost, soldungb).

`akk-stack/server/quests/global/Instance_Keeper.pl` — single generic script used by all Instance Keeper NPCs. NPC's `lastname` field stores the target zone short name. Handles: hail (status + options), enter (create if needed + move), join (follow group leader's instance), reset (popup confirm → destroy + recreate), status (remaining time).

Key Perl API used: `quest::CreateInstance`, `quest::DestroyInstance`, `quest::GetInstanceIDByCharID`, `quest::AssignToInstance`, `quest::AssignToInstanceByCharID`, `quest::MovePCInstance`, `quest::GetInstanceTimerByID`.

Group behavior: leader says 'enter' → all online group members are assigned to the same instance and notified via Message(). Non-leaders say 'join' to teleport in.

Instances use version=1, duration=43200s (12h). Placement coordinates are pulled from `zone.safe_x/y/z` as a starting point — adjust per zone with `/loc` in-game.

---

## 2026-06-22 — Bard songs permanent (issue #5)

`eq-solo-gm/scripts/bard_songs_permanent.sql` — new file

Updated 430 bard beneficial buff spells in `spells_new` to `buffdurationformula = 50` (DF_Permanent). Targets spells where `classes8 > 0 AND classes8 < 255 AND buffdurationformula != 0 AND goodEffect = 1`. Skips DDs, debuffs, charm, and mez (goodEffect = 0). Script is idempotent — already-permanent spells are excluded.

No zone restart required — spell data is read fresh per cast.

---

## 2026-06-22 — pok_attunement_setup.sql fixes

`eq-solo-gm/scripts/pok_attunement_setup.sql` corrected to match actual DB schema:
- `spells_new` column names: `GoodEffect` → `goodEffect`, `base1` → `effect_base_value1`, `limit1` → `effect_limit_value1`; added missing string columns (`you_cast`, `other_casts`, `cast_on_you`, `cast_on_other`, `spell_fades`, `descnum`, `typedescnum`, `effectdescnum`, `effectdescnum2`)
- `aa_ability` INSERT: added `deities`, `charges`, `first_rank_id`, `enabled`, `reset_on_death`, `auto_grant_enabled`; removed legacy columns
- `aa_ranks` INSERT: removed `aa_id`, `passive`, `total_cost`, `rank`; added `prev_id`, `next_id`

## 2026-09-12 - Project baseline and balance working agreement

Recorded the owner's core requirement: solo-preferred play must remain demanding
and balanced. Spell damage/healing caps above 250 and NPC HP adjustments may be
considered when supported by encounter and build evidence. Added
`docs/project-understanding.md` with a read-only source/PEQ assessment, current
percentage-based spell/healing scaling, source/mirror drift, the missing level-1 AA
XP rule override, and item-generation reproducibility gaps. No gameplay, database,
binary, or client changes were made.
