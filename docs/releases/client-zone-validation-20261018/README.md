# Classic travel archive validation and repair — October 18, 2026

Intent: prevent missing or corrupted managed zone archives from stranding players
after zoning, and deliver the West Commonlands repair through normal launcher Play.

## Evidence and diagnosis

Karl's October 12 screenshot explicitly identified missing zone file `commons`.
The October 18 incident reached West Commonlands, never completed client-ready,
became linkdead at 04:10:47 UTC, and the empty zone unloaded at 05:09:44 UTC.
This supports a client loading failure, not a server process crash. Karl's current
computer is not accessible here, so this repeat incident's local file state is
not independently observed. The earlier repair ZIP was never confirmed installed.
Today's location rescue is recorded separately in the default checkout's
`docs/ops/karl-rescue-20261018.md`.

Live signed release 2026101702 contained 106 managed files and omitted both
`commons.s3d` and `commons_obj.s3d`. The patcher already hashes every signed managed
file on checks/Play and repairs missing or mismatched files, even at the same
release. Unlisted base-client files are outside that validation. Toxxulia/Misty
had the same known delivery omission after an owner-local October 12 repair.

## Implementation and scope

`assets/client-zone-archives.json` pins terrain/object bytes for the 17 previously
audited Classic travel destinations. `tools/client_zone_archives.py` verifies
SHA-256, all PFS entries and expected WLD headers before generation. Packaging
requires the same 34 paths. The existing Nektulos pair is retained; 32 paths are
added to the 106-file signed inventory, totaling 138. All prior asset bytes,
minimum launcher 0.6.0, history and tombstones are preserved.

This is bounded coverage, not a complete RoF2 installation validator, not a claim
that every zone dependency is covered, and not a repair for arbitrary native
crashes. Character archives, sounds and unrelated files outside the existing
manifest remain outside this addition. No settings, executable, DLL, server,
database or gameplay balance changes are needed.

Plan: reproduce missing packaging coverage; validate pinned sources; require them
in generation/packaging; exercise inspection/staging/install; preserve the live
signed inventory in a higher-counter asset-only release; rehearse atomic publisher
recovery; verify hosted content; retain native zoning acceptance as separate QA.
Rejected alternatives: another manual ZIP leaves other clients unprotected;
rebuilding the desktop duplicates working hash/repair behavior; a fresh generic
asset generation risks replacing newer live spells/UI/DLL assets.

## Verification and release

Initial packaging regression failed because `butcher.s3d` was unlisted. Full
launcher suite then passed. Python generator tests passed (11 tests across zone,
gameplay and hub modules). `archive-verification.json` records 34 complete PFS and
WLD-header checks against the retained sources; it is not native rendering QA.
Dedicated tests cover missing terrain, same-size corruption, current-file reuse,
bad download rejection, installation repair and settings preservation.

Independent review found the publisher accepted any earlier release. It now
requires exact baseline 2026101702 inside `publish()` and at entry; regression
coverage rejects a different baseline. Cross-model review was offered and declined.

Published game release: **2026101801**, signed using the existing local production
key. `sign-client.go` and `verify-client.go` run within eq-launcher to use the shipped
manifest parser. Private staging is `/opt/nightcap/releases/client-zone-validation-20261018`.
`published.json` confirms activation; `hosted-verification.json` verifies the shipped-key signature and all 138 hosted files (278,996,304 bytes). No main-branch gameplay promotion is
implied. The publisher preserves all five service identities and unrelated public
root files, fsyncs nested directories, and switches the signed channel last.

Recovery: on interruption inspect the retained previous channel, candidate inventory,
service baseline and immutable target. Resume only the same verified operation.
Never lower a release counter or delete current player files. A content rollback
must use newly signed higher metadata and reviewed file policy; removing entries
from the manifest alone does not remove already installed archives. Reverted
packaging source would lose coverage in future generations, so preserve the catalog.

## Exact player QA

1. Close EverQuest and the launcher. Reopen the usual shortcut, select Karl's actual
   game folder, and press Play. Confirm game release 2026101801 or a later release
   retaining these archives; keep desktop 0.6.0 or newer.
2. Log Karl in at East Commonlands. Enter West Commonlands through its zone line;
   confirm terrain/objects render and movement works. Return to East Commonlands.
3. Repeat the West Commonlands trip using Khalure's travel option and direct say
   route. Check Misty and Toxxulia travel, terrain, landing and return paths.
4. In a disposable client copy only, remove commons.s3d and alter commons_obj.s3d;
   check that Play restores both before starting and preserves settings. Never
   damage a player's live installation merely to demonstrate repair.
5. If Karl still fails, retain that installation's fresh dbg.txt/error dialog and
   launcher file status; do not infer another missing file from linkdead alone.

Owner acceptance — October 18: after the request to update through launcher Play and test East Commonlands to West Commonlands and back, the owner replied ‘Confirmed’. Record Karl's reported zoning issue as resolved. This does not attest every Khalure route, Misty/Toxxulia destination, deliberate-corruption scenario or the entire RoF2 installation; those broader checks remain open.

Wiki: release 20261018-client-zone-repair-v1 published using the existing guarded updater. Fourteen content/refresh tests and sixteen Linux deployment/recovery tests pass. Existing config, private downloads and all five service identities are preserved. Whole-wiki impact assessment is in wiki-review.json.
