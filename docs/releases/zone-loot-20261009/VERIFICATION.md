# Candidate verification â€” October 9, 2026

All checks below passed on the feature candidate. No binaries, gameplay SQL or quests were installed on OVH. Test-branch integration is recorded separately below when completed.

| Check | Result and scope |
|---|---|
| Catalog and native zone-hunt suite | 7 tests; exact data generation, source/socket exclusions, actual award and cap functions, recommended-level scaling, nonplayer preservation and merchant protection |
| Inventory native translation unit | Passed; actual advanced-loot/forge implementation, per-query failure/exception injection, zero affected rows, stale instances, binding, replay, uncertain commit/rollback and publication quarantine |
| MariaDB rehearsal | 15 checks; 448 variants, 48 zones, 6,056 source pairs, disabled installation, replay refusal, late socket-preimage rollback, actual forge SQL and preservation of earned inventory/receipts |
| Universal trading regression | 6 tests passed |
| Gameplay policy regression | 2 tests passed |
| Throw Stone regression | 108 compiled checks, zero failures |
| Advanced loot adapters | Native currency and saved-state regression suites passed |
| Native binaries | world, zone, shared_memory, loginserver and ucs built in a fresh isolated tree; source fingerprints stable; hardened world contract verified |
| Native equipped-stat diagnostic | 24 synthetic level-50 loadouts; 12 paired comparisons, six valid augments each; see BALANCE.md |
| Independent code review | Read-only gpt-6-astra review. A mercenary cap regression was found and fixed by limiting raw accumulation/final headroom to clients. Follow-up review reported no remaining concrete P1/P2 issue. Reviewer did not independently rerun the parent execution evidence. |

Generated acquisition is 0.5% independently per family, with 60/30/8/2 quality weights. Acquisition and forging remain globally disabled until the matching candidate is explicitly installed and activated. The reviewed signal-only Plane of Fear script hash is pinned by the generator. Production content capture was read-only.

Owner QA remains required for RoF2 display/socket/removal behavior, exact acquisition sources, advanced loot, forge/reconnect behavior and combined legal-AA/multiclass/pet encounters. Full six-augment HP/mana gains are material; the approved stats have not been tuned beyond the approved catalog. See QA.md and BALANCE.md.

## Branch integration verification

Feature commit `99f88e4` was combined with current main `d5f273f` and existing test `9315ae5` (including dev `97f6f93`) in merge `8f2aa6c`. Current live-release fixes and the pending Adventure Journal were retained. Additive documentation/import conflicts were resolved by preserving both sides; historical Adventure Journal phase 45 and deployed social-tunnel phase 46 remain separate.

The integrated candidate passed 25 affected Python/native tests (zone hunt, Epic 0.5, gameplay policy and client asset generation), plus all 51 Epic quest assertions. A fresh read-only independent integration review found no concrete P1/P2 issue or lost main/test functionality. The existing native object tree was verified against its recorded manifest before applying exactly three integrated files (`epic05.h`, `perl_client.cpp`, `spells.cpp`); all five binaries rebuilt and the source stayed stable. Every candidate overlay file matches the final source fingerprint exactly. See [combined build manifest](integration-build-manifest.json), the authoritative binary set for this integrated candidate. The earlier manifest and equipped-stat diagnostic retain their pre-integration scope; the merge changes only Epic contract/duration behavior, with no active buffs in the diagnostic.

Neither the Adventure Journal nor zone-hunt acquisition was activated by Git integration. Their independent installation and owner acceptance gates remain intact. No main promotion, production database write, client publication or runtime replacement occurred.
