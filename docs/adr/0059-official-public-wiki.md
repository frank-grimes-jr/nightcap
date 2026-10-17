# 0059 — Official public Nightcap wiki

Date: 2026-10-09. Accepted intent: an official guide maintained by the owner and
assistant, inspired by the article/navigation pattern of Project 1999's wiki.

## Decision

Generate static HTML in `wiki/` from reviewed guide articles and a public catalog
projection. Provide full-text browser search, stable article links, contents,
categories, recent changes, zone/item cross-links, review dates and release labels.
Use the current green/cream Nightcap identity and unchanged approved artwork.

Use `wiki.nightcapgame.org` as the public target with an isolated Nginx root on
existing OVH. Retain `play.nightcapgame.org` and its approved-IP game/download
policy. Share the existing website deployment lock. Keep all wiki routes read-only,
allow only known static file shapes, retain CSP, and test private-route denial.

## Alternatives

- MediaWiki: supports player accounts and editing, but those are explicitly not
  requested. A database/PHP application would introduce unnecessary maintenance.
- Public wiki below the private play hostname: conflicts with its existing IP
  policy and couples public reading to game/launcher access.
- Separate managed hosting: viable but ignores the requested existing domain/host
  when OVH can serve the small static payload without a game restart.

## Boundaries and proof

Only the generated `dist/` manifest is published, never the repository, source
ledger, raw exports or operational artifacts. The initial scope is 17 guide pages,
48 enabled reward zones and 384 obtainable item variants, plus directories/search.
The 64 reserved variants and unreleased quest rewards are not offered as live loot.
40% passive AA follows the latest deployment record, not the compiled 1% fallback.

Automated local-link, content, package, search and deployment failure checks accompany
real browser inspection. The origin installation verifies every served file and
preserves all five container identities/start times and private download hashes.
Public completion additionally requires Cloudflare DNS/tunnel routing, a wiki-only
exception from any zone-wide approved-IP block, and external HTTPS verification.
Wiki publication does not promote gameplay or sign off in-game QA.
