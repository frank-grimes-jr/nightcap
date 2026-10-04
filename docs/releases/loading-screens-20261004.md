# Nightcap loading gallery

**Published October 4, 2026:** [PR 124](https://github.com/frank-grimes-jr/nightcap/pull/124)
merged to main at `70fd26a6ce6e22be9f6b6bdbdf4a6762291ef3b6`. Signed game
**2026100407** and launcher **0.4.0 / channel 2026100401** are live on OVH.
Fully exit EQ and the launcher, then reopen the normal Nightcap shortcut.

The owner requested publication to main and the hosted server of all ten approved
paintings. Acceptance: every pinned RoF2 loading slot uses this set, all ten scenes
are included, the signed production launcher installs them, main contains the
sources and repeatable builder, and hosted signatures/hashes verify. Existing game
files, player settings and running services must be preserved.

## Plan and implementation

1. Add the ten original PNGs and prompts under `assets/nightcap/loading-screens/`.
2. `tools/client_loading_screens.py` generates baseline RGB JPEGs, preserving each
   full 1672x941 frame. Slots 01–55 cycle through all ten paintings; the gnome is the
   fallback. No artwork is cropped or stretched during generation.
3. Extend the launcher/packager for exactly `resources/loadscreen.jpg` and
   `uifiles/default/loadscreens/loadscreen01.jpg` through `loadscreen55.jpg`.
   The pinned executable names those paths directly, independent of selected skin.
   Protect all other default UI files. No binary hooks are needed for selection.
4. Publish desktop 0.4.0 before the game release requiring 0.4.0. Preserve the
   installed stable starter and all 48 prior game files byte-for-byte. Stage and
   verify immutable assets first, then replace signed channels under the existing
   deployment lock. Retain prior metadata and immutable releases.
5. Test complete coverage, full-frame image fidelity, strict file-scope rejection,
   version gating, package/patch/recovery and signed public delivery. Independently
   review the security boundary and publication procedure before deployment.

The source client stays read-only. Generated assets and operational evidence live
under `E:/EQ_Local_Dev/artifacts/loading-screens-20261004/`.

## Recovery

Keep the prior launcher and game channels and all immutable files. If interrupted,
resume only when public channels match the captured old or candidate hashes.
Once published, never decrease counters: sign a higher game release containing
the previous 48 files and the captured stock loading JPEGs to undo the artwork.
Keep desktop 0.4.0 while restoring images. The launcher journals/backups provide
per-client interrupted-install recovery. No database write or service restart is
part of this release.

## Native visual check

Close EQ and the desktop; start the normal Nightcap shortcut. Confirm desktop
0.4.0 and the published game release. Load character selection and enter a zone,
then zone repeatedly with random loading screens enabled. Verify NIGHTCAP branding,
full image visibility, readable native progress text, and the gnome's three pets.
Test fixed/default load-screen modes too. Publication/hash checks and native image
decoding do not by themselves record visual player acceptance.

## Verification

Game release **2026100407** contains 104 files (48 unchanged plus 56 JPEGs),
211,896,707 total bytes, and requires desktop **0.4.0**. Its signature verifies
against the existing shipped production key. Desktop channel **2026100401**
also verifies against that trust. The compiled desktop retains the starter-era
22-path inventory for old schema-1 recovery journals. The existing public starter
ZIP is retained. Upload only the new images, launcher and metadata; reuse the
48 existing files on OVH after size/hash verification against the signed baseline.

Normal and production Go suites and production vet pass. Frontend build and
dependency audit pass (zero vulnerabilities). Complete 56-slot installation and
injected-interruption recovery pass on Windows, including the stock mixed-case
Resources directory and preservation of settings/default UI. Image coverage and
whole-frame pixel fidelity pass. Publication rehearsals interrupt immutable staging,
desktop-channel commit and game-channel commit; retries preserve monotonic channels
and prior backups. Concurrent public drift and mismatched reused files are rejected.

An independently compiled x86 harness using the client's actual `d3dx9_30.dll`
decodes all 56 JPEGs to pixels successfully, with ten distinct results and the
stock image as a control. GPU CreateDevice is unavailable in the execution
environment; native viewport aspect and progress-text placement remain visual QA.
[Decoder evidence](loading-screens-20261004/native-decoder.json) and
[local signature/hash verification](loading-screens-20261004/local-verification.json).
Independent review found and resolved the initial packager-version floor and
canonical-generator integration gaps; the final implementation and publisher have
no remaining required findings.

## Production receipt

The user explicitly approved both the GitHub repository/main publication and
OVH destination/payload after automatic approval review requested those details.
The 63-file upload contained only new artwork, launcher, metadata and publisher;
the 48 existing client files were reused on-host after signed hash verification.
The publication lock and fresh baseline checks preserved the concurrently deployed
universal-trading server. Immutable assets preceded the desktop channel and then
the game channel. No game, database, gateway, web or tunnel restart occurred.

Independent HTTPS verification read all 104 files (211,896,707 bytes), checked the
game signature against the shipped production key, and verified desktop channel
signature and executable bytes. All 56 image hashes match the approved gallery,
all ten paintings are represented, and all 48 prior game files are byte-identical.
The stable starter ZIP and guide are unchanged. Game and database are healthy.

- [Deployment checks](loading-screens-20261004/deployment.json)
- [Public game verification](loading-screens-20261004/hosted-verification.json)
- [Public launcher verification](loading-screens-20261004/hosted-launcher-verification.json)
- [On-host publication receipt](loading-screens-20261004/published.json)

Prior channels remain under `/opt/nightcap/releases/loading-screens-2026100407/`
as `previous-channel.json` and `previous-launcher-channel.json`. Retained stock
loading images and local release evidence are in the artifact directory above.
Rollback remains a new higher signed release; never republish the older counters.
Native in-game viewport appearance has not been recorded as accepted.
