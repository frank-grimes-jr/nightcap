# Production-backed wiki loot finder

October 22, 2026 (EDT). **Installed and publicly verified with owner approval.**
Active wiki release: `20261022-loot-finder-v2`. Owner requirements: any held class is the
default, and production data refreshes automatically.

The finder selects up to three held classes, with an optional all-class mode,
and filters active-era equipment by name/ID, slot, quality, maximum required level
and source zone. Item links display public stats, NPCs, zones, level-dependent drop
chances, spawn locations in `/loc y, x, z` order and spawn conditions. Filters,
pagination, item links and browser Back use URL state. Existing handbook, Build
Lab, Hunt catalogs and Hate Keeper owner confirmation are retained.

The public wiki reads a1.6MB index and requested item JSON. The production reader
runs every15minutes; it uses fixed field-allowlisted read-only SQL
and publishes an immutable complete generation before switching `current`.
No player/account tables, credentials or arbitrary database queries are exposed.
Failures retain the last good capture. The browser shows its time and warns after
45minutes. Scope and calculated-vs-observed limits are visible in the guide.

## Evidence

- Scheduled recurrence verified October23UTC (October22EDT): timer trigger01:40:27,
  service success01:41:15, capture `2026-10-23T01:40:27.396985+00:00`, snapshot
  `56ccc0c7378abfae`. Public current index matches origin; the prior immutable
  `c7da22524ad022f9` item still loads. All installed reader/unit hashes match the
  reviewed staging manifest. Timer remains enabled/active; free disk567,111,680bytes.
- Live HTTPS browser: Warrior/Cleric/Enchanter matches4,926items in any mode and
  1,440 in all mode. Item1365 shows frenzied ghoul, Lower Guk,59.04%,21haste and
  three spawn coordinates; Back/reload, mobile overflow and light/dark pass with
  no warning/error console entries. Screenshot hashes are in `deployment/live-browser.json`.
- Read-only capture `2026-10-23T00:33:41.070662+00:00`: production Classic0;
  9,688 captured definitions,6,293 published eligible items. Global loot multiplier4,
  ordinary quality chances20%/5%/1%. Captured rows remain only in ignored local
  `artifacts/wiki-loot/`; no raw capture is part of the release.
- Native comparison compiles the actual reviewed `NPC::AddLootDropTable` method
  with deterministic fixtures: six scenarios ×200,000rolls; maximum absolute
  error0.001631 (0.164percentage points). This validates the pool model, not current
  native binary identity, encounter access or player kill measurements.
- Linux publication/recovery tests, nginx syntax and unprivileged JSON traversal
  pass in local Docker with networking disabled. Source/content never leave the
  computer during these tests. `deployment/linux-verification.json` records62cases
  and native comparisons. Offline nginx integration also verifies encoded/identity
  JSON, denied raw paths and POST. Latest content/source/model checks:28passed.
- Windows model/source/site checks and Node filter/search/handbook/Build Lab checks
  are recorded in `verification.json`. Whole build:460HTML pages,467static files.
- Browser: any/all class filtering, three-class limit, name search, unsafe/no-result
  text, reset, pagination, Back, item reload, source locations and light/dark layouts
  at320/768/1024/1440. `browser-verification.json` records observed results.
- Independent reviews found disabled-spawn/global-flag edge cases, snapshot
  traversal permissions, regex quoting, interrupted pointer recovery, asynchronous
  nginx reload and systemd ownership/override issues. These were corrected and
  tested. The final installation review found no remaining substantive issue.
  The owner chose to finish with this review and tests, without another model.

Automatic approval review rejected an earlier plan to send the test bundle and
production fixture to the production host as unnecessary sensitive egress. It was
replaced with offline local Docker checks. No remote test bundle was uploaded.

## Deployment and recovery

The feature branch starts from the latest combined wiki source `b077d49`; the
subsequent owner-confirmed Hate Keeper prose was preserved from the maintained
wiki checkout. Its89d8d38source reproduced all466previous live file hashes before
publication. Reconcile any newer publication before future deployment.

The owner explicitly approved installing the reader, timer and JSON route and
publishing the wiki. Initial installation exercised the actual systemd sandbox,
verified a fresh capture, rehearsed the route/config inverse and enabled the timer.
Static publication rehearsed pointer rollback. Both preserved private downloads
and all five container IDs/start times. V2 corrects Windows-decoded UTF-8 article
prose; the original Unicode content is restored and the live reader is unchanged.

Production had about720MB free, so uncompressed snapshots would not fit retention.
Gzip-only storage reduces327MB JSON to23.34MB payloads per capture, with canonical
JSON URLs/hashes and nginx static gzip/gunzip serving. Before staging, the publisher
budgets file allocation plus256MiB reserve; low space leaves the last capture intact.
Fresh-context review and low-space/compression tests passed. Peak RSS655132KiB is
below the1GiB service limit. Scope expansion needs a new capacity check.

`deployment/` contains installation, both HTML publications, all467HTTPS file/hash/
header checks, nine private-route denials, JSON pairing, timer and live-browser
evidence. Server-side receipts are retained under `website-history/`; raw captures
are not committed or published. No gameplay promotion, database mutation, client
patch, game restart or Cloudflare change occurred. Browser verification is agent
QA, separate from future owner acceptance or native gameplay/balance testing.

[Guarded install and inverse](../../ops/wiki-loot-reader.md) preserve current wiki,
private downloads and service IDs/start times. Receipts, preimages and snapshots
remain available for recovery. Acceptance steps: [QA.md](QA.md).
