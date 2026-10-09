# Advanced loot row controls — October 9, 2026

The owner authorized main and server deployment on October 9 with "Deploy to
main and server". Release **2026100901 / proxy 0.7.8-dev is published**;
owner in-game acceptance remains pending.

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

The initial paired local candidate and inspected preview are retained in
`E:/EQ_Local_Dev/artifacts/advanced-loot-controls-20261009/`.
[Initial candidate hashes and verification](row-controls-20261009.json).
The versioned signed release and operational receipts are in its `deployment/`
subdirectory; the initial candidate DLL is historical, not the published binary.

Review found no additional authorization, inventory or protocol surface: row
choices call the same server FilterCommand and the close operation only hides
the screen. Pair the DLL with regenerated `uifiles/nightcap/equi_petinfowindow.xml`.
An older XML lacks required controls and cannot configure this candidate window.
Publish through the existing signed launcher workflow after the normal release
gate; never overwrite the original RoF2 installation or a running client.
Rollback the pair together. Existing server-side saved rules remain valid.

## Production release and recovery

PR [129](https://github.com/frank-grimes-jr/nightcap/pull/129) merged into main
at `081c4d8`. Signed game generation **2026100901 / proxy 0.7.8-dev** changes
only `dinput8.dll`, `nightcap-patch-sites.json`, and the Pet Info XML. The other
101 files retain their exact deployed hashes, including all loading images,
model/helmet assets, bootstrap, spells and configuration. All 71 native patch
sites and the non-loot Pet Info controls are unchanged.

The release uses the production key already shipped in launcher 0.4.0 and
retains the 0.4.0 minimum launcher. Native loot/runtime checks, the three Go
manifest/preflight/packaging packages and 12 publication recovery tests pass.
The local signature and all 104 payload hashes verify. Publication uses the
existing deployment lock, refuses baseline drift, commits immutable files before
the channel, and preserves the preceding channel in its staging directory.
No game-runtime, database, launcher-desktop, starter, guide or ZIP change is needed.

Publication completed successfully. The public HTTPS channel signature and all
104 payload hashes (211,906,857 bytes) verify against the shipped production key.
All five services retained their identities, images, start times and restart
counts; game/database health remained healthy with zero container restarts.
The desktop channel, starter ZIP and guide are byte-for-byte unchanged. No
running local client or original installation was modified. Fully exit EverQuest
and click Play to install the update through the existing launcher.
[Verified publication and service evidence](row-controls-publication-20261009.json).

If the client fails to load or the new controls regress, use the retained
2026100407 DLL/catalog/XML with the other current assets and sign them as a
new game release **greater than 2026100901**. Verify every file and the shipped
public key before atomic channel publication. Do not republish an older counter
or alter receipt/filter data. Old immutable files and metadata are retained at
`/opt/nightcap/deploy/production/data/public/release/2026100407` and
`/opt/nightcap/releases/advanced-loot-controls-2026100901/previous-channel.json`.

## Owner live QA after publication (pending)

Fully exit EverQuest and click Play in the existing Nightcap launcher. In East
Commonlands, open `/advloot` and kill a normal eligible skeleton for Bone Chips:

1. Verify Always Loot and Never Loot are readable and clickable directly on its
   row. With Use saved rules temporarily off, select each choice and click it
   again: exactly one or neither should be checked after acknowledgment.
2. Restore Use saved rules and verify Always collects eligible future chips,
   Never leaves them, and Filters > Remove restores Ask. Camp/reconnect and
   verify saved preferences; another character retains its own rules.
3. Collect the last offered item, then repeat with Loot All across multiple
   pages: the window closes after the queue empties. Inventory restrictions
   leave the item/error visible. Reopening an empty window, Settings and an
   empty Filters search must remain usable.

Use ordinary earned loot on production. Controlled spawns and injected faults
belong exclusively to the isolated plan below.

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
