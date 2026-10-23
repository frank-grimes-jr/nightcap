# Production-backed wiki loot finder

October 22, 2026. **Implemented and locally verified; production installation and
public publication are pending.** Owner requirements: any held class is the
default, and production data refreshes automatically.

The candidate selects up to three held classes, with an optional all-class mode,
and filters active-era equipment by name/ID, slot, quality, maximum required level
and source zone. Item links display public stats, NPCs, zones, level-dependent drop
chances, spawn locations in `/loc y, x, z` order and spawn conditions. Filters,
pagination, item links and browser Back use URL state. Existing handbook, Build
Lab, Hunt catalogs and Hate Keeper owner confirmation are retained.

The public wiki reads a1.6MB index and requested item JSON. The production reader
is prepared to run every15minutes; it uses fixed field-allowlisted read-only SQL
and publishes an immutable complete generation before switching `current`.
No player/account tables, credentials or arbitrary database queries are exposed.
Failures retain the last good capture. The browser shows its time and warns after
45minutes. Scope and calculated-vs-observed limits are visible in the guide.

## Evidence

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
  computer during these tests. `linux-verification.json` records exact results.
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

## Release and recovery boundary

The feature branch starts from the latest combined wiki source `b077d49`; the
subsequent owner-confirmed Hate Keeper prose was preserved from the maintained
wiki checkout. Reconcile any newer publication before deployment.

The next action requires approval to install the reviewed reader/timer and public
JSON route on OVH, then publish this wiki with released labels. The
[AI-native SDLC skill](C:/Users/verre/.codex/skills/ai-native-sdlc/SKILL.md) requires
“a human approval boundary” for production-facing changes. No gameplay promotion,
database mutation, client patch, game restart or Cloudflare change is needed.

[Guarded install and inverse](../../ops/wiki-loot-reader.md) preserve current wiki,
private downloads and service IDs/start times. Receipts, preimages and snapshots
remain available for recovery. Acceptance steps: [QA.md](QA.md).
