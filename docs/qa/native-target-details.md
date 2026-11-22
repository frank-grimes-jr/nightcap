# Native NPC target details

The first Nightcap feature inspired by MacroQuest's TargetInfo shows a second piece of information when a player targets an NPC. A label such as **Lv 12 Cleric** appears between aggro and buffs. The client uses the current spawn's displayed level and class and recognizes trainers, merchants and other service roles. Unknown class IDs display the level alone. Clearing the target, selecting a player or corpse, or leaving the game clears the line. The feature uses the existing Nightcap label provider and signed launcher asset path. It adds no command or server request.

## Candidate checked on November 22

Source base `92f2aa7b`. The local candidate in `eq-client-dll/build/target-details/` contains the following paired files. The public channel and protected RoF2 reference were not modified.

| File | SHA-256 |
| --- | --- |
| dinput8.dll (x86, 0.14.0-dev) | `8d8450a1bbdd593199a15ca7253d9d34435aba73ffb06cd0cafea9c017b2a677` |
| nightcap-patch-sites.json | `7ef4b66df87917db27f7d62bac3b679d61b562226d6a4c147b5017cfe524b120` |
| uifiles/nightcap/equi_targetwindow.xml | `ec59307a3091696b6c3284c829615628131ad4814d522c708b5d6c0a7e11f60f` |

The stock target XML digest is `2db371c2c24ed67d026b2c47e66eeb1d3645273c7ec073b9a98ee883d0dfa657`. The generated skin retains all 12 target window pieces and their order. It adds 17 pixels of default height and moves the buff pane down 17 pixels. Saved window sizes still need a visual check.

The production code lives in `eq-client-dll/src/target_details.h` and the existing `LabelHook` in `ui_hooks.h`. The read-only game-state and current-target fields belong to the pinned RoF2 build. Native level and class reads were checked against the local executable. The zone spawn encoder sends the NPC class and targetability. The test uses synthetic selections in the same layout and exercises immediate replacement, clearing, zoning, service and unknown classes. The XML generator lives in `tools/client_target_ui.py` and runs through `tools/client_gameplay_assets.py`.

Run `eq-client-dll/tests/run-target-details.bat` and build with `eq-client-dll/build.bat`. Run the Python target and existing gameplay asset tests from `tools`. In `eq-launcher`, set `NIGHTCAP_TARGET_CANDIDATE` to the absolute staging directory and run `go test ./cmd/nightcap-package ./internal/preflight ./internal/manifest`. The real paired files passed the packager's skin and proxy/catalog checks. The exact executable and retained configuration passed all 120 static preflight sites.

## Player QA

1. On a QA installation carrying the candidate, fully exit EQ and launch through Play with MacroQuest closed. Log in and open the target window.
2. In East Commonlands, select the Plane of Hate Instance Keeper at the tunnel. The October keeper record lists NPC 998812 as level 50, class 1. Expect **Lv 50 Warrior** if that spawn is still configured the same. Check the selected spawn with GM Show Stats on the QA server if its data differs.
3. Click a tunnel merchant, then target the keeper again with the keyboard. Verify the merchant label and level match the merchant and the keeper line returns immediately. Press Esc, target yourself, then target a corpse. The detail line should be blank in each case.
4. In combat, check name, con color, HP, aggro and buff icons while the details are visible. Check a long class name and the saved window size. Resize, reload the Nightcap UI, zone, and relog. Confirm the current selection supplies the label after each transition.

## Release and wiki

Include the proxy, matching catalog and generated target skin in the same signed release based on the current channel. Preserve pending Cairnwright client assets and the exact unrelated file descriptors when assembling the release. Players receive the feature on a full exit and launcher Play after publication. No server binaries, SQL, cache reload or launcher executable change is required. A recovery release can restore the previous proxy/catalog and stock target layout together.

Reviewed the combat guide, Features, Home, commands, Recent changes and item/zone catalogs against the November 21 Cairnwright wiki source. The refresh checker reported historical source drift and flagged the client files. The candidate is local. At publication, add the target-selection instruction to Combat and a short entry to Recent changes. No catalog or command values change.
