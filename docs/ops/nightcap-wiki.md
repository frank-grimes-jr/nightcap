# Official Nightcap wiki — hosting and maintenance

Updated October 9, 2026.

## Current state

- Intended public URL: `https://wiki.nightcapgame.org/`.
- **OVH origin installed and verified:** `20261009-wiki-v2`.
- **Public hostname pending:** Cloudflare was signed out in the available browser;
  no DNS/tunnel/WAF changes have been made and public HTTPS is not claimed live.
- Local preview: `http://127.0.0.1:8767/` while its development server runs.
- 451 articles: 17 maintained guides, 48 enabled zone pages, 384 item pages and
  two catalog indexes. All articles, Search and 404 bring the build to 454 pages.
- The exact publication contains 461 files. Private player guide and game access
  remain on `play.nightcapgame.org` under the existing approved-IP policy.

Source and build commands: [wiki/README.md](../../wiki/README.md).
Architecture: [ADR 0059](../adr/0059-official-public-wiki.md).

## Finish the public hostname

Using the authenticated Cloudflare account for `nightcapgame.org`:

1. Inspect existing DNS, tunnel configuration and custom security rules first.
2. In the existing `nightcap-production` tunnel, add a published application route
   for `wiki.nightcapgame.org`, all paths, service **HTTP `web:8080`**. Preserve the
   existing play `/connect` gateway route, other play routes and final 404 catch-all.
   Do not override the origin Host header to the play hostname.
3. Confirm a proxied DNS record for `wiki` targets that same tunnel. Let the tunnel
   workflow create it when supported; do not create a direct public OVH A record.
4. If a zone-wide approved-IP block includes the new hostname, amend only its scope
   to exclude the exact wiki hostname. Preserve its existing IP expression and all
   play/other-host restrictions. Do not disable WAF, add a broad skip rule, change
   the gateway allowlist, or make downloads public.
5. From an unapproved external source, verify the wiki and representative deep
   links return 200 with the exact release bytes, CSP and no-transform cache policy.
   Verify `/channel.json`, `/launcher-channel.json`, `/nightcap-friends.zip`,
   `/guide.html`, `/connect`, `/player-site/current/index.html` and dotfiles are 404
   on wiki. `/../channel.json` may be 400 because Nginx rejects the malformed URI.
6. Confirm an unapproved source still receives 403 from the play hostname. Re-run
   the browser search, navigation and mobile checks at the public URL. Record the
   actual Cloudflare changes and final HTTPS verification here before declaring live.

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
remove only the new wiki route/DNS and reverse only its scoped IP-rule exception.

For later content updates, prepare a fresh immutable package/release and compare
the active pointer/config under the same shared lock. Reuse archive/hash validation,
switch `current` atomically to a relative release path, and verify all bytes plus
private-route denial. Preserve the previous target for pointer rollback. Extend
the installer with a tested update mode before automating this; do not rerun the
initial installer or manually merge old play-only configs over the wiki host.

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
