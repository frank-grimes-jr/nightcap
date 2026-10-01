# Phase 44 — OVH player guide

October 1, 2026. The owner requested a green/cream player guide using existing
loading art, with Nightcap-only public text and hosting on the existing OVH server.

Built: 21 grouped feature entries, six workbench areas, recent changes and FAQ;
native accessible disclosures and anchors; two original artworks; static-only
packaging and branding guard; isolated public virtual host; drift-aware serialized
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

Deployed: release `20261001-player-guide-v3` at https://play.nightcapgame.org/ for
approved player IPs. No game restart, data mutation or gameplay promotion.

Remaining: apex/www public routing needs authenticated Cloudflare access. The
available dashboard is at sign-in, and root/www had no address records. Public
reachability from a non-approved network is not claimed. Original PNGs make the
payload about 5.3 MB; no artwork was altered. Gameplay acceptance remains as
recorded in the individual release guides.

Runbook, content sources, exact checks and recovery: [player website](../ops/player-website.md).
