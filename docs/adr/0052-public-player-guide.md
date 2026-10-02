# 0052 — A static player guide on the existing OVH host

Date: October 1, 2026. Accepted intent: the owner requested a racing-green and
cream player guide using the repository's loading art and Nightcap-only branding,
hosted on the existing OVH server/domain. The owner explicitly clarified that
the guide must stay private.

Retain canonical `index.html`, with local CSS, a favicon, and two unmodified
loading-screen PNGs. Native anchor navigation and details disclosures work without
JavaScript, a framework build, cookies, external fonts, analytics, or an account
service. The existing strict web Content Security Policy remains intact.

Publish an exact five-file allowlist into a versioned website directory. A symlink
selects the release. Only the existing approved-player-IP play hostname serves
the guide and its assets. Existing signed patches and gateway routing remain.
Apex, www and unknown Host headers fail closed with 404; no public DNS/tunnel
routes are added. The existing Cloudflare IP allowlist remains enforced. Website
responses use private, no-store, no-transform cache directives.

Content differentiates deployed-for-testing from undeployed candidates and open
verification. Source history alone is insufficient evidence of live behavior.
The content ledger and publication evidence live in `docs/ops/player-website.md`.
Brand checks cover all public text, attributes and static code; the two images
are visually inspected. Website publication does not promote gameplay to main.

GitHub Pages is unavailable on the private repository's current plan. A second
hosting service would ignore the selected OVH destination. A framework and client
data fetch would add complexity to a static guide with no account workflow.

Deployment captures the previous web config and current pointer outside the
public directory, rehearses forward/rollback, validates Nginx before graceful
reload, checks file hashes and restricted-route isolation, and verifies all five
service IDs/start times remain unchanged. No database writes or game restarts.
