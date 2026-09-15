# Current Nightcap status

Updated September 15, 2026. This is the current status index; dated studies and
QA reports preserve their original evidence and are not live-state promises.

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

**15 open issues.** Six completed issues closed after evidence publication:
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
| #36 | Skills/dual wield and second/third trainers, including client gates |
| #37 | Level-1 AA XP rule now durable; in-game XP proof pending |

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

Draft PR #52 contains signed manifest verification, full asset staging, guarded
Windows installation/recovery, and a scoped equipment-submission DLL candidate.
Automated fixture tests and independent reviews pass; no new client binary has
been deployed. Wails, release signing/hardening, remaining native client gates
and in-game acceptance stay open. Current [development plan](ops/client-delivery-plan.md)
and [transaction evidence](milestones/phase-11-report.md) preserve these gates.
