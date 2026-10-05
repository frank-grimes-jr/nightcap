# Phase 44 — OVH player guide

October 1, 2026. The owner requested a green/cream player guide using existing
loading art, with Nightcap-only public text and hosting on the existing OVH server.

Built: 21 grouped feature entries, six workbench areas, recent changes and FAQ;
native accessible disclosures and anchors; two original artworks; static-only
packaging and branding guard; private-only hostname routing; drift-aware serialized
deployment with private receipts and rehearsed rollback. Existing play-host access,
game services, signed channels, setup guide and ZIP are retained.

Verification: local and HTTPS browser suites pass at five viewport widths, with
keyboard/history/deep links, 200% text, strict CSP, no JavaScript, images and clean
console/network. Package/security tests pass. Nginx syntax, all website hashes,
protected-route denial, existing artifact hashes and unchanged container identity/
start-time checks pass. Forward/rollback was actually rehearsed on OVH. Independent
review led to fuller older-feature coverage, precise candidate labels and a
stale-pointer guard. The edge-injected analytics script was eliminated using the
website-only no-transform header, including the rewritten index URI.

Deployed: release `20261001-player-guide-friendly` at https://play.nightcapgame.org/ for
approved player IPs. No game restart, data mutation or gameplay promotion.

Private access: the owner explicitly declined public hosting. The unused apex/www
virtual host was removed, alternative hostnames return 404, an unapproved network
receives 403 on play, and approved HTTPS/browser checks pass. Website responses
disable shared caching and storage. No DNS/WAF changes or dashboard sign-in are
needed. The requested website is complete.

Readability follow-up: conversational feature descriptions, “Ready to try” labels,
commands and choices in lists, larger detail text and stronger contrast. Review
confirmed full feature coverage and preserved warnings. Local and hosted browser
checks pass; the prior private release is available for rollback.

Limits: original PNGs make the payload about 5.3 MB; no artwork was altered.
Gameplay acceptance remains as recorded in the individual release guides.

Runbook, content sources, exact checks and recovery: [player website](../ops/player-website.md).

## October 4 — visible changes and separate quests

Built: 43 visible changes in six topic groups; separate Ascension and Waypoint
Explorer entries; all eight unreleased journal quests with levels and objectives.
Updated older tunnel/loot descriptions, recent client repairs, and gear/stat
customizations. Read-only hosted checks confirm quest installation and current
rule values. Independent review found the older health/gear/stat omissions, now
included. Existing loading artwork, theme and private access are retained.

Limits: installed gameplay still needs the acceptance checks in its release
records. Journal quests remain built but not installed; the helmet has no reward
source. The website does not release any gameplay changes.

Deployed: `20261004-player-guide-lists`. Final local and HTTPS browser checks,
nine package/deployment tests, origin activation/rollback, exact file hashes,
protected downloads and unchanged service identities all pass. Unapproved access
remains 403. Review and desktop/mobile inspection completed. Recovery retains the
prior private release and a matching helper beside the new private receipt.

## October 4 — custom systems coverage follow-up

The first list compressed major systems too far. Expanded to eight named sections
with 67 feature/control entries and prominent custom loot, multiple pets, custom
pet window and armor shortcuts. Added the missing control, persistence and caster
interface details; preserved quest separation, content status and private access.
Independent source review and desktop/mobile checks pass. No gameplay changes.

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

## October 4 — latest gameplay and shareable text

Refresh the guide for the deployed passive-AA, free-trade/resale and loading-gallery
releases. Correct stale command, consent and sell-all instructions, preserving
important restrictions and warnings. The user also requested a complete shareable
bullet summary in chat; its prepared text is checked against the same source ledger.

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
