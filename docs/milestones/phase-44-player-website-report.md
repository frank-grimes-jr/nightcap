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
