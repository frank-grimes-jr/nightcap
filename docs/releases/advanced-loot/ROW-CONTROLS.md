# Advanced loot row controls — October 9, 2026

Candidate source and build, not deployed or accepted in game.

## Behavior

Always Loot and Never Loot are directly beside every item on the main loot
page. These are checkbox-style buttons using the existing native button ABI;
the checked label follows the server's saved rule, not a speculative local
change. Selecting either replaces the other; selecting the checked choice
returns to Ask each time. An item need not be selected first, and changing
another row's rule preserves the current selection. Always Need/Greed remain
in Item rule. Filters keeps its existing Remove action.

Rules retain their existing per-character persistence and Use saved rules
setting. Saving Always does not bypass NO TRADE consent, inventory limits,
group rights or any other server transfer check. No server, SQL or protocol
change is required.

The window closes when a complete, accepted Drops snapshot changes the total
queue from nonempty to empty, including the last page and automatically handled
items. It also closes when the last item leaves the offered queue through Never,
Leave or decay. A pending/failed award or partial snapshot cannot close it.
An empty Filters search, editing Settings, changed settings, or navigation away
while a request is pending does not close the window. Reopening an already empty
window permits normal Settings/Filters access. An outstanding auto-show request
is cancelled when the queue empties before the next frame.

## Implementation and verification

- `eq-client-dll/src/advanced_loot_ui.h`: row actions, acknowledged check labels,
  lifecycle close; existing capability/session/revision checks remain intact.
- `tools/client_advanced_loot_ui.py`: 16 labeled row toggles within the existing
  588-by-430 screen; Filters' Remove controls remain separate.
- `tests/run-advanced-loot-tests.bat` in `eq-client-dll`: four x86 production-header
  fixtures pass with `/W4 /WX`; controller exercises native notification calls,
  row targeting, mutual exclusion, unchecking, send failure, denied capabilities,
  pending requests, paging, partial replies, auto-close and navigation.
- `python -m unittest discover -s tests -p test_advanced_loot_ui.py` in `tools`:
  five control inventory, labeling, viewport, overlap and duplicate-insertion
  checks pass. New-control tests failed against the original implementation.
- `eq-client-dll/build.bat`: x86 DLL build passes. Generated layout preview is a
  geometry/font approximation, not evidence of the native RoF2 renderer.
- Shared UI regression checks pass: three Pet Management, four client gameplay
  UI and five client asset tests. The real stock Pet Info XML generates and
  parses successfully, preserving the original file byte-for-byte.

The paired local candidate and inspected preview are staged in
`E:/EQ_Local_Dev/artifacts/advanced-loot-controls-20261009/`.
[Candidate hashes and verification](row-controls-20261009.json).

Review found no additional authorization, inventory or protocol surface: row
choices call the same server FilterCommand and the close operation only hides
the screen. Pair the DLL with regenerated `uifiles/nightcap/equi_petinfowindow.xml`.
An older XML lacks required controls and cannot configure this candidate window.
Publish through the existing signed launcher workflow after the normal release
gate; never overwrite the original RoF2 installation or a running client.
Rollback the pair together. Existing server-side saved rules remain valid.

## Exact in-game QA (pending)

Use a separate managed QA client with the paired DLL/XML. In isolated East
Commonlands (`ecommons`, zone 22), use `a_decaying_skeleton` (NPC 22003) and Bone
Chips (13073), following the controlled-corpse recipe in [QA.md](QA.md). Spawn
with `#npctypespawn 22003`, target it, run `#npcloot remove all` and
`#npcloot add 13073 5 0`, then kill through normal combat. Do not inject fixtures
into production. Initial settings: Enabled, Use saved rules and Open on new loot
on; Loot everything and Unfiltered items only off.

1. Open `/advloot`. Verify both fully readable toggles beside the chips at
   640-by-480 and the normal playing resolution; no overlap or extra navigation.
2. Disable Use saved rules temporarily, return to loot, and click Always Loot
   without selecting the item. After acknowledgment only Always is checked.
   Click Never: only Never is checked. Click Never again: neither is checked.
   Repeat Always twice. Confirm the corresponding saved rule/absence in Filters.
3. Enable Use saved rules. Save Always, kill another fixture, and verify eligible
   chips arrive once. Save Never on offered chips and verify they remain on the
   corpse without future collection. Remove the rule in Filters to restore Ask.
   Camp/reconnect to verify persistence; another character's rules stay separate.
4. With Ask, loot one fixture manually: the window closes after the final award.
   Create nine separate fixture corpses, move to page two, and Loot All: it
   collects eligible drops from both pages and closes once the queue is empty.
5. Fill bags or create a lore conflict using Worthless Coin (1041): the declined
   row and error remain visible. Clear the restriction, collect the remaining
   loot, and verify the window closes with no duplicate award.
6. For NO TRADE, use an item verified non-tradable under the active server rules;
   the historical 1068 fixture may be tradable under FreeTrade. First Loot All
   must retain its consent prompt and window; close only after accepted collection.
7. Reopen an empty window: it stays open. Empty a Filters search or remove the
   last saved rule: Filters stays open. Open Settings while an Always item is
   collected: Settings stays open. Return to loot, close/reopen, zone, and
   `/loadskin`; verify normal controls and subsequent auto-show/close still work.

Native appearance, real inventory delivery and preference persistence remain
owner QA. The deterministic fixtures do not establish those results.
