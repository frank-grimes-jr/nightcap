# Native target and item windows in production

Signed launcher release `2026112201` carries the native NPC target details, worn-item comparison and private notes from main merge `d845b6b7`. Fully exit EverQuest and press **Play** in the normal Nightcap launcher. Use the Nightcap skin. In-game acceptance is open.

The release replaces the x86 DLL and its matching patch catalog and adds the item display and target window skins to the signed inventory. The publisher validated the other 146 files at origin before switching the channel. An HTTPS check compared the public envelope and all four delivered files byte-for-byte with the signed candidate. Both parent and candidate passed the launcher trust policy and exact RoF2 executable preflight. All 20 Linux publisher tests passed. Game, gateway, web, database and tunnel retained their running identities. [Client receipt](client-verification.json)

The November 21 public spell file is retained. The DLL includes the class snapshot parser already on main. The separate Cairnwright spell update and birth-class work remain outside this release.

## Live QA in East Commonlands

1. Target the Plane of Hate Instance Keeper in the tunnel. The recorded spawn is a level 50 Warrior. Select a merchant, clear the target, and select yourself. Check the line updates each time and leaves space for HP, aggro and buffs. [Target QA](../../qa/native-target-details.md)
2. Wear a Silver Fire Wedding Ring and a Golden Fire Wedding Ring. Inspect a Platinum Fire Wedding Ring. Match the left and right changes to their respective worn items, remove one ring and inspect again. Repeat with a socketed ring and check that its augment contributes to the correct side. [Comparison QA](../../qa/worn-item-comparison.md)
3. In the platinum ring's Notes tab, save `Save <for> A & B`. Inspect another copy of that ID, then a gold ring. Check persistence after relaunch and confirm a blank save removes only the platinum ring's note. [Notes QA](../../qa/private-item-notes.md)

## Publication and recovery

The wiki release `20261122-native-qol-v1` updates Combat, Equipment, Recent changes and search. Its other 627 files match the prior public release. No command, home summary, numeric catalog or zone guide required an edit. The wiki updater rehearsed rollback. The public HTTPS check verified all 631 file hashes and five private-path exclusions. [HTTPS receipt](wiki-https.json) The source refresh check flagged historical drift going back to the October review. That broader review remains open. [Wiki receipt](wiki-publication.json)

The operator artifacts for this release are under `E:/EQ_Local_Dev/artifacts/native-qol-live-20261122`. They include the verified signed parent, the four-file release, the guarded publisher and its before/after receipt. OVH retains the staging directory `/opt/nightcap/releases/native-qol-20261122-v1`. For clients that have already accepted this release, recovery requires a higher signed release. Pair the previous DLL and catalog with compatible stock window layouts, verify against the current channel, and preserve each player's saved notes.
