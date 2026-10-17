# Nightcap player website on OVH

Updated October 17, 2026. The owner requested the green/cream player guide on OVH,
using repository loading artwork and Nightcap-only player-facing branding. The owner explicitly requires private access.

## Current publication

- **Hosted:** https://play.nightcapgame.org/ under its existing private access policy.
- **Private by owner instruction:** retain the existing private website access boundary.
  No public apex/www site, new DNS route or Cloudflare sign-in is needed.
- Apex/www and unknown Host headers return 404 at the origin. The unused public
  virtual host was removed before closing this task. No DNS/WAF rules changed.
- Active release: `20261017-progression-combat`, selected by
  `/opt/nightcap/deploy/production/data/public/player-site/current`.
- The website operation preserves all five container identities/start times,
  both patch channels, the existing setup guide and friend ZIP. It does not
  restart the game or mutate the database; gameplay deployment is recorded separately.

## October 17 publication

Updated the exact five-file private payload after paired gameplay activation.
The guide covers Recommended abilities, 10% passive AA, independent Monk attacks,
normal death EXP protection, minimum-100 stacks, 3/4/4 reforging and Commonlands
services. All five public hashes, existing route protections and service identities
verify; stage rehearsed rollback. Ten Linux deployment tests and real Chrome
responsive/keyboard/CSP checks pass. Previous 20261009-zone-hunt remains retained.
Current evidence: `docs/releases/october-17-2026/`. Older access/feature descriptions
below are dated history; native game access uses personal codes.

## Current content contract and source ledger

`index.html` plus `site-assets/` is an exact five-file payload: local CSS, favicon
and two unmodified loading-screen PNGs. Native anchors and details work without
JavaScript, external fonts, cookies, forms or analytics. Brand checks cover public
text, metadata, attributes and static code. Both images were inspected visually.

Seventy-three feature/control entries appear in eight custom-system sections.
Loot and pet systems come first, with direct links to the custom loot window,
multiple pets, custom pet window and Pet Armor tab. A separate quest
section covers Ascension and Waypoint Explorer, with starting points, requirements
and rewards. Eight built journal quests are listed in their own unreleased panel.
The guide retains plain language, larger detail text and material warnings.
Installed means available for live testing, not manual acceptance.
Current additions: [zone-hunt production evidence](../releases/zone-loot-20261009/PRODUCTION.md). The [October 4 content ledger](player-guide-content-20261004.md) retains the prior 70-entry scope.

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
releases, manifest bytes, rejection of stale website pointers, denied alternative
hostnames and private cache directives. Independent
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

Only play serves the guide. Origin probes require 404 for apex, www and unknown
hosts across the website, assets, patch channels, downloads, setup guide, gateway,
dotfiles and private history. Existing play downloads are fetched and hashed, and
all five service IDs/start times remain unchanged. The existing Cloudflare IP
allowlist remains the access boundary; no game or website access rules changed.

Website-only `Cache-Control: private, no-store, no-transform` prevents shared
caching and edge analytics injection while retaining strict CSP. Include
`/index.html` in the cache map: `try_files` changes the URI. Signed release caching
is unchanged. [Documented edge behavior](https://developers.cloudflare.com/web-analytics/faq/).

## October 9 zone hunt update

Release `20261009-zone-hunt` adds three feature entries and a 48-row zone reward
table after successful server activation. It documents independent 0.5% family
rolls, 60/30/8/2 qualities, six armor locations, level-50 cap relief up to 280,
zero resale and free three-identical-copy forging. Eight access-check zones and
city/hub reserves remain separate. The prior live five-file payload was verified
before editing; all other player guidance and artwork remain.

Ten Linux package/deployment tests and local/live HTTPS browser suites pass, including
73 entries, 48 reward rows, private headers, exact bytes, five widths, 200% text,
keyboard/history, and clean console/network. Origin staging rehearsed activation
and rollback. Final activation retained all service IDs/start times, protected
downloads and existing private routing. The previous `20261004-player-guide-latest`
release and private receipt are retained for rollback. Initial staging restored
the old guide after detecting a restrictive-umask directory bug; the repaired
publisher passed its new Linux regression and the repeated rehearsal. Public
payload directories are 0755; private history stays 0700. No DNS/WAF changes.

## Historical October 4 latest gameplay update

Release `20261004-player-guide-latest` reconciles current main b1110e8: passive
ability XP and binary focus, universal trading/fixed resale, and the complete
loading gallery. The 70-entry guide preserves its separate quest lists and
private-only route. Browser checks assert the new behaviors and reject stale
partial-allocation guidance. The package remains exactly five files.

Deployed `20261004-player-guide-latest`; previous `20261004-player-guide-systems`
is retained for rollback. Local and live HTTPS browser checks pass, including
70 entries, two installed/eight unreleased quests, current trading/XP guidance,
featured links, exact five-file bytes, private headers, five viewport widths,
200% text, keyboard/history, branding and clean console/network. Origin staging,
rollback and final activation passed. Protected download hashes and all five
service IDs/start times were preserved. Unapproved play access remains HTTP 403.
No gameplay, database, DNS/WAF or public-routing changes occurred.
The matching receipt and recovery helper are retained at
`/opt/nightcap/deploy/production/website-history/20261004-player-guide-latest/`.
Local evidence is under `E:/EQ_Local_Dev/artifacts/player-website-20261004/`:
`latest-https-screenshots/`, `latest-verification.json`, and the reviewed
`shareable-changes.txt` (54 bullets, checked for prohibited branding).

## Historical October 4 systems coverage update

Release `20261004-player-guide-systems` expands the previous list release's
compressed descriptions. Only HTML and CSS payloads change; the five-file package,
private host routing and loading images remain. Local browser checks pass for the
system shortcuts, 67 entries, two installed quest lines and eight unreleased quests.
Independent content review and desktop/mobile inspection are complete.

Deployed as `20261004-player-guide-systems`; prior release
`20261004-player-guide-lists` is retained for rollback. The full HTTPS browser
suite passes, including featured links, exact five-file bytes, private cache
headers, 67 entries, two installed/eight unreleased quests, five viewport widths,
200% text, keyboard/history, branding and clean console/network. Nine package/
deployment tests pass. Origin activation and rollback passed with protected
downloads preserved and all five service identities/start times unchanged.
An unapproved source still receives 403. No game restart, database mutation,
DNS/WAF change or public route. Matching receipt and recovery helper are under
`/opt/nightcap/deploy/production/website-history/20261004-player-guide-systems/`.
Evidence: `E:/EQ_Local_Dev/artifacts/player-website-20261004/expanded-https-screenshots/`
and `systems-verification.json` in the same artifact root.

## Historical October 4 initial list update

Release `20261004-player-guide-lists` replaces `20261001-player-guide-friendly`.
Only HTML and CSS payload bytes change. The deployment retains the same private
Nginx configuration and exact five-file package. Local and live HTTPS browser
suites pass for all 43 changes, two installed quests and eight unreleased quests,
including five widths, 200% text, keyboard/history/deep links, image loading,
branding, strict CSP, exact payload bytes and private cache headers. Nine package/
deployment tests pass. Desktop/mobile rendering and independent content review pass.

OVH staging exercised activation and rollback, then final activation verified all
five files, protected downloads, alternative-host/storage-route denial and unchanged
IDs/start times for all five containers. An unapproved OVH-source request still
returns HTTP 403. No DNS/WAF, database or gameplay changes occurred.
Receipt, configuration preimages and matching rollback helper:
`/opt/nightcap/deploy/production/website-history/20261004-player-guide-lists/`.
Local evidence: `E:/EQ_Local_Dev/artifacts/player-website-20261004/`.
The previous private release remains available for rollback.

## Historical October 1 access verification and recovery

October 1 evidence: `E:/EQ_Local_Dev/artifacts/player-website-20261001/`.
Forward/rollback and final activation passed for `20261001-player-guide-friendly`.
The full HTTPS browser suite passed from the approved connection, including all
five exact payload bytes and private cache headers. Readability review confirmed
all 21 features and six workbench entries, with material warnings preserved. The OVH-source play request
returned 403; apex/www/unknown-host origin probes returned 404. The guide is
complete at the restricted play address. Public root-domain setup was cancelled
by the owner's explicit private-only instruction.

Receipts and the matching deployment helper are saved outside the served tree at
`/opt/nightcap/deploy/production/website-history/20261001-player-guide-friendly/`.
This release changes HTML and CSS only. Its previous release is
`20261001-player-guide-private`; both use the same private-only Nginx configuration,
so the recorded rollback preserves access restrictions. Do not add public routes
or loosen the player IP restriction without owner approval.

---

# Historical September 15 GitHub Pages attempt

Superseded by the October 1 private-only OVH decision above. Do not follow these
historical publication instructions for current updates.

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
