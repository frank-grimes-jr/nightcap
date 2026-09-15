# PoK usability work

The owner selected a compact arrival-area hub with a class guide and class-labeled
spell merchants. ADR 0024 records the scope and separation from AA persistence work.

Implemented and script-tested, not deployed:

- Three explicit class slots on hail, login, and selection/release responses.
- #classes and /say !classes for on-demand status.
- Clear selection confirmation and progression wording without misleading counts.

The hub migration and restock are implemented and tested on an isolated MariaDB
schema. All 14 database controls pass, including exact rollback and failure
handling. The sixteen class merchants preserve all 1,229 current scrolls and
prices across 1,747 class listings. Five utility services move into the hub and
identical duplicate Forgemaster spawns are consolidated. Player directions name
the new class merchants and retain camp guidance.

See hub-layout.md for placement, verification.md for evidence, and QA.md for
activation and exact in-game checks. Ground/path clearance, client merchant and
Find behavior, and the native selection flow remain unverified in game. No live
changes or restart have occurred. Native AA lifecycle work stays separate.

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
