# PoK usability work

The owner selected a compact arrival-area hub with a class guide and class-labeled
spell merchants. ADR 0024 records the scope and separation from AA persistence work.

Implemented and script-tested, not deployed:

- Three explicit class slots on hail, login, and selection/release responses.
- #classes and /say !classes for on-demand status.
- Clear selection confirmation and progression wording without misleading counts.

A tested merchant inventory and preliminary placement proposal is available in
hub-layout.md and hub-merchant-plan.json. The planner preserves all 1,229 unique
scrolls and item prices; two planner tests pass. It applies no database changes.

Still in progress:

- Choose and verify unobstructed arrival-area positions.
- Build one class merchant for each of the 16 classes, using Spells, Songs, or
  Disciplines labels that match the actual inventory.
- Preserve existing item availability and prices; replace the old vendor spawns
  through a guarded migration with rollback and restock integration.
- Validate merchant contents and the full player flow in game before promotion.

hub-stock-audit.json contains the read-only stock snapshot and original class
levels from the matching downloaded/server-export spell file. The two source
files were not modified. The snapshot contains 1,229 unique stocked scrolls,
no name/ID mismatches, and no scroll without an original class eligible by level 50.
It describes the current observed inventory, not an approved future-expansion pool.

Run the script tests in an isolated directory using the stack's interpreters:

    lua test-pok-class-status.lua path/to/global_player.lua
    perl test-pok-chronicler-dialogue.pl path/to/The_Ancient_Chronicler.pl

The Perl test has 16 assertions. The Lua test checks all 16 primary classes plus
command, login, and delegation behavior. Existing regression:
tools/tests/test-multiclass-login-banner.ps1.
