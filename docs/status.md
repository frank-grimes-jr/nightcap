# Current Nightcap status

Updated September 20, 2026. This is the current status index; dated studies and
QA reports preserve their original evidence and are not live-state promises.

## Living economy QA candidate

Finite city-merchant finds, ten EC traders and all six requested residents are
**active for QA** after owner-approved backup/restart. The corrected world and
all eight zones have verified running hashes and clean checked startup logs.
Epoch 1 has 10 finds, six WTS and four WTB offers, each quantity one. Existing
player/merchant fingerprints are unchanged. Dated P1999 prices are scaled for
observed earning boosts before premiums. [Activation evidence](economy/ACTIVATION.md).

Initial activation exposed stale build artifacts; the corrected paired rebuild
and regression guard are recorded in [verification](economy/VERIFICATION.md).
The Classic Lavastorm server map alias is repaired, but client terrain is still
missing, including from the owner's suggested `E:/EQ_Local` copy. Khalure offers
the other eight Classic rings and rejects stale Lavastorm links. No client files
were changed. [Client prerequisite](economy/residents/CLIENT-TERRAIN.md).

Costume rendering, normal-account transactions, pricing balance and owner
[in-game QA](economy/QA.md) remain open. [Resident QA](economy/residents/README.md)
includes all six appearances, Trift's OOC story and offered ring landings.
Promoted through **dev/test**, not main.

## East Commonlands hub QA candidate

The approved tunnel hub is active on the development server and promoted through
**dev/test**. It moves22existingservices, adds ten paired Classic travel routes
and a PoK bridge, sets new starts, and repairs Ancient Attunement in place.
Existing player state, binds, merchant stock and original travel doors are preserved.
World and all eight zones have verified hashes and clean checked startup logs.
Signed client release **2026092002** is required. Its20files and actual startup
passed on the separate QA client copy. Close the old launcher and use the new
release executable listed in [activation evidence](releases/ecommons-hub-20260920/ACTIVATION.md).
The usual launcher executable is awaiting replacement because Windows has it open.
Owner [in-game QA](releases/ecommons-hub-20260920/README.md) and main promotion remain open.

## Three-pet QA candidate

The server candidate supports one permanent summoned pet per held class, shared
ordinary pet controls and separate eight-slot armor loadouts. The 36 native
class/summon permutations, attack/range cases, migration cases and transactional
failure checks pass. [Evidence and exact owner QA](releases/multiclass-pets-20260919/README.md).
The QA candidate is active: world and all eight zones have verified hashes,
with a fresh backup and clean checked startup logs. [Activation evidence](releases/multiclass-pets-20260919/ACTIVATION.md).
Manual acceptance and main promotion remain pending. The pet feature itself needs
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
| Bags | 22 positive prices, base 10–7,500 platinum; flags/stock retained | Quotes, wallets, restrictions, resale refusal and economy |
| Earned AAs | Purchases/grants/refunds and atomic native class release; paired binary/plugin | In-game counters/effects, reconnect, failure recovery and rendering |
| Five server fixes | Held-class weapon damage, extra-pet ownership/orders, direct-AA duration and owned-AA profile handling | Exact per-build gameplay matrix |
| Skills | Canonical 58,359-row caps; value-1 unlock policy, existing held-Monk slice | Full class/slot coverage and client Skills/trainers |
| AA XP | Minimum level 1 survives matching world startup | Actual XP award/allocation and persistence |
| Waypoints | Marker discovery quest and relocated PoK travel service | Discovery, recall, safe arrivals and Explorer completion |

[Exact live QA checklist](releases/live-qa-20260915/QA.md) ·
[Deployment and rollback](releases/live-qa-20260915/README.md).
The server release entered dev/test in PR #49. The owner subsequently authorized
all gameplay to move to main for live testing; [promotion record](releases/main-live-qa-20260915.md).
Manual gameplay acceptance remains pending. The September 15 deployment did not
include the new client patch or permanence policy; the September 19 release above
supersedes those portions of the live baseline.

## Issue disposition

**14 open issues** at the latest September 15 query. Six completed issues closed after evidence publication:
#8, #9, #12, #21, #24 and #25. Three reports were administratively consolidated:
#38 → #13 (equipment), #39 → #36 (trainers), #20 → #19 (song landing).
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
