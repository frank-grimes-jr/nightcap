# Phase 3 candidate report — PoK arrival hub

> Current status (2026-09-15): implemented server/AA/PoK candidates are deployed for live QA; main gameplay acceptance remains pending. See [current status](../status.md). The dated evidence below retains its original scope and is not a current deployment checklist.


2026-09-13. Implementation and automated verification complete; activation and
manual in-game QA pending. This phase is not accepted or promoted to main.

Built: explicit multiclass status on login, hail, and commands; clearer selection
confirmation and saved-slot responses; sixteen named class merchants at a compact
arrival hub; original-class stock routing for all 1,229 currently available items;
five nearby utility services; duplicate Forgemaster consolidation; guarded forward
and rollback SQL; compatible, transactional restock; preflight before era changes.

Kept separate: AA ownership/lifecycle changes, balance tuning, permanent character
panel UI, client spell-data changes, and future-expansion inventory policy. The
current release does not add free spells, prices, rewards, or combat power.

Evidence: 14 database controls, four planner/migration tests, era preflight/file
failure tests, and the Lua/Perl class UI checks. Independent review findings were
addressed. See ../pok/verification.md and ../pok/hub-database-tests.json.

Still unproven: exact ground and path clearance; live Find and merchant windows;
normal-account command routing and native confirmation flow. Existing client
sync and native class/AA mutation limitations remain. Exact QA and activation
requirements are in ../pok/QA.md. The owner's no-restart-while-playing boundary
remains in effect.
