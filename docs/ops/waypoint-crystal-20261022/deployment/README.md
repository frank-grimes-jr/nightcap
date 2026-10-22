# Waypoint crystal production release — October 22, 2026

The owner authorized **“Merge to main and server”**, selected a glowing crystal
with its waypoint label, and confirmed **“EverQuest is fully closed”** before
activation. This release is installed for live QA; native visual acceptance is
still open. No standing approval for future releases is implied.

## Source and delivery

Main PR280 is `f293626d4ddb69d464806084308f00b93ca8f35f`, following dev PR278
and test PR279. Signed game **2026102202** supersedes **2026102201**. It replaces
the DLL, paired catalog and Classic import list, adds the Modern import list and
`crs.eqg`, and preserves all135 other descriptors/URLs, including the robe assets.
The assembled140-file inventory retains patch history and the25-file model
contract. The production signing key stayed local; no seed was uploaded.

`signed-candidate.json` and `stage.json` are historical preparation receipts.
`deployment.json` records the actual atomic publication. The separate
`hosted-verification.json` verifies the shipped production signature, all140
HTTPS files (279,409,074 bytes) and actual new DLL/catalog compatibility.
Exact executable preflight is recorded separately in `signed-candidate.json`. Channel SHA256:
`5b897b3577b0b01be65eaf603bbf9eb3fd64af8459213dc01ccddb820981788c`.

The previous envelope is retained privately at
`/opt/nightcap/releases/waypoint-crystal-20261022-v2/previous-channel.json`.
Its SHA256 is
`78e1173d2279ff185c883645f8c2d43e1d1454676bf696f8ac0b545d2e3174fa`.
Published asset and paired catalog hashes are in `signed-candidate.json`.
The protected reference and installed client folders were read only. No desktop
launcher build was required; users fully close EQ and use normal launcher Play.

## Quest activation

`quest-check.json` verified zero connected clients, an unlocked world and an
unpaused gateway. `activate.py` extracts the quest directly from promoted Git
source and sends the committed LF bytes, checking normalized checkout identity.
The earlier candidate/Windows checkout hash is not the Linux deployment hash.

The deployed quest SHA256 is
`4b15350087dfd4153ea2ef98e418da9696b0c7efe99cdd8fe62cb96483f764a2`.
`quest-apply.json` verifies the host/container bytes,12 aggregate quest-reload
acknowledgments and signal20261022 to NPC999240. Aggregate logs do not identify
each worker or prove rendered appearance. Unbooted zones apply the script on
normal spawn. No quest compilation errors were observed.

The operator holds the shared deployment and GM locks, retains exact originals
under `/opt/nightcap/backups/waypoint-crystal-20261022`, and briefly locks world
admissions and pauses the gateway before rechecking zero clients. World lock
alone permits GM bypass. Admissions were restored after activation; world and
all12 zone lifetimes, all five service identities/start times and Keeper quest
SHA903086e6… remain unchanged. No database mutation, process kill, native restart,
repop or saved-state rewrite occurred. Waypoint positions, discovery and rewards
are unchanged.

## Checks and review

- Existing implementation checks are retained in `../verification.json`:
  quest19, Keeper52, Python27, x86 build/runtime,288 native animation cases,
  invisible-actor regression,107 exact-client guards and launcher pairing suites.
- Client publisher:11 Linux tests, including inventory/history preservation,
  preimage drift, interrupted staging and service/control preservation.
- Quest operator:13 Windows and13 Linux tests, including active-client refusal,
  admission restoration, reload failure, owned partial recovery, foreign partial
  rejection and exact rollback retry. `quest-stage.json` records Linux execution.
- Independent review initially found interrupted-install and rollback-retry
  blockers; both were fixed and independently rerun through all13 tests before
  activation. The retained source includes those fixes.
- Wiki content:14 Python tests,6 search and7 equipment checks;458 pages built.
  Publication uses the unchanged guarded updater and runs16 Linux recovery tests
  before swapping. `wiki-publication.json` and `wiki-public-verification.json`
  separately own publication, rollback rehearsal and public465-file verification.

## Recovery

Do not replay an old signed counter or restore player data. Inspect the actual
current channel, quest, services and ownership of a held gateway before recovery.
These helpers deliberately refuse unrelated later releases or quest changes.

For this exact quest release, fully exit clients and run from this directory:

```text
python -B activate.py rollback
```

This restores exact retained quest SHA
`f8fe9a8783e28b6685104a73769cf083c17ef5c411c9bc616e9fc3a420684e65`,
reloads without resetting timers, and signals NPC999240 with20261011. The retained
old handler actively restores race127/gender0/size6 and portal178; a temporary
handler is unnecessary. Restoring bytes alone does not reverse an active illusion.
The original world-lock intent is preserved. After an uncertain post-write failure,
admissions remain held until recovery verifies. Validated retained-payload prefixes
may be removed from the owned partial file; foreign/symlink partials are refused.
A rollback retry must match the original recovery receipt and runtime snapshot.
Recovery logic was fault-tested, not exercised against the successfully activated
live quest.

If client rollback is needed, assemble a fresh complete inventory from the current
release and replace only its three changed prior descriptors with the retained
matching old DLL/catalog/Classic list, preserving unrelated later assets. Keep the
two added crystal files inert, retain patch history, assign a higher game counter,
sign locally, verify the actual pair/all assets and use guarded publication.
Native clients must fully exit and update. Do not run this rollout's pinned
publisher against a new release without a separately reviewed preimage.

## Player acceptance

Follow the five-step [native QA](../README.md#exact-in-game-acceptance): Befallen,
Unrest and Crushbone; particles low/off; both model modes after full restart;
names, scale and low ceilings; attunement/recall; late joins and saved-state loads;
separate Keeper selection. Race425's additive material makes particles-off
visibility a required empirical check. Successful delivery and reload do not
establish that acceptance.

Wiki **20261022-waypoint-crystal-v1** is published and verified across all465
public files with security headers and five private-source route denials. Only
Waypoint Explorer, In development, Recent changes and the search index changed.
