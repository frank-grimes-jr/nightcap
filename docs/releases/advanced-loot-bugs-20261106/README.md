# Advanced loot reliability and controls — November 6, 2026

Candidate on `codex/advanced-loot-bugs`, based on locally observed
`origin/main` d5c895d3. Signed candidate2026110605/proxy0.13.5 is prepared and
verified locally, replacing exactly three assets over live2026110604. No
publication, production change or owner in-game acceptance is claimed.

## Problems and behavior

Closing the native window while browsing Filters left its server subscription
on saved rules. Those snapshots contain no drops, so subsequent kills could
not trigger auto-open. A hidden window now returns to Drops with an empty
search, without opening itself or changing saved preferences. A new eligible
drop opens the main list, including after closing Settings. Enabled and Open
on new loot remain required; Never/automatic collection and loot rights remain
server-owned. An open Filters page continues showing Filters until closed or
Back to loot is selected.

The last Drops total is retained separately from the saved-rule count. This
also detects a newly queued ninth item while returning from Filters with the
same first eight rows. An unchanged queue respects the player's close. The
cross-view/page regression failed before this correction and passes afterward.
The retained count is presentation-only and resets with the character context.

A skin reload destroys and recreates the native screen. Previously creation
always hid it, and already-seen tokens did not reopen it. The destruction
callback now preserves visibility through reconstruction; a deliberately hidden
window stays hidden. Lifecycle reset still clears character state and consent.

Search previously accepted only byte CXStr storage. Native CEditWnd can convert
plain text to UTF16 (the existing Bazaar audit documents VA0x87DD51 and the
same +0x1ec InputText layout). The reader now accepts printable ASCII from both
representations, checking encoding, length32, byte capacity and exact terminator.
Non-ASCII/control input remains rejected. Enter and Search submit the existing
hex-encoded, server-filtered item-name query; Clear removes it.

Stock icons grow from20x20 to32x32 in eight32px rows. The screen is588x472 at
(12,4), within640x480. Inspect item moves beside Loot item, Item rule and More
on both main Drops and Filters lists after selecting an inspectable item.
Other group/corpse actions remain in More. Pet Info controls remain intact.

## Implementation and checks

- `eq-client-dll/src/advanced_loot_ui.h`: hidden subscription rearming,
  auto-open panel and Inspect visibility, reload visibility preservation.
- `eq-client-dll/src/advanced_loot_screen.h`: bounded byte/UTF16 search reader
  and native destruction visibility capture. Native ABI/patch sites unchanged.
- `tools/client_advanced_loot_ui.py`: paired XML geometry and main Inspect.
- Actual production-header x86 fixtures in `eq-client-dll/tests/advanced-loot-*`
  reproduce byte/UTF16 input, hidden Filters, reload and direct Inspect.
  Before fixes: UTF16 search and hidden Filters assertions failed; XML icon,
  Inspect position and non-overlap checks failed. They pass after the repair.
- `run-advanced-loot-tests.bat` now rejects negative Windows exit codes as well
  as positive failures. An assertion crash previously could return suite success;
  the failing UTF16 fixture was observed returning suite exit1 after this guard.
- Five advanced-loot x86 fixtures, seven XML tests, five shared gameplay UI and
  three pet UI tests pass. DLL builds. Catalog generator verifies120unchanged
  sites; exact original RoF2 executable signatures pass. Final shared-runtime
  and wiki results are recorded in `verification.json`.

This is a self-review of correctness, bounds, native lifetime, authority,
compatibility and scope; no independent reviewer or visual acceptance is claimed.

## Delivery and recovery

`signed-candidate.json` and `candidate-verification.json` verify the shipped-key
signature, all148descriptors and exact preservation of145other descriptors/URLs,
history and tombstones. The three replacements are DLL, matching versioned
catalog and Pet Info XML. Source catalog regeneration changes only the proxy
version/hash contract, retaining all120native sites. The local signature does
not reserve a release counter; recheck the live baseline before any publication.

`prepare_client.py` reads the fresh, hash-pinned live Pet Info XML and replaces
only its100loot controls/screen blocks. All bytes outside those spans, including
the native Schema and pet controls, are retained. Three tests cover LF/CRLF,
idempotence, missing/duplicate controls and drift refusal. `prepare.go` authenticates
the baseline envelope and actual baseline runtime bytes, checks the exact
candidate DLL/catalog/executable pair, then signs locally. `verify.go` separately
verifies signature/inventory/history preservation. Signing material stays local.

All23preparation/publisher checks pass on Linux with no skips (real fsync,
symlinks, mode bits and interrupted-write recovery); Windows passes with five
POSIX skips. Tests use a disposable network-isolated container, read-only source
and temporary files, not the running game services. `publish.py` pins both
envelopes/assets, checks all retained assets and public controls, holds service
fingerprints and writes the channel last under the deployment lock. Main/live
publication remains owner-gated. `release-validation.json` records current scope.

Deliver the DLL, its matching catalog/config and newly generated
`uifiles/nightcap/equi_petinfowindow.xml` together through the existing signed
launcher flow. Use the latest verified signed release as the baseline and retain
unrelated Stats, recall, cast-bar, pet and other assets. Never regenerate the
entire channel from the old reference client. No server/SQL/cache/rule/quest
reload is required. Full EQ exit and normal launcher Play are required after
authorized publication. Protected and installed clients were not modified.

Recovery requires a higher signed counter and a compatible previous DLL/XML
pair, retaining current unrelated assets and all player preferences/data.
Do not lower the channel counter or restore a player snapshot.

## Exact in-game QA after publication

1. Fully exit EQ, update using launcher Play, enter East Commonlands and enable
   Advanced loot/Open on new loot. Kill loot-bearing skeletons. Verify automatic
   opening,32px matching stock icons and eight readable rows at640x480 and a
   normal resolution. Select an item and click Inspect directly; confirm the
   correct native item window opens. Loot and inline Always/Never still target
   the correct row; only a confirmed empty queue closes automatically.
2. Open Filters, search a saved Bone Chips rule with typing/paste, Search and
   Enter, mixed case, spaces and a32-character query. Clear, page and remove a
   rule; verify names/results and no stale icons. Try non-ASCII input: reject
   visibly without sending an unrelated query. Select and inspect a saved rule.
3. Close Filters using X and separately `/advloot`. Kill another skeleton: the
   main Drops list must open. Repeat after closing Settings. Repeat with Open
   on new loot off: it must stay closed. Re-enable and repeat.
4. With a populated window open, `/loadskin nightcap 1`; it should return with
   usable rows, icons and Inspect. Repeat while deliberately closed: it must
   remain closed. Zone, reconnect and switch characters; verify preferences,
   new-drop opening, no stale item selection and no inherited confirmation.
5. Verify pet controls, Inventory Stats, Bazaar, ordinary corpse looting,
   group permissions and NO TRADE consent where applicable. Missing icons must
   leave the item name usable. Broader intermittent failures require a fresh
   reproduction/log; these tests do not prove every possible missing-window cause.

## Wiki impact review

All24maintained articles and generated item/zone directories were assessed
against this client-only change. Advanced loot gets a clearly unreleased repair
preview and its stale Ignore instruction is corrected to the already-published
Always/Never controls. Change Log records the candidate. Features/home already
link the live system and need no new release claim; Commands still uses
`/advloot`, Launcher retains ordinary Play/skin recovery. Equipment, rewards,
catalog values, loot finder, combat/build tools, pets, crafting, classes, travel,
quests and acquisition pages have no mechanics/content change. No public
publication is claimed. The global source ledger retains unrelated historical
drift; `check_refresh.py --ref HEAD --include-worktree` is recorded rather than
silently advancing it.
