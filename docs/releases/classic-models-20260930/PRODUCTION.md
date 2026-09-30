# Classic model defaults: production activation

Published September 30, 2026, at `play.nightcapgame.org` after the owner explicitly
requested "Push to main and server". Source moved through PRs 88 (dev), 89 (test)
and 90 (main). Main at publication was `c67ee0e2eeaeeeecf8d70003a0a81666e9e2c5a9`.
Deployment approval does not record completed in-game visual acceptance.

## Delivered release

Signed game release **2026093004**, proxy **0.7.0-dev**, contains 46 managed files.
The existing Nightcap starter and desktop **0.3.1** download it before Play.
Players should exit the game, reopen their usual starter, and confirm this game
release before launching. No new launcher ZIP is required.

- Old player, Magician elemental, skeleton, spectre and other counterpart models
  are the default. The catalog protects 144 race/gender registrations and maps
  98 later remakes, using 22 isolated archives plus one import list.
- Races without old counterparts keep their existing models, as requested.
- Modern alternatives require `[Nightcap] UseModernModels=TRUE` in the game
  folder's `eqclient.ini` and a complete restart; native Luclin preferences then
  apply. Existing Luclin settings alone cannot enable the alternatives.
- Current main's compact Pet Info layout is retained. Relative to the previously
  hosted release 2026092201, 23 model assets are added and five files change:
  proxy, bootstrap helper, configuration, catalog and Pet Info XML. The other
  18 managed files are identical. User INIs are excluded from the inventory.

The latest Enchanter animation command source already on main is retained in
Git. This model publication changes only client delivery; it does not activate
any additional native server change.

## Verification and preservation

[Production evidence](production.json) records the release, artifact hashes,
public verification and service preservation. All 46 files, totaling 148,621,472
bytes, passed size/hash checks both locally and over public HTTPS. The signature
verified against the public key already shipped in desktop 0.3.1. The channel
SHA256 is `9b7fcf0d79c5ba6fef677f58ea7585ebc79161faa964961dd95145c357c3b57a`.
Game metadata expires **2026-10-30 19:21:38 UTC**; existing desktop metadata
retains its separate expiry.

The staged publisher verified immutable files before switching `channel.json`.
All five services retained their container/image identities, start times,
restart counts and health. Game and database remained healthy. Desktop channel,
starter ZIP and guide hashes are unchanged. No game restart or database/quest
write was needed. The original development client was read only.

The model proxy/helper/catalog and model assets are the exact bytes covered by
the earlier [native and isolated startup evidence](verification.json); only the
generated Pet Info layout differs from local QA release 2026093003. No new
automated test suite or authenticated/rendered gameplay session was run for
this publication. Follow the [owner visual checklist](QA.md).

## Recovery

- Host package and exact publisher: `/opt/nightcap/releases/classic-models-2026093004`.
- Previous game channel: that directory's `previous-channel.json`.
- Immutable prior files: `/opt/nightcap/deploy/production/data/public/release/2026092201`.
- Local verification and public-only deployment bundle:
  `E:/EQ_Local_Dev/artifacts/classic-models-20260930/`.

The [publisher](publish.py) is specific to this staged release and its captured
baseline. It refuses unexpected public metadata or service drift. The production
private signing seed remains local and was excluded from the upload.

To reverse the model policy, sign the previous reviewed proxy/helper/configuration,
catalog and gameplay inventory as a **new game release above 2026093004** using
the compatible prior packager. Publish immutable files before the new channel.
Never restore the older channel counter or reset player checkpoints. Preserve
user INIs; the isolated classic archives are inert under the prior proxy.
No server or player-data rollback is required for this client-only release.

## Remaining acceptance

Rendered model appearance, armor, animations and zoning remain open. The exact
checks cover all four Magician pet types, skeleton families, spectres, the listed
remakes, native models for races without classic counterparts, and both INI
modes. Deployment, hashes and startup evidence do not replace those checks.
