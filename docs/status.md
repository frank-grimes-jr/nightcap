# Current Nightcap status

Updated September 15, 2026. This is the current status index; dated studies and
QA reports preserve their original evidence and are not live-state promises.

## Local QA launcher

A signed offline QA package now installs/repairs four client patch files and
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
| PoK hub | 16 class merchants, 1,747 listings / 1,229 unique items; relocated utilities and one Forgemaster | Grounding, paths, Find, shop and quest interactions |
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
Manual gameplay acceptance remains pending. No new client patch, numerical balance policy or augment content was
introduced by this deployment.

## Issue disposition

**14 open issues** at the latest September 15 query. Six completed issues closed after evidence publication:
#8, #9, #12, #21, #24 and #25. Three reports were administratively consolidated:
#38 → #13 (equipment), #39 → #36 (trainers), #20 → #19 (song landing).
Their unresolved acceptance was preserved; consolidation did not fix the bugs.

| Open issue | What remains |
|---|---|
| #4 | Decide actual AA class column versus labels; true column needs client work |
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
