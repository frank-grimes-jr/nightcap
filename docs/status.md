# Current Nightcap status

## Death EXP penalty removal — candidate October 17

The [no-death-EXP configuration](ops/no-death-exp-loss-20261017/README.md) is tested
and ready for owner release approval. `Character:DeathExpLossLevel=256` disables
normal death EXP loss at all supported levels through a global rules reload.
The read-only production check still observes 10; nothing is activated. Two focused
tests include 2,048 native cases and old-policy controls. Other death mechanics
and old corpse resurrection EXP remain. Wiki notices are prepared but unpublished;
main promotion, production activation and exact in-game QA remain pending.

## Raid and Grind dungeons — deployed for live QA October 16

The [dungeon release](dungeons/README.md) adds seven dungeon modes, 52 explicit
objectives, 330 reward definitions, private Classic Cazic-Thule and durable
UUID-based progress/corpse/reward recovery. Guarded installation/enablement and
concurrent allocation, enrollment, reset and duplicate-receipt checks pass in
an isolated local database. Native policy/credit/spawn and inventory/corpse
adapter checks are separate from the [fourteen-mode in-game QA](dungeons/QA.md).
Owner-authorized main promotion and OVH deployment are complete. All twelve
zone workers and world match the paired build, revision 2026101601 is enabled,
and access is open. The regenerated cache preserves 309,410 old items and adds
330; stopped checks preserve 47 player and 11 existing custom tables. Signed
client 2026101501 remains unchanged. The initial preflight DB memory-limit
restart recovered before feature SQL; its cause and correction are recorded in
[deployment evidence](dungeons/deployment/README.md). CT terrain/path validation,
level-50 Vox/Nagafen balance and full owner acceptance remain pending. On October
16, Palwar confirmed Keeper selection, Raid entry and a named kill. The Tasks
objectives were blank despite retained ledger credit. The [journal repair](dungeons/journal-repair/README.md)
is on main and deployed after the explicitly authorized restart. All 12 zone
workers match the candidate; cache and stopped player/run preservation checks
pass. The owner replied "Confirmed" after the Befallen journal retest instructions,
closing the reported display issue. Full-clear rewards remain unconfirmed. Existing
unmanaged instances retain their legacy behavior. The public [Raid & Grind guide](https://wiki.nightcapgame.org/dungeon-modes.html)
is published as `20261016-dungeon-journal-v1`; all 465 public hashes and preservation
checks pass. [Publication evidence](dungeons/wiki-publication/README.md) is
separate from pending gameplay acceptance.

## Equipment race policy — deployed for live QA October 16

The [equipment race fix](releases/equipment-race-policy-20261016/README.md) is
merged in PR #204 and deployed after the authorized server restart. Class match
now allows every playable race for ordinary wearable items and augments;
non-player definitions and other equipment restrictions remain. The full
309,410-item production cache comparison preserves every other field, 47 player
and 11 custom tables, current content/rules/quests and signed client 2026101501.
All 12 zones retain the latest AA-duration fix, with zero new restarts/detected
errors; access is open. Bronze Knuckles remains primary-only. Native, cache and
37 operator controls pass; live Bronze Knuckles/inspection/relog QA is pending.

## Multiclass equipment and inspection — published for live QA October 16

The [equipment correction](releases/multiclass-equipment-20261015/README.md) fixes
Forged Javelin placement for Paladin/Warrior/Monk and unheld equipment appearing
green. Proxy 0.9.1-dev uses current held classes in cursor and inspection paths;
native restrictions and canonical scroll access remain. Native regressions,
scope coverage, x86 builds, full Go suite and catalog checks pass. PR #202 merged;
signed release **2026101501** verifies all 106 hosted assets and the production
signature. Only DLL/catalog changed; all five services are unchanged. The owner
confirms javelin use in the follow-up; broader live gameplay QA remains pending.
No server/DB change in that client release.

## Temporary AA buffs — deployed for live QA October 16

Killing Spree and related activated/proc/recourse buffs now bypass blanket
player/pet permanence in the deployed fix. Native positive timers remain unchanged;
affected saved permanent sentinels receive one remaining tick. Ordinary blessings
retain permanence. All 30 focused checks, full retained-source zone link and
read-only production content verification pass. Owner-authorized main/OVH
rollout and 33 recovery checks pass: all 12 zones match the new binary, with zero
restarts/detected errors and access open. Player/custom data, quests, rules and
signed client 2026101501 are preserved. Owner gameplay QA remains open. See the
[release evidence and exact QA](releases/aa-temporary-buffs-20261015/README.md).

## Stacked tradeskills and Craft All — deployed for live QA October 13

Owner-authorized PR #200 is on main and OVH with signed game release **2026101304**
and proxy **0.9.0-dev**. Material stacks retain leftovers; Craft All repeats the
selected recipe with native requirements, outcomes and output placement. All 12
zones and 106 hosted signed assets verify, with zero candidate restarts/detected
errors. Closed-access checks preserved 47 player / 11 custom tables, current
rules/content/quests and other binaries, including the divine-summon loader.
Player access is open. Close EQ and use launcher Play. Owner gameplay and visual
acceptance remain pending. [Behavior, evidence, recovery and exact QA](tradeskills/README.md).

## Unrest waypoint — entrance relocation deployed October 13

Live inspection found the portal/recall 921 units from the floating-eye Keeper.
Owner-approved PR #198 moved the waypoint and recall to `/loc -38,52,3`, preserving
player discoveries and unrelated saved state. All 68 local checks, independent
review, fresh full-backup restore/forward/inverse rehearsal and closed-access
preservation checks pass. The current runtime/client pairing is unchanged; all
12 zones are healthy and access is open. Owner portal/discovery/recall QA remains
pending. [Cause, production evidence and QA](ops/unrest-waypoint-20261013/README.md).

## Divine summoned weapons — deployed October 13

Owner-approved PR #197 is on main and live. Existing Paladin/Cleric hammer spells
already select Ascended definitions; the new item loader closes their FreeTrade
resale loophole without changing combat or spell access. All 44 definitions have
zero resale; every other byte in the 309,410-item cache is preserved. Native
forward/rollback rehearsal passed. Preserved 47 player / 11 custom tables and
current native binaries; all 12 zones are healthy and player access is open.
No client update is needed. In-game balance and visual acceptance remain pending.
[Scope, evidence and exact QA](releases/divine-summons-20261013/README.md).

## Passive AA — 20% deployed October 13

Owner-approved passive AA decreased from 40% to **20%**. Normal leveling XP,
full AA focus, 4,000 XP per point and existing progress are preserved. All 12
zones and world reloaded successfully without restarting; all five services
remain running. 129 native checks, nine recovery tests and independent review
pass. Palwar/Befallen gameplay and later-level balance QA remain pending.
[Evidence, rollback and exact QA](ops/passive-aa-twenty-20261013/README.md).

## Relaxed tradeskill workshop — deployed October 13

Owner-approved PRs #194/#195 are on main and live. Twenty-five NPCs form looser
crafting groups and a buffer-side service nook for the Chronicler, Bartholomew
and Tessa. Six stations and three native ornaments complete the layout. Exact
production afterimages, preserved player/content/runtime/public fingerprints,
full-backup restore and forward/rollback rehearsal pass. All 12 zones are healthy.
No client update is needed. Owner in-game appearance and interaction QA remains
pending. [Evidence, layout and exact QA](releases/tunnel-cozy-20261013/README.md).

## October 13 class AA expansion — deployed for OVH QA

The [26-line implementation and Triple Backstab repair](releases/aa-class-ranks-20261013/README.md)
is live on all 12 OVH zones. All 1,051 ranks remain available at level 1;
47 player and 11 custom tables were preserved, including purchases and points.
Native/policy, independent review and runtime checks pass. Signed notes 2026101303
are published; the signature and all 105 hosted files verify. All 12 AA zone
hashes were rechecked after separate tunnel maintenance restarted the runtime.
Gameplay acceptance remains pending; main was not promoted.

## October 13 class AA rank audit — implemented above

The [class-rank re-audit](audits/aa-class-ranks-20261013/README.md) recommends
Slay Undead 9 and deeper progression in 25 other lines, preserving level-1 access.
The target catalog adds 110 ranks. The implementation above repairs and tests
Triple Backstab's native level-55 activation gate for earned AA bonuses at any
level. The audit remains historical recommendation evidence; encounter balance
and THJ's exact Slay cap remain unverified.

## October 13 AA correction: level-1 access

Owner QA rejected the initial AA level gates. The correction opens all allowed ranks at creation and retains purchases. [Correction and QA](releases/aa-tbs-level1-20261013/README.md); live on OVH with all 12 zones verified and 239 purchases preserved. Signed notes release 2026101302 is published. Owner acceptance remains pending. The earlier small starter-list policy is superseded, not accepted.

## Earlier AA staging candidate — rejected in owner QA

The initial small starter list and character-level gates are superseded by the correction above. Historical deployment/preservation evidence remains in [the original receipt](releases/aa-tbs-20261013/README.md).

## Multiclass skills — corrective release deployed

Owner-approved PR #191 is merged to main and deployed with signed game release
**2026101301** / proxy **0.8.3-dev**. It fixes missed native purchase/offhand gates
and retained primary-only server skill progression/empty-fist checks. All 126
zone objects were rebuilt; all 12 running zones and 105 hosted client assets
verify. Preserved 47 player / 11 custom tables, zero new restarts/detected errors.
No skill/point/coin grants or cap rewrites. Close EQ and use launcher Play.
Owner confirmed the reported Palwar issue **resolved** on October 13, 2026.
Individual control/relog QA steps were not separately enumerated.
[Cause, deployment, recovery and exact QA](releases/multiclass-skills-20261013/README.md).

## Launcher patch summaries — published October 12

The patcher now presents concise Feature/Bug fix summaries for the latest signed
release and expandable previous patches, including during updates. Five recent
client releases are curated in `eq-launcher/patch-notes.json`. Go regressions,
desktop compilation, frontend build and 11 Chrome UI tests pass; rendered
patching layout was inspected. Owner-approved PR #186 is on main. Signed desktop
0.6.0/channel 2026101201 and game 2026101202 are hosted; all 105 client assets,
starter ZIP, guide and running services were preserved. Close EQ and the launcher,
then reopen the normal shortcut. Native player acceptance remains pending.
[Evidence, recovery and QA](releases/launcher-patch-history-20261012/README.md).

## Early spell scribing — deployed October 12

PR #185 is on main and live on OVH with signed game release **2026101203**.
Selected-class scrolls can enter the spellbook before their required level;
gem memorization and casting retain canonical levels. All 12 running zones
match, player/custom tables and rules/content were preserved, and the gateway
is open with zero new restarts or detected errors. Public HTTPS verifies the
signature and all 105 client files. Only DLL/catalog changed; launcher 0.6.0,
existing patch history and all other assets were preserved. Compiled regressions,
client/runtime and Go tests, 76 patch checks and independent reviews pass.
Owner scribe/relog/gem gameplay acceptance remains pending.
[Deployment, recovery and exact QA](releases/early-spell-scribing-20261012/README.md).

## Sell-all supply protection — deployed October 12

Owner-approved PR #183 is on main and live on OVH. `#sellall` and the merchant
Sell All button preserve food, drink, spell reagents such as Bone Chips, and
casting focus items in carried slots and bags. Existing loot payouts remain.
The compiled command passes 33 checks, seven existing resale/upgrade tests pass,
and eight recovery tests pass. All 12 running zone hashes match; gateway access
is open with zero new restarts or detected native/quest/database errors. A fresh
verified backup and closed-gateway player/content/rule preservation checks passed.
No client update is needed. Real inventory, payout and relog acceptance remains
owner in-game QA. [Deployment, recovery and exact QA](ops/sellall-supplies-20261012/README.md).


## Merchant Sell All button — resolved October 13

Owner confirmed the merchant button resolved on October 13. Owner-approved
PR #182 is on main. Initial signed client release 2026101201 added a
Sell All button to the shared merchant window, invoking the existing server
command. All 105 host files verified; 101 existing assets, all five services,
the desktop channel and starter were preserved. Close EQ and use launcher Play
to update. The owner confirmation closes this button issue; the checklist
remains available for regression testing.
[Evidence, recovery and exact QA](releases/merchant-sell-all-20261012.md).

## Instance Keeper and waypoint visuals — resolved October 13

Permafrost player QA confirmed the waypoint portal is visible and functional;
the remaining human was the separate Instance Keeper. PR #181 gives all seven
custom dungeon Keepers a small floating-eye appearance, preserving instance
controls and the portal. All 29 Perl assertions pass. Quest hashes, 12 completed
reloads, process continuity and service health were verified. No client update
or restart was needed. On October 13 the owner confirmed the reported visual
issue resolved after the Permafrost follow-up; this closes its acceptance gate.
The reply does not separately attest every zone or optional QA case.
[Evidence, rollback and exact QA](ops/keeper-visuals-20261012/README.md).

## Remove all item LORE - deployed October 12

Owner-approved PR #180 is on main and Items:DisableLore=true is live on OVH.
All 309,410 cached definitions have no LORE flag/group, including the 160,783
previously restricted definitions. All other item bytes, 46 player-state tables
and 11 custom tables were preserved. Fresh backup, all 12 zone hashes and
follow-up health checks passed; access is open. No client update is needed.
Manual combine/duplicate-equipment balance QA remains pending.
[Evidence and exact QA](releases/remove-item-lore-20261012/README.md).

## Character boost correction — deployed October 12

Owner-approved PR #177 is on main and the updated production GM is running.
Darthy is restored to level50 with165592026XP and250 training points, retaining
his earned XP and crediting225 omitted training points. Fresh backup, ten data
preservation hashes and post-restart checks passed. All services are running;
world/all 12 zones preserve the existing item-upgrade release. Actual client kill,
zone and relog acceptance remain pending. [Evidence and exact QA](ops/darthy-boost-20261012/README.md).

## Reusable item upgrades — deployed for live QA, October 12

Owner-approved PR #171 is merged into main and deployed. Artisan Veyra supplies the
free reusable box in the East Commonlands tunnel: four Polished copies become
one Exalted item, and four Exalted copies become one top-tier item. The complete
zone build and verified local deployment bundle pass, along with native inventory
regressions, 28 disposable database checks, quest and packaging tests. The fresh
backup and eight rollout recovery tests passed. The gateway is open, all 12 zone
processes match the release, and the new runtime has zero restarts or detected
native/quest/database errors. All 47 player-state tables, nine existing custom
tables and unrelated cached items passed preservation checks. Revision 2026101201
is enabled. Real client Combine, NPC appearance and balance acceptance remain
pending; deployment approval is not manual acceptance.
[Evidence, activation and rollback](releases/item-upgrades-20261012/README.md) ·
[Exact in-game QA](releases/item-upgrades-20261012/QA.md).

## Pet summon client crash — resolved October 12

Owner-approved PR #166 is merged into main. Signed client release 2026101101
preserves registers required by RoF2 when a pet arrives, addressing Darthy's
recorded crash. All 104 hosted files and the production signature verify;
runtime, ABI regression and 13 publisher recovery checks pass. No game restart
was needed. The owner confirmed the reported crash resolved on October 12.
Players receive the fix through the launcher. [Diagnosis, publication evidence and exact QA](ops/darthy-pet-crash-20261011.md).

## Waypoint portal visuals — deployed October 11

Owner-approved PR #163 is on main and live on OVH. Waypoint markers now apply
the stock portal effect over an invisible actor; the overlapping Instance Keeper
in Befallen remains available. All 24 automated checks passed. The quest hash
matches main, all 12 zone workers reloaded without reported quest errors, and
native processes were not restarted. No client update is needed. The owner
confirmed Permafrost portal visibility/function October 12 and the combined
visual issue resolved October 13 after the Keeper follow-up. Detailed optional
QA cases are not individually attested by that reply.
[Deployment, rollback and exact QA](ops/waypoint-visuals-20261011/README.md).

## Food and drink requirements — removed October 11

Owner-approved PR #162 is merged and live on OVH. Hunger/thirst penalties and
depletion are removed; nutrition packets stay full and eating/drinking requests
preserve inventory. Optional item bonuses remain. The full build, 349 compiled
regressions, eight rollout tests and all 12 running zone hashes passed. Player
access is open; saved-data checks and follow-up health checks passed. No client
update is needed. Native warning rendering remains owner acceptance.
[Deployment, recovery and exact QA](ops/food-drink-removal-20261011/README.md).

## Advanced loot stock images — published October 10

Owner-approved PR #151 is merged to main. Signed client release 2026101001
(proxy 0.8.0-dev) publishes the stock item icons, matching patch catalog and
Pet Info XML. Server verification covers all 104 files; no game service restart
was needed. Restart EQ and use launcher Play. Native visual acceptance remains
pending; [exact QA and release evidence](releases/advanced-loot/STOCK-ICONS.md).

## Production GM controls — activated October 10

The owner-local GM UI now reads OVH production over SSH and retains character,
account, rule, progression, vendor and client-setting controls. It adds player
access codes, verified password resets, maintenance/recovery and action history.
Owner-approved PR #143 is merged to main. Production GM writes and the two support
tables are active, with a verified private database backup. The registry now holds
the two owner-requested player codes, and the credential gateway is active. Password
resets and existing GM controls are available; offline edits require maintenance.
Era activation remains governed by committed era.json and catalog review.
[Entry point, evidence and exact QA](ops/production-gm-20261010.md).

## Player access independent of changing IPs — activated October 11

Signed desktop0.5.0/release2026101001 and the credential gateway are live. Owner and
Joe codes were issued privately. Cloudflare exempts only native GET/HEAD routes
from its player-IP check; both real codes passed public TLS WebSocket/native UDP
checks from an unlisted address, and invalid codes fail. Downloads and service
health passed. Joe's Windows login, remembered code and changed-network acceptance
remain open. [Activation and recovery](ops/player-access-20261011.md) and
[exact player QA](../deploy/production/PLAYER-ACCESS.md#exact-player-qa).

Updated October 11, 2026. This is the current status index; dated studies and
QA reports preserve their original evidence and are not live-state promises.

## NPC-targeted heals deployed for live QA

Owner-authorized PR #139 is on main and deployed to OVH. Player heals aimed at
NPCs resolve to the caster while retaining the combat target. The fresh build,
99 compiled regressions, five rollout tests and all twelve zone process hashes
pass. Saved player/custom data, rules, content and client assets are preserved;
access is open and follow-up health checks pass. In-game HP/animation acceptance
remains pending. No client update is required.
[Deployment, recovery and exact QA](ops/npc-heal-self-20261009/README.md).

## Crushbone entrance waypoint deployed

Published to main and deployed to OVH on October 11. The marker, saved marker
state and recall destination now use the entrance safe point
(`/loc -644, 158, 4`). Eight tests, three live transaction/rollback rehearsals,
exact database comparisons and service/12-worker health checks passed.
In-game grounding, discovery and recall acceptance remains pending.
[Deployment, rollback and exact QA](ops/crushbone-waypoint-20261009/README.md).

## Classic zone hunt and forge deployed for live QA

Owner-authorized PR #132 is on main and deployed to OVH. Forty-eight audited
Classic combat zones now have independent 0.5% augment/gear rolls, four qualities,
six-location augment support and atomic three-copy upgrades with `#zoneforge`.
Eight access-check zones stay disabled; cities/hubs stay reserved. All 448 item
definitions and 2,290 socket edits passed exact checks. Five hardened native
binaries, twelve healthy zones, full item-cache checks and closed-gateway
player/content/receipt preservation passed. The private player guide includes
the 48-zone catalog and current mechanics. Client/socket/encounter acceptance
remains open. [Deployment and recovery](releases/zone-loot-20261009/PRODUCTION.md)
and [exact owner QA](releases/zone-loot-20261009/QA.md).

## Advanced loot row controls deployed for live QA

Always Loot/Never Loot toggles are directly on each main-page item row, and a
confirmed empty loot queue closes the window. Owner-authorized PR #129 is on
main, and signed release 2026100901 / proxy 0.7.8-dev is published. Client build,
controller/runtime/layout, packaging and publication-recovery checks pass.
The other 101 assets and game services are preserved. Fully exit EverQuest and
click Play to update. Native rendering/gameplay QA remains pending.
[Scope, deployment evidence and exact QA](releases/advanced-loot/ROW-CONTROLS.md).

## Throw Stone deployed for live QA

Throw Stone now adds effective Spell Damage directly: 251 ordinary damage at
250 Spell Damage before other modifiers. The fresh hardened Linux zone build,
108 compiled production-method checks, 12 spell regressions and eight rollout
failure tests pass. Owner-authorized PR #127 is merged to main and deployed to OVH.
Post-deployment health checks passed and access is open. Gameplay QA remains
outstanding. [Scope and exact QA](releases/throw-stone-20261009.md).

## Passive AA leveling: 40% live

The owner increased passive AA from 20% to 40% on October 9, alongside unchanged
full leveling XP. AA focus remains 0/100. The guarded rule update, 129 native-method
checks and eight operation tests pass; world and all twelve zones reloaded without
restarting. Existing AA progress and other rules remain. In-game reward/persistence
and combined build balance acceptance remain open.
[Tuning, evidence and exact QA](ops/passive-aa-forty-20261009/README.md).
[Original implementation](releases/passive-aa-20261004.md).

## Nightcap loading artwork published

PR 124 is merged into main (`70fd26a`). Signed game **2026100407** and desktop
**0.4.0** are live on OVH. All 55 numbered loading screens and the resource
fallback now use the ten approved Nightcap paintings. All 104 public game files
and the desktop executable verify over HTTPS; the previous 48 game files,
stable starter, player settings and running services are preserved.
Fully close EQ and the launcher, then reopen the normal Nightcap shortcut to
receive the desktop and game update. Native decoding and installation/recovery
tests pass; viewport appearance and progress-text placement remain player QA.
[Release evidence, rollback and exact visual checks](releases/loading-screens-20261004.md).

## Universal trading and one-platinum NO DROP resale deployed

The policy deployed from main `1a5c0fe` remains active in the current zone-hunt
OVH image, with full-catalog verification repeated after that rollout. All 309,409 hosted definitions have
effective tradable flags, including saved attunement; the 171,561 original NO
DROP definitions sell for 1pp per unit at merchants and through `#sellall`.
Full-catalog verification, all five binary hashes, 12 zone workers, backup and
player/content/client preservation checks pass. That deployment retained client
2026100406; its game files are also preserved in loading-gallery release 2026100407.
Ordinary prices remain; the 448 new zone-hunt definitions have zero resale. Merchant previews may differ from the fixed receipt.
Player trade/sale acceptance and repeatable-reward economy QA remain open.
[Deployment, rollback and exact QA](releases/free-trade-20261004/README.md).

## NPC animation follow-up published for pet retest

The owner confirmed that 2026100404 repaired beetle walking/death, while
Enchanter weapons still twitched under stationary nameplates. PR 123 preserves
the graphics engine's native IVM identity, a second requirement beyond the
animation-family repair. Proxy **0.7.7-dev**, first published in 2026100406,
remains unchanged in current release 2026100407, alongside all 48 prior files
and the existing helmet assets.
Close EQ and press Play in the normal launcher to update. Pet idle/follow/combat,
zoning/relog and broader NPC visual acceptance remain open.
[Native cause, deployment and exact retest](releases/npc-animation-20261004/enchanter.md).

## Winged Paladin helmet snug-fit update

Blender/Unity assets and all 24 original-race/gender fits are built. Item 990500
exists in the live database and shared-memory cache with Classic raid stats.
Owner QA exposed two native requirements: contiguous head meshes and the actor's
shared material palette. Both are repaired in source 292aef4 and signed client
release 2026100403, published under the owner's live-testing instruction.
All 25 tests pass; 46 other client files and service identities/start times are
preserved. Game/DB are healthy. Camil 999521 uses head material 90.
The owner's latest screenshot confirms native Classic rendering on Camil, but
the shell is too wide. The revised fit narrows High Elf male by 22.9% and all
24 fits by 5.7-25%. Blender/Unity previews, 27 regressions and actual crown-plane
clearance checks pass. Signed candidate 2026100405 is prepared; publication
verification is pending. Native fit, player wear and reference fidelity remain
open. [Snug-fit evidence and QA](releases/winged-helmet-snug-20261004/README.md).
[Material repair and retest](releases/winged-helmet-materials-20261004/README.md).
[Deployment evidence](releases/winged-helmet-20261004/README.md).
[Current evidence and exact QA](helmets/winged-paladin.md).

## Blessing lifetime repair deployed for owner retest

The October 3 reconnect repair was insufficient: RoF2 expired finite-formula
blessings on its next tick because native effects used duration -1. Main
`7a645ebf` and fresh paired world/zone now preserve policy duration -1000 in
native effects; icon countdowns are unchanged. Exact native regressions and
closed-gateway hash/data-preservation checks pass. Current helmet client release
2026100403, Camil, tunnel quests and player progress are retained. Wait at least
30 seconds after hailing, open inventory, then relog without another hail and
compare speed/stats. Actual player acceptance remains open.
[Evidence and exact QA](releases/blessing-lifetime-20261004/README.md).

## Compact tunnel service layout deployed for visual QA

The owner accepted the six-resident campfire arrangement. PR 119 is on main and
the server update is complete. The new layout
pairs trainers and merchants in four compact gatherings, tightens the tradeskill
workshop by about 48%, groups traders and reroutes walkers. All 119 actors and
their functions remain. Full backup restoration, guarded forward/rollback,
data preservation, installed quests and server/public-session checks passed.
No client update is needed; rendered crowding and station interaction QA remain
open. [Layout and exact owner QA](releases/tunnel-compact-20261002/README.md).

## Spell-selection menu cache correction deployed for owner QA

Signed release **2026100202**, proxy **0.7.4-dev**, introduced this repair,
retained in current **2026100203 / 0.7.5-dev**, after PR 116 merged to
main. It refreshes native menu labels and ordering after class snapshots, fixing
cached 255 levels while preserving canonical scroll inspection. All 70 patch
sites, native regressions, runtime/launcher/loot suites, 46 hosted files and
existing-updater installation pass. The other 44 assets and all five production
services are preserved. Close EverQuest and click Play to update; check that
Pet > Sum: Water shows **02 - Elementalkin: Water** before memorization and after
zoning. [Evidence and exact owner QA](releases/spell-menu-20261002.md).

## Advanced loot action repair deployed for owner QA

Signed client **2026100203 / 0.7.5-dev** and matching world/zone binaries are
live from main. Loot All collects eligible earned drops across the current zone,
reports its result and offers one bulk NO TRADE confirmation. Each row has
Ignore; Filters has Remove. Corpse rights, receipts, bag/lore/cursor checks and
classic/public range remain enforced. All 46 hosted files, native process hashes
and closed-gateway data preservation checks pass. This retains the spell-menu,
pet, model and tunnel/campfire repairs. Close EverQuest, click Play and use
`/advloot`; real inventory/filter acceptance is pending the owner's test.
[Diagnosis, evidence and exact QA](releases/advanced-loot/ACTION-REPAIR.md).

## Compact pet window repair deployed for owner QA

Signed production release **2026100104** corrects native buff-panel resize
anchors that covered the compact roster and commands. All 46 hosted files
verify; only the pet UI changed from 2026100103. Production services and other
assets are preserved. Close the game and click Play in the normal launcher to
apply it. Existing saved window sizes remain; resize down if needed. Rendered
acceptance remains open in the [repair report](releases/pet-window-layout-20261001.md).
## Adventure Journal / Epic 0.5 candidate

The [Adventure Journal](adventure-journal/README.md) adds eight native tasks and
one archetype charm through the EC Chronicler. Guardian, Striker, Arcanist,
Warden and Binder are earned independently of primary class, with one durable
shared cooldown and hub-only attunement changes. The release gate starts
disabled. Content, quest, native-function and disposable database checks are
recorded with the candidate; client spells are staged separately. Native client
and balance acceptance remain open in the [exact QA route](adventure-journal/QA.md).
This entry does not record a production deployment.

## Character-selection crash repair deployed for owner QA

The [October 1 material repair](releases/character-select-crash-20261001/README.md)
fixes missing shared materials in seven imported classic models. The player's
crash dump identified a null material after login, before character selection.
Signed production release **2026100103**, proxy **0.7.2-dev**, introduced this
repair, retained in **2026100203** through the existing launcher: opening it and clicking **Play** applies the patch before
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
release **2026100203** retains it with proxy **0.7.5-dev**.
The original spell-inspection release passed hosted checks for all 46 files,
signature verification and installation through the production controller. That
release changed only the DLL and patch catalog, preserving all five services and
other assets. Close the game and reopen the patcher to apply the current update.
Rendered owner acceptance remains open with exact merchant/inventory QA linked.

## High-impact Play incident repair deployed

The [October 1 startup repair](releases/launcher-play-20261001/README.md) fixes
PFS version-2 archives exceeding RoF2's 8 KiB block limit. Signed game release
**2026100101** introduced the repair, retained in current **2026100203**. That
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
