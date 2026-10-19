# Official Nightcap wiki — hosting and maintenance

Updated October 19, 2026.

## Current state

- **Public URL: https://wiki.nightcapgame.org/** — live and verified October 19, 2026 (EDT).
- **Active OVH origin release:** `20261019-client-contract-v1`; previous release
  `20261018-thj-parity-v1` is retained for recovery.
- **Features:** major departures from Classic, with dedicated upgrade and crafting guides.
- **Equipment:** 96 item families with four quality links each, gear/augment
  views, name/slot/level/zone filters, sorting and 12-family pagination.
- **Public hostname active:** the existing tunnel now routes the wiki to
  `http://web:8080`; its proxied CNAME was created automatically. The existing
  player-only WAF rule required no change.
- 455 articles: 21 maintained guides, 48 enabled zone pages, 384 item pages and
  two catalog indexes. All articles, Search and 404 bring the build to 458 pages.
- The exact publication contains 465 files. Player access uses the current personal-code
  policy; wiki updates preserve it. October 9 IP-only descriptions below are historical.

Source and build commands: [wiki/README.md](../../wiki/README.md).
Architecture: [ADR 0059](../adr/0059-official-public-wiki.md).

## October 19 client launch repair

Launcher, home and Recent changes explain signed game2026101901 and normal
launcher Play. The former candidate notice is removed; all other gameplay guides,
Features, commands and item/zone values are unchanged. Four public files changed
including search-index.json; all465 HTTPS hashes/headers and five private-source
denials verify. Guarded rollback rehearsal preserved private downloads, config
and all five service identities. Native gameplay acceptance remains open.
Evidence: [client contract repair](../releases/client-contract-20261019/README.md).

## October 18 cooldown and reforging corrections

The combined release preserves the published client-travel repair, adds the
verified cooldown identity guidance and clarifies built-in colors for reforging.
All465 public hashes/headers and five denied private-source routes verify. The
origin updater rehearsed rollback and preserved private downloads, configuration
and all five service identities. Thirty Linux tests and thirteen Node checks pass.
Owner gameplay acceptance remains separate. Evidence: [reforging release](../releases/reforge-colors-20261018/README.md).

## October 17 progression, combat and crafting

All 465 public hashes, origin pointer rollback and private/service preservation
checks pass. Recommended AA, 10% passive AA, Monk/duration fixes, normal death EXP,
minimum-100 stacks and 3/4/4 reforging guidance are published together. Owner gameplay
acceptance remains separate. Exact evidence: [combined release](../releases/october-17-2026/README.md).

## Dungeon guide — October 16, 2026

Raid & Grind is published as `20261016-dungeons-v1`. All 465 public hashes,
origin rollback/preservation and browser search/responsive checks pass.
See [release evidence](../releases/wiki-dungeons-20261016/README.md). No game
restart, client/cache, database, Nginx or access-policy change was needed.
Gameplay and balance acceptance remain pending.

## Features refresh — October 16, 2026

The Features hub and guide refresh are live in `20261016-features-v1`. All 464
public file hashes/headers pass; ten private/source wiki paths remain denied.
Current player-host behavior, private downloads and five service identities are
preserved. Rollback to `20261010-equipment-v1` was rehearsed; no Nginx reload.
The full [release record](../releases/wiki-features-20261016/README.md) separates
content, tests, production proof and remaining gameplay acceptance.

Every future Nightcap change requires reviewing affected content across the wiki,
including Features, commands, generated catalog pages and Recent changes. Run
`wiki/check_refresh.py` against the actual source authority and follow
`wiki/README.md`; do not blindly advance its recorded revision. No-impact changes
need a recorded assessment, and unpublished updates remain explicitly pending.

## Equipment update — October 9 EDT / October 10 UTC, 2026

The earlier `20261010-equipment-v1` was published at [Equipment](https://wiki.nightcapgame.org/items.html).
The catalog groups 384 variants into 96 families and keeps guides separate from
item browsing. All quality URLs remain reachable in static markup without JavaScript.
Mobile layouts use stacked cards; copied filter URLs and Back navigation retain
the selected view. Exact-name search recognizes all four published variant names.

The guarded content updater verified the new 461-file release, rehearsed rollback
to `20261009-wiki-v2`, and reactivated the new pointer. Nginx configuration, private
download hashes and all five container identities/start times stayed unchanged;
no reload or service restart was required. See [origin verification](../releases/wiki-equipment-20261010/origin-verification.json).
That update used `data/public/wiki/current` → `releases/20261010-equipment-v1`.
The immutable receipt is in
`/opt/nightcap/deploy/production/website-history/20261010-equipment-v1/`.

At 2026-10-10 01:01:29 UTC, public HTTPS matched all 461 file hashes and security/cache
headers. Eight private/source paths returned 404 on wiki; POST returned 403;
unapproved play access stayed 403. See [public verification](../releases/wiki-equipment-20261010/public-verification.json).
Live combined filters returned the expected two head-slot gear families at level
10 or below. Local browser checks also covered empty/reset states, pagination,
quality links, Back restoration, exact variant names, mobile cards and four widths.

Independent review identified config-drift recovery, interruption immediately
after pointer replacement, and exact variant-name search issues. All three were
fixed and regression-tested before publication; no material findings remained.

## Public launch — October 9, 2026

The authenticated dashboard added the third published application route to
`nightcap-production` (tunnel `3bc33805-1f74-487f-bc4b-621d07e8285c`):

| Order | Host / path | Service |
| --- | --- | --- |
| 1 (preserved) | `play.nightcapgame.org/connect` | `http://gateway:8080` |
| 2 (preserved) | `play.nightcapgame.org`, all paths | `http://web:8080` |
| 3 (added) | `wiki.nightcapgame.org`, all paths | `http://web:8080` |

All routes use default origin settings. Cloudflare created proxied CNAME `wiki`
pointing to `3bc33805-1f74-487f-bc4b-621d07e8285c.cfargotunnel.com` with automatic TTL.
The existing play DNS record was preserved. There is no direct public OVH A record.

The active `Nightcap allow` Block rule (`46c8a12408e64acbadc6d1d8c64b21ce`)
already restricts only `http.host eq "play.nightcapgame.org"` with the existing
approved-IP set. **No WAF, gateway allowlist, origin configuration or runtime
restart was needed for this public activation.**

At 2026-10-10 00:30:40 UTC (October 9 EDT), external HTTPS checks from OVH's
unapproved public egress passed all 461 SHA256 values, TLS validation, CSP and
`no-transform` cache headers. Eight private/source paths returned 404 on wiki;
POST returned 403. Play's homepage, channel, client archive and connection path
all remained 403 from that same source. See the
[machine-readable verification](../releases/wiki-public-20261009/verification.json).

Live browser verification passed item search (six results, exact item first),
item details/navigation, 390px item/home layouts without horizontal overflow,
desktop visual inspection and an empty warning/error console. Screenshots and
the read-only external verifier are in the local working evidence directory.

The stock Python-urllib user-agent was rejected by Cloudflare with error 1010;
the same identity reproduced the rejection in curl. Verification used installed
curl's normal identity and passed, without disabling or bypassing a security rule.

For public rollback, remove only the wiki application route and its DNS record.
There is no wiki WAF exception to reverse. Keep the existing play routes, DNS,
IP rule and gateway environment intact. Origin recovery is documented below.

Provider references: [Tunnel routing](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/routing-to-tunnel/)
and [IP allowlist custom rules](https://developers.cloudflare.com/waf/custom-rules/use-cases/allow-traffic-from-ips-in-allowlist/).

## Origin deployment and recovery

`wiki/deploy.py` is the initial installer. It refuses an existing wiki pointer or
hostname and checks the exact Nginx preimage. It uses the existing publisher's
`website-history/.lock`, validates all archive members/hashes with a 32 MB total
uncompressed budget, stores immutable releases, writes the bind-mounted config in
place, and reloads only Nginx. The initial installation used this relative
symlink so it resolves inside the container mount (superseded by the Equipment
update above):

`/opt/nightcap/deploy/production/data/public/wiki/current` →
`releases/20261009-wiki-v2`.

Receipts, manifests and config preimages are outside the public tree:
`/opt/nightcap/deploy/production/website-history/20261009-wiki-v2/`.
Final Nginx SHA256:
`03ef62717aad29884d3c1a60d800b19d0ee9cc7024fec7313d0263f37fbd046c`.

The installer activated, verified all 461 files, restored the original config,
proved wiki 404 and private downloads unchanged, then reactivated and verified
again. Both game/runtime services and all other container IDs/start times remained.
The first attempt (`20261009-wiki-v1`) failed because the traversal test required
404 instead of permitting Nginx's 400; automatic rollback restored exact original
config and hashes. A regression now allows 400 only for that malformed path.

For initial-release rollback, take the shared deployment lock and require the
current config to match the recorded final hash. Write `nginx.before.conf` bytes
back **in place**, run `nginx -t`, then gracefully reload and confirm wiki 404 plus
unchanged play resources/services. Remove `current` only after checking it points
to this release; preserve release/receipt files for diagnosis. If any other website
operation changed the config, do not overwrite it with an old preimage: prepare a
scoped inverse that removes only the wiki host. After Cloudflare activation, also
remove only the new wiki route/DNS; no IP-rule change was made.

For content updates, `wiki/update.py` reuses archive validation and origin probes.
Run the Linux deployment/update tests first, then as root invoke:

```sh
python3 update.py NEW.tar.gz NEW.tar.json NEW_RELEASE EXPECTED_PREVIOUS_RELEASE EXPECTED_CONFIG_SHA256
```

It holds the same `website-history/.lock`, checks exact Nginx bytes and the relative
current pointer, verifies the previous release and private/service baseline, then
stages an immutable release. It atomically replaces only `wiki/current`, verifies
every new file, rehearses the previous pointer, and reapplies the new release.
Nginx, DNS/WAF and game services are untouched. Any failed activation restores the
owned pointer; concurrent config is preserved and reported for attention. An
unrelated concurrent pointer is never overwritten. Receipts include the previous
target and exact manifests for recovery. Do not rerun the initial installer.

For manual content rollback, hold the shared lock, require the expected current
pointer/config, validate the previous immutable release, and atomically replace
the pointer with that previous relative target. Re-run its manifest, private-route,
private-download and service checks. Keep all release and receipt directories.

## Verification evidence

- Nine complete-site/content/package tests pass across all 457 HTML pages.
- Five source-refresh tests cover committed, staged, unstaged and untracked changes.
- Seven Node Equipment cases cover all 384 exact variant names, combined
  filters, sorting, pagination, level/slot semantics and unsafe-looking queries.
- Eight content-update tests pass on Linux, including failed activation,
  stale preimage, corrupt archive, unrelated pointer ownership, private-download
  drift, config drift and interruption immediately after atomic replacement.
- Eight deployment tests pass on Linux, including symlink cleanup when recovery
  reload fails, stale config rejection, archive traversal/symlink rejection, total
  memory bound and private-route denial.
- Six Node search cases pass: command relevance, exact item, multiple words,
  unsafe text, blank query and index-load failure.
- Browser: item search and quality links, Enter submission, command ranking,
  no-results/unsafe text, clean warning/error log and 20 overflow/title checks
  across five page types at 320/768/1024/1440 widths. Desktop and 390px layout were
  visually inspected. Articles and navigation are server-rendered static markup;
  search includes a no-JavaScript index alternative.
- Independent hosting review found lock, rollback and aggregate-memory issues;
  all were fixed. Second review found no remaining material contract violation.
- Local working evidence: `E:/EQ_Local_Dev/artifacts/nightcap-wiki/`.

No gameplay, client, database or original player-guide content was changed.
