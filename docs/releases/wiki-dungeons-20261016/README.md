# Raid & Grind wiki publication — October 16, 2026

Published [Raid & Grind dungeons](https://wiki.nightcapgame.org/dungeon-modes.html)
as `20261016-dungeons-v1` after the owner's explicit wiki-update request.
The retained previous release is `20261016-features-v1`.

The guide covers all seven dungeons, mode selection, personal encounter credit,
shared completion rewards, exclusive Raid drops, persistent claims and reset
rules. Features, Travel, home, Getting started, Equipment, Item upgrades and
Recent changes link or explain the deployed feature. In development no longer
lists it as unavailable. The separate hunt catalog remains unchanged. The whole
wiki was reviewed in the dungeon release; publication preserves Live testing
labels and does not close gameplay or level-50 dragon balance acceptance.

Verification: 14 Python content/source tests, 13 Node search/equipment cases and
16 Linux publisher recovery tests pass. The immutable package contains 455
articles, 458 HTML pages and 465 files. Origin and public HTTPS verification
match every file hash. Security/cache headers, ten denied private/source routes
and write-method denial pass. Browser search returns the new guide first for
“raid grind”; the guide has no horizontal overflow at 320/768/1024/1440 widths,
one title and no console warnings/errors. Desktop and 390px views were inspected.

The existing guarded updater atomically switched only the wiki pointer,
rehearsed the previous release and reapplied the new release. All five service
identities/start times, private downloads, public player access and Nginx config
were preserved. No restart, reload, SQL, native/cache/client or access-policy
change was needed. Initial Windows test failures were sandbox temporary-directory
permissions; the unsandboxed run passed. The first Linux run lacked the static
Nginx test fixture; supplying that fixture made all 16 tests pass before activation.

Receipts: `origin-verification.json`, `public-verification.json`,
`browser-verification.json`, `release.json`, `source-manifest.json` and
`linux-tests.txt`. The publisher source is unchanged from the maintained wiki.
Exact package and hash manifest remain in the task's `work/wiki-publication/`;
server receipts are under
`/opt/nightcap/deploy/production/website-history/20261016-dungeons-v1/`.

Recovery: hold `website-history/.lock`; require the current pointer to equal
`releases/20261016-dungeons-v1` and config SHA-256
`03ef62717aad29884d3c1a60d800b19d0ee9cc7024fec7313d0263f37fbd046c`.
Validate the retained previous manifest/release, atomically restore the relative
previous pointer, then rerun full origin/public and private/service preservation
checks. Never overwrite a later pointer/config or use the initial installer.
Keep both releases and all receipts. Player activity requires no rollback.
