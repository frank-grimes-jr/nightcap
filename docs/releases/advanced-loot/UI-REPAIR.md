# Advanced loot window repair — October 2, 2026

## Report and scope

The owner reported that the buttons did not work and the window was confusing
and crowded. The original 720 x 578 window exceeded a 640 x 480 viewport and
displayed all item, group, filter and settings controls together. Its controller
disabled even navigation while waiting indefinitely for a complete server reply.

The replacement is 588 x 430, with Loot, Saved rules and Settings tabs. Select
an item to see Loot item, Item rule and More. Item rules and extra actions have
their own panels; group actions appear only when the server grants those actions.
All five saved choices remain available, including preconfiguring Need/Greed.
The window's INI version is 2. Server rights and transfer code are unchanged.

Local navigation remains usable during a request. A five-second timeout shows
Retry, followed by a bounded automatic refresh. Retry requests current state;
it does not repeat an award whose outcome is unknown. An unchanged NO TRADE
confirmation survives refresh. Switching views or losing a selected item clears
selection and closes its detail panel, preventing an action on a replacement row.

## What is and is not established

- The live server's advanced-loot command is available to ordinary accounts;
  its receipt-aware image is running. The owner has saved item rules.
- Exact-client disassembly confirms native buttons notify their parent with
  message 1 through vtable offset 0x88. This agrees with the hook. Button
  transparency defaults do not explain the report.
- The prior screen fixture invoked a callback directly. It did not exercise
  the controller, native hit testing, real transport or rendered geometry.
- New controller coverage exercises native notification ABI adapters together
  with visibility, timeout/retry, protocol acknowledgments, all action commands,
  persistent rules, NO TRADE confirmation and selection invalidation. The
  transport and controls are still fixtures.
- XML checks establish unique complete controls, viewport bounds and no button
  overlap within each panel. These checks are not a rendered game inspection.
- The original live button failure is **not yet localized**. The owner stopped
  Computer Use before the window could be inspected. Keep the goal open until
  the actual updated game path below passes.

The proxy writes bounded, non-player diagnostic event labels to its existing
local log: `ADVLOOT control-click:<control>`, `request-sent:<verb>`,
`snapshot-accepted`, timeout/send errors and specific snapshot rejection classes.
`request-sent` proves only invocation of the client's serializer, not server receipt.
No item names, character names, chat, credentials or packet bodies are logged.

## Published release

Published client generation **2026100201**, proxy **0.7.3-dev**. It retains all
67 patch sites and 15 required features. Only the proxy, its versioned catalog
and the advanced-loot definitions in `equi_petinfowindow.xml` change from live
2026100104. The recent pet-window anchor repair, other UI definitions, model
archives, spells, bootstrap and configuration are preserved.

[PR 113](https://github.com/frank-grimes-jr/nightcap/pull/113) merged to main at
`2f530209b463225d12029db2853b2d158924a414`. The client was published on October 2;
all 46 public HTTPS files and the signature verify against the previously shipped
production key. All five services retained their identities, images, start times
and restart counts throughout publication. Desktop, starter, guide and previous
release assets remain intact. [Publication evidence](ui-repair-20261002/publication.json).

Staging initially refused a concurrent game-container recreation and gateway
restart. Inspection confirmed unchanged images and public files and healthy
services. The original baseline was retained, and the inspected service state
was recorded under the deployment lock before staging passed. This client repair
did not restart services or alter the database. The concurrent tunnel deployment
is recorded separately in its October 2 production report.

The managed local client was not altered by this publication. Close EverQuest
normally and click Play in the existing launcher to apply the update. Native
rendering, clicks and server acknowledgment remain unaccepted.

No server restart or database migration is required. Original
`Client_RoF2_Dev` files remain read-only. Receipt-aware recovery restrictions in
[PRODUCTION.md](PRODUCTION.md) still apply; do not downgrade the server or
restore the old database to troubleshoot this client-only repair.

## Automated verification and source record

The [candidate evidence](ui-repair-20261002/candidate-verification.json) records
the source hashes, signed channel, complete file inventory comparison and test
outcomes. The proxy was built after all recorded proxy source edits. Regenerating
the UI from the original stock XML produced the exact packaged XML.

- Four advanced-loot native fixtures pass, including the new controller fixture.
- Eleven UI XML regressions and five native runtime test cases pass.
- The complete launcher `go test ./...` passes.
- Twelve publication recovery/drift fixtures pass. Their Windows lock/fsync
  substitutions do not replace the Linux deployment-lock and drift guard.
- All 46 signed files verify against the previously shipped production public key.
- Independent review found and prompted fixes for two selection hazards; the
  final pass found no remaining concrete source blocker. A narrow disassembly
  check found no click/Enter callback from native Show/text calls that would
  justify adding a speculative render-reentrancy guard.

These checks establish the candidate's source and tested controller behavior.
Actual hit testing, appearance and server acknowledgment still require the
in-game steps below.

## Exact live acceptance

1. Close EverQuest normally. Open the existing Nightcap launcher and click Play.
   Confirm game release 2026100201; enter East Commonlands on Darthy.
2. Enter `/advloot`. Capture the full window including its top status line.
   The entire window must fit at 640 x 480 without clipping. Loot, Saved rules
   and Settings must respond visibly. `/advloot` must close and reopen it.
3. Open Settings. Toggle Open on new loot off then on; each change must show a
   server acknowledgment and survive closing/reopening. Restore the preference
   you want. Capture the status and proxy log if a five-second Retry appears.
4. Kill a natural skeleton near the tunnel, approach within collection range,
   and select Bone Chips. The row must highlight. Before looting, use More ->
   Inspect to open its item window. Return to the list; Loot item must add the
   item once and remove the awarded row.
5. On a later Bone Chips drop, choose Item rule -> Never loot. The rule must
   appear in Saved rules, survive reconnect, and leave a later drop on its corpse.
   Change to Always loot and confirm a later eligible drop collects once. Change
   back to Ask each time; its saved-rule entry must disappear.
6. Search Saved rules and use Clear; test paging if there are more than eight
   saved items. Choose a row, open Item rule, and verify its name remains the
   item affected. If the selected drop is looted externally, its editor must
   close without selecting another item.
7. Confirm the compact pet window still shows its roster, commands and buffs.
   Preserve the separate NO TRADE/lore, group/raid, inventory-full, UI reload
   and receipt/replay acceptance gates in [LIVE-QA.md](LIVE-QA.md).

If any control fails, retain the fresh `nightcap_dll_*.log` and a screenshot of
the status line. A healthy launcher or passing fixture alone does not close this
incident. No synthetic items or persistence faults should be injected into live.
