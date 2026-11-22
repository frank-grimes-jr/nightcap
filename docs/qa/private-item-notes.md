# Private item notes

Inspect an item, open **Notes**, type a reminder, and select **Save**. The reminder appears in the ordinary item description on each inspection. **Reload** discards a draft and restores the saved text. Saving an empty field deletes the note for this item. The editor accepts one line up to 240 bytes in the RoF2 client code page.

Each item definition ID owns a single Windows registry string under `HKCU\Software\Nightcap\ItemNotes`. Copies of the same ID share one note across characters using that Windows account. Different IDs remain independent, including tier variants that share a name. Notes are local user data, outside the signed game files. The UI reads and writes locally, without a chat command or game-server request. Across simultaneous editors, the last explicit successful save wins.

## Candidate and release

Branch `feature/private-item-notes` builds on worn comparison commit `511a3d1f`. The combined x86 proxy is `0.14.2-dev`. The staged directory is `eq-client-dll/build/private-notes/`. Ship its DLL, matching site catalog, new item display skin and retained target skin together from the current signed parent. Preserve unrelated release descriptors and pending client changes. Players receive an authorized release by fully exiting EQ and pressing Play. This feature requires no server, SQL or cache update. A recovery release can restore the preceding proxy/catalog and previous skin layout together. Leave player notes in place during recovery.

The generated item skin keeps the stock description and lore tabs and all 213 original top-level definitions. `tools/client_item_notes_ui.py` adds the Notes controls via the existing gameplay asset generator. The launcher package includes `uifiles/nightcap/equi_itemdisplay.xml`. Source stock XML SHA-256 is `976a55648570139c52d187333df9d8203ea0939edfafe7c52eacb2b8c14ce2eb`.

## Verification

| Local candidate file | SHA-256 |
| --- | --- |
| dinput8.dll | `9bf8b95382d4210d76e458c478cf226d74b103c24a5675704d375a913e3a6428` |
| nightcap-patch-sites.json | `2d88adcc351afe9e1c9567d8760c720eab7f8115737b2c6ab0ca302bb9c1b358` |
| uifiles/nightcap/equi_itemdisplay.xml | `8d37558ea0fa4cb3eeece8bd636643afa10b94548d76483fb31a4ecefef71196` |
| uifiles/nightcap/equi_targetwindow.xml | `ec59307a3091696b6c3284c829615628131ad4814d522c708b5d6c0a7e11f60f` |

The item-window fixture passed 76 checks and the native equipment fixture passed 81. The target regression and four target/item skin generator tests passed. Static preflight verified 122 sites on the pinned executable with the retained client configuration. The installer and launcher Play regression suites passed.

The fixture in `eq-client-dll/tests/augment-item-window.cpp` exercises original RoF2 item-description rendering, guarded Notes notification and destruction slots, fixture edit controls and a real disposable per-run Windows registry key. It verifies save, persistence, reload, removal, draft preservation on read failure, UTF-16 edit conversion, markup escaping, duplicate item names, stale window identity and ordinary notification forwarding. The temporary registry key is separate from player notes. Keyboard interaction, focus and visual layout need in-game QA.

The implementation is in `eq-client-dll/src/item_notes.h`, `item_note_ui.h` and `ui_hooks.h`. The notes and target skin tests cover the generators. Set both `NIGHTCAP_ITEM_NOTES_CANDIDATE` and `NIGHTCAP_TARGET_CANDIDATE` to the absolute combined staging directory to run the launcher tests on the real files. The standalone registry/editor checks and the unchanged equipment and target regressions are client-side checks.

The Equipment guide and Recent changes contain staged instructions. Home, Features, commands and numeric item/zone catalogs have no content change. The combined wiki preview was built from the retained Cairnwright wiki plus the earlier comparison copy. All 24 wiki, player-language and refresh tests passed, as did search and equipment checks. The source refresh checker reported historical drift and flagged the new client files. The signed channel and public wiki have not been changed.

## In-game QA

1. On a QA installation with the combined client, fully exit EQ and use Play with MacroQuest closed. In the East Commonlands tunnel, inspect a Platinum Fire Wedding Ring (14679). Check that Description, Lore and Notes are available.
2. In Notes, enter `Save <for> A & B` and select Save. Switch to Description. Expect the exact text beside the ordinary item information and the two ring comparisons. Reinspect another copy of 14679 through an item link.
3. Inspect a Golden Fire Wedding Ring (14678) in a second window. Give it a different note. Edit each window in turn and confirm each description shows its own text. Change an edit without saving, select Reload and check the previous saved version returns.
4. Reload the UI, zone and relaunch the game. Inspect both rings with another character on the same Windows account. Confirm each saved note persists. Save a blank field for the platinum ring and verify only that note disappears.
5. Test keyboard focus, a long note, a narrow saved window and an accented character supported by the client. Check that target level/class and worn comparison still work. A separate Windows account should start with its own note collection.
