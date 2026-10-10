# Official Nightcap wiki — hosting and maintenance

Updated October 9, 2026.

## Current state

- **Public URL: https://wiki.nightcapgame.org/** — live and verified October 9, 2026 (EDT).
- **OVH origin installed and verified:** `20261009-wiki-v2`.
- **Public hostname active:** the existing tunnel now routes the wiki to
  `http://web:8080`; its proxied CNAME was created automatically. The existing
  player-only WAF rule required no change.
- Local preview: `http://127.0.0.1:8767/` while its development server runs.
- 451 articles: 17 maintained guides, 48 enabled zone pages, 384 item pages and
  two catalog indexes. All articles, Search and 404 bring the build to 454 pages.
- The exact publication contains 461 files. Private player guide and game access
  remain on `play.nightcapgame.org` under the existing approved-IP policy.

Source and build commands: [wiki/README.md](../../wiki/README.md).
Architecture: [ADR 0059](../adr/0059-official-public-wiki.md).

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
place, and reloads only Nginx. The active symlink is relative so it resolves inside
the container mount:

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

- Six complete-site/content/package tests pass across all 454 HTML pages.
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
