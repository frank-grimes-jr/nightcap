# Phase 61 — Official Nightcap wiki

Date: October 9, 2026.

## Built

An official green/cream wiki with article contents, category navigation, local
full-text search, command ranking, review dates, status labels and responsive/print
layouts. Seventeen guides cover current custom systems. The released catalog adds
48 zones and 384 item variants with stat tables, source zones and quality links.
The output is 454 HTML pages and an exact 461-file static release.

OVH origin release `20261009-wiki-v2` is installed and byte-verified. Separate host
root, shared publisher lock, strict CSP, read-only routes, archive/hash checks,
rollback rehearsal and five-service/private-download preservation are verified.
Public HTTPS is live at https://wiki.nightcapgame.org/ through the existing tunnel.
All 461 files pass external byte/header checks; private wiki paths return 404 and
unapproved play access remains 403. Live search and mobile/desktop browser checks
pass. The existing player-only WAF policy was preserved without modification.
Local tests, browser checks and independent hosting review are recorded in
[the runbook](../ops/nightcap-wiki.md).

## Cut

Player accounts and editing were explicitly declined. No MediaWiki backend,
database, third-party analytics, bulk import from other wikis or game-server API.
The catalog does not claim every ordinary item, NPC, map or quest.

## Shaky / remaining

Later content updates need the documented guarded pointer-update mode. In-game
acceptance and balance gates remain with their original gameplay releases.
