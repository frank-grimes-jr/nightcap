# Nightcap player website on OVH

Updated October 1, 2026. The owner requested the green/cream player guide on OVH,
using repository loading artwork and Nightcap-only public branding.

## Current publication

- **Hosted:** https://play.nightcapgame.org/ under its existing approved-IP access.
- **Intended public domain:** https://nightcapgame.org/ and www. The separate OVH
  virtual host is prepared and origin-tested. DNS/tunnel routing still needs an
  authenticated Cloudflare session. The available dashboard is at sign-in.
- No apex/www address records were present at inspection. Do not call the apex
  live until public HTTPS and a non-approved network verify it.
- Active release: `20261001-player-guide-v3`, selected by
  `/opt/nightcap/deploy/production/data/public/player-site/current`.
- All five container identities/start times, both patch channels, existing player
  guide and friend ZIP are preserved. No game restart or database mutation.

## Current content contract and source ledger

`index.html` plus `site-assets/` is an exact five-file payload: local CSS, favicon
and two unmodified loading-screen PNGs. Native anchors and details work without
JavaScript, external fonts, cookies, forms or analytics. Brand checks cover public
text, metadata, attributes and static code. Both images were inspected visually.

Twenty-one feature entries cover the older conveniences and recent deployments.
Six workbench entries separate undeployed candidates, planned content and open
verification. Deployed means installed for live testing, not manual acceptance.

| Area | Evidence to check before updating |
|---|---|
| Current deployments | `docs/status.md`, latest `CHANGES.md` |
| Spell inspection / startup | `docs/releases/spell-inspection-20261001.md`, `launcher-play-20261001/` |
| Hub, provisions, travel, market | `docs/releases/tunnel-services-starters/`, `tunnel-travel-alcove/`, `tunnel-class-courts/` |
| Loot | `docs/releases/advanced-loot/PRODUCTION.md` and `LIVE-QA.md` |
| Pets and models | `docs/releases/pet-management-20260922/`, `enchanter-animation-pet-commands-20260930/`, `classic-models-20260930/` |
| Buffs, casting, pet armor | `docs/releases/client-gameplay-20260919.md`, retained by later production builds |
| Older conveniences | July 15–16 changelog plus October 1 hosted checks below |
| Combat/item candidate | `docs/releases/combat-item-fixes-20260922/README.md` |
| Ability curation | `docs/balance/native-aa-release-candidates.md` — candidates, not a live whitelist |
| Journal candidate | `E:/EQ_Local_Dev/_worktrees/adventure-journal-epic05/docs/adventure-journal/SPEC.md`, accepted October 1; not deployed |

Read-only hosted checks confirmed no-corpse rules, death-item-loss level 999,
merchant buy multiplier 2.5, ability-experience minimum 1, right-click scribing,
seven Keeper spawns, both tunnel blessing NPCs and 72 waypoints. The zone image
contains the three documented player commands. Both blessing quest hashes match
source. The installed Keeper script was read and matches the documented flow;
its raw hash differs from the Windows checkout. No player records were exported.

Artwork comes unchanged from local repository loading screens dated 2026-09-20:
`01-traders-at-dusk.png` and `10-gnome-master-of-three.png`. The hero is eager and
the lower image is lazy loaded. Total payload is approximately 5.3 MB.

## Current verification and deployment

```powershell
node tools/tests/test_player_site.cjs
python -B -m unittest discover -s tools/tests -p test_player_site_package.py
python -B tools/player_site_package.py ABSOLUTE_NEW_PACKAGE_PATH.tar.gz
```

Provide `PLAYWRIGHT_MODULE`, `BROWSER_EXECUTABLE` and `SCREENSHOT_DIR` when needed.
Set `SITE_URL` to test HTTPS. The suite passes locally and on the play hostname:
strict CSP, no scripts, branding, all anchors, keyboard disclosures, history,
deep links, 320/390/768/1024/1440 widths, 200% text, images and clean console/network.
Package tests cover private-file exclusion, forbidden hidden metadata, immutable
releases, manifest bytes and rejection of stale website pointers. Independent
content/deployment review findings were fixed before final activation.

Upload only the generated tar/JSON manifest, reviewed Nginx config and
`deploy/production/player-site-deploy.py` outside the public mount. Run on OVH:

```text
sudo python3 player-site-deploy.py stage PACKAGE MANIFEST YYYYMMDD-NAME EXPECTED_NGINX_SHA CONFIG
sudo python3 player-site-deploy.py activate YYYYMMDD-NAME
sudo python3 player-site-deploy.py rollback YYYYMMDD-NAME
```

The helper uses a host lock and checks the current pointer, config, services,
protected downloads and staged bytes. Private receipts/config preimages stay in
`/opt/nightcap/deploy/production/website-history/`. Stage rehearses the actual
origin plus rollback before activation. Keep the helper with its receipt for
recovery. The bind-mounted Nginx config must be written in place to preserve its
inode; validate with `nginx -t` before a graceful web-only reload.

Apex/www serve only the isolated website root. Origin probes prove patch channels,
downloads, setup guide, gateway and private history return 404; dotfiles return
403, and unknown hostnames 404. Existing play downloads are fetched and hashed,
and all five service IDs/start times remain unchanged. No game access rule changes.

Cloudflare initially injected an analytics script. Website-only
`Cache-Control: public, no-cache, no-transform` suppresses it while retaining the
strict CSP. Include `/index.html` in the cache map: `try_files` changes the URI.
[Documented edge behavior](https://developers.cloudflare.com/web-analytics/faq/).

## Remaining root-domain setup

Sign in to Cloudflare and inspect current tunnel/WAF rules. Add apex/www routes
to the existing tunnel using `http://web:8080`, retaining the incoming Host.
Preserve play `/connect` to the gateway, remaining play paths to web and the final
catch-all. Create proxied DNS records for the same tunnel. Keep play's allow/deny
protections; scope any zone-wide IP restriction to play instead of disabling it.

Verify apex/www HTTPS, all five file hashes, script-free HTML, browser suite,
public access from a non-approved network and denial of private paths. Recheck
that a non-approved network still gets 403 on play. Root-domain publication is
not complete merely because origin checks passed.

References: [tunnel DNS](https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/routing-to-tunnel/dns/),
[Nginx host matching](https://nginx.org/en/docs/http/server_names.html).

October 1 evidence: `E:/EQ_Local_Dev/artifacts/player-website-20261001/`.
Forward/rollback and final activation passed for v3. The full play-host HTTPS
suite passed. The OVH-source play request returned 403, preserving restricted
access. Apex/www routing remains pending authentication.

---

# Historical September 15 GitHub Pages attempt

The owner explicitly authorized updating the HTML/documentation and public
GitHub Pages publication on September 15, 2026. The earlier automatic-review
block is superseded by that specific approval.

## Content contract

`index.html` is a self-contained player guide: Home, Features, Major Changes and
FAQ tabs. No framework build, external fonts, tracking scripts, account form or
client download is required. Copy follows deployed behavior and clearly labels
live testing and unfinished features. Current internal status belongs in
[status.md](../status.md); technical deployment details stay off the player page.

## Publication

Public destination: https://frank-grimes-jr.github.io/nightcap/.
Publish only reviewed `index.html` and `.nojekyll` on the dedicated `gh-pages`
branch. Configure Pages to that branch, root directory. This payload excludes
server sources, database backups and local artifacts and does not promote gameplay
to main. Keep the canonical HTML in the normal feature/dev/test history.

For an update: review actual gameplay statements, run browser checks, copy the
exact HTML bytes to the Pages branch, commit/push, wait for a successful build,
then fetch the public URL and compare its SHA256 to the source. Verify all four
tabs, keyboard navigation, FAQ disclosure and small-screen layout publicly.
A pushed branch alone is not proof of a successful deployment.

## Verification and rollback

Browser checks cover tab selection, arrow/Home/End keys, direct fragment links,
browser history, FAQ disclosure, no-JavaScript readability and narrow viewports.
Publication evidence is recorded below; GitHub rejected site activation.
Rollback by restoring the last verified static commit on `gh-pages` with a new
commit, then repeat the public hash/browser checks. Gameplay deployment and QA
remain independent of this site.

## September 15 publication result

- Source implementation: `9f6f48b`; reviewed PR #50 merged to dev and test at
  `2d95329`. Main gameplay was not promoted.
- Static branch: `gh-pages`, commit `e6efdf1`; exactly `index.html` and `.nojekyll`.
- Local browser suite and desktop/mobile visual inspection passed.
- POST `/repos/frank-grimes-jr/nightcap/pages` returned HTTP 422:
  `Your current plan does not support GitHub Pages for this repository.`
- The repository is private. Follow-up Pages GET still returns 404. The proposed
  public URL is **not live**; no public hash/browser verification is claimed.
- Issue #23 remains open. Hosting requires a supported GitHub plan or an
  owner-selected alternate destination, such as a public website-only repository.
  Publication authorization is present; the remaining blocker is GitHub plan support.

Run the browser suite from the repository root with Node:

```powershell
node tools/tests/test_player_site.cjs
```

Install/provide Playwright through `PLAYWRIGHT_MODULE` if it is outside normal
Node resolution; `BROWSER_EXECUTABLE` selects an installed Chromium browser.
`SCREENSHOT_DIR` saves visual evidence. Set `SITE_URL` to test the deployed URL
once hosting succeeds. No server restart is needed for website updates.
