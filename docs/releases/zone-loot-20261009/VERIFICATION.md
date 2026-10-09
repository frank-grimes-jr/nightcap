# Candidate verification — October 9, 2026

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
