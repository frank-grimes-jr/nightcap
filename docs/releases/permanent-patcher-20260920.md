# Permanent patcher — September 20, 2026

The owner approved automatic patching and launcher self-updates, with main promotion and application to production. Launcher **0.3.0**, independent launcher release **2026092001**, and game channel **2026092006** are published at [play.nightcapgame.org](https://play.nightcapgame.org/guide.html). Download [the one-time starter ZIP](https://play.nightcapgame.org/nightcap-friends.zip), retain it in a permanent folder and make a shortcut to `nightcap-launcher.exe`. Existing game folders and saved launcher selection remain usable. Subsequent routine updates use that shortcut.

The starter checks and updates the signed desktop launcher. The desktop checks on opening/selecting the game folder and applies required patches before Play. Only changed files are downloaded. Game inventories and patch catalogs can evolve without recompiling the launcher, within compiled client-identity, path and trust boundaries. Interrupted update recovery retains signed destination authority. See [ADR 0043](../adr/0043-permanent-nightcap-patcher.md) and [operator instructions](../ops/permanent-patcher.md).

## Verification

- Full Go suite passed, including exact supported RoF2 preflight, evolving signed catalog checks, disposable installer/launch locks, native C++ config/health agreement and bootstrap/session fixtures. The original client was read only.
- Automatic Play tests cover update-before-start, current-file reuse, corrupted active-signature repair, refreshed verification time, cancellation, recovery and no launch after failures.
- Real Windows fixture EXEs proved version-one to version-two launch from the same starter implementation/cache. Tampering, unknown/wrong keys, rollback, expiry, incomplete downloads and concurrent starters are rejected. Native progress-window cancellation/hiding tests pass.
- Default and production-tag Go suites, `go vet`, frontend typecheck/build, production Wails build and compiled-trust channel verification passed. Dependency audit: zero vulnerabilities.
- Eight real-Chrome UI tests passed, zero unexpected failures/skips. Desktop/narrow screenshots were inspected. Vite teardown hung after the assertions; the identified test server was terminated, after which Playwright emitted its successful report.
- Independent review found and resolved stale launch-time verification, repair of corrupt cached signatures, signing-key/build agreement and publication interruption gaps. Final reviewed publisher SHA256: `7ea4a3132bdf00fc205bb050db08bfb86121a4f27f8f1ff1122e816b34584ceb`.
- All **63** injected publication copy/rename failures resumed successfully with all originals preserved. New starter ZIP visibility always followed launcher-channel availability.
- Hosted verification used the production Go trust and actual starter download/locking implementation: both signatures, all 22 game files, desktop EXE, ZIP and guide passed. The hosted desktop was not executed against the owner's real game folder during this check.

Evidence: [native/default suite](permanent-patcher-20260920/go-tests.log), [production suite](permanent-patcher-20260920/go-production-tests.log), [browser result](permanent-patcher-20260920/browser-tests.json), [hosted result](permanent-patcher-20260920/hosted-smoke.json), [publication recovery](permanent-patcher-20260920/publication-recovery-tests.json), [public file hashes](permanent-patcher-20260920/publication-files.json).

## Publication and recovery

Twenty-seven hosted files were verified after activation. A release audit is retained in staging. The 22 gameplay files are byte-for-byte identical to release 2026092005; this release changes delivery and launcher compatibility, with no DB write, game-server restart or native image change. Services remain running, with game and DB healthy. Prior ZIP/guide/game channel are retained at `/opt/nightcap/releases/patcher-2026092006/previous-public`; prior immutable images remain available.

The reviewed [publisher](permanent-patcher-20260920/publish.py) uses resumable verified hidden-directory staging, then launcher channel → ZIP → guide → game channel. [Failure rehearsal](permanent-patcher-20260920/test_publish.py) uses disposable public-file fixtures. After a channel becomes visible, rollback means publishing previous reviewed bytes under a **higher** signed counter; never rewind players' checkpoints. Public signing metadata needs renewal before its October 20 expiry. Starter trust needs a reviewed migration before September 20, 2028.

Hashes:

- Starter EXE: `1f12b6f5c361a46fce152cf70a4398505535f6d89a8a9bdca8159111e36b24af`
- Desktop EXE: `8400d547cf93f585406bc4ccfe21b884e07e3bd40a67bb09c7813521a64ccc22`
- Friends ZIP: `2abdb9f293daad239e0d0cc656ce7153c9e2ffb47580196306aaf222963b6a5c`
- Game channel: `6e5d2b95d3ac9be29949bb839153aeb0040d43e6013c56ad3e069c8216f0e23d`
- Launcher channel: `b81f97154e1b78f890b6cab3af95cbf59679ff8633ea1e8db2055baea2ab3963`

## Exact owner QA remains open

1. Close old launchers, extract the transition ZIP and open its stable starter shortcut. Confirm launcher 0.3.0 and select the existing dedicated RoF2 folder.
2. Press Play without manually installing updates. Confirm release 2026092006 installs/validates and the game starts. Keep the launcher open through the session.
3. Close game/launcher and open the same shortcut again. Confirm it opens without downloading/replacing a new ZIP.
4. On Monktest, repeat [the production NPC/spell QA](production-bugfixes-20260920.md#exact-owner-in-game-qa): selected-class usable vendor filtering, normal spell levels/scribing, error-free Tunnel Trader hails and auction WTS/WTB after 75–120 seconds.

The owner stated the gameplay fixes have not yet been tested. Automated update/transport evidence does not close that acceptance gate. Binary-delta downloads, automatic release renewal and automatic trust-key rotation are outside this release.
