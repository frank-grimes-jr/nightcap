# Phase 61 — Official Nightcap wiki

Date: October 9, 2026.

## Built

An official green/cream wiki with article contents, category navigation, local
full-text search, command ranking, review dates, status labels and responsive/print
layouts. Seventeen guides cover current custom systems. The released catalog adds
48 zones and 384 item variants with stat tables, source zones and quality links.
The output is 454 HTML pages and an exact 461-file static release.

Initial OVH origin release `20261009-wiki-v2` was installed and byte-verified. Separate host
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

The guarded content-update command is now implemented and covered by Linux
rollback tests. Content remains limited to the documented custom reward catalog. In-game
acceptance and balance gates remain with their original gameplay releases.

## Equipment organization follow-up

Replaced the flat Equipment category with a focused catalog: 96 families, four
quality links per family, gear/augment tabs, slot/level/zone/name filters, sorting
and 12-family pagination. Guide links are separate and visible before browsing.
Seven site tests, seven catalog cases (including all 384 exact variant names),
six existing search cases and sixteen Linux deployment/update cases pass.
Browser checks cover combined filters, empty/reset states, pagination, quality
links, Back restoration, mobile cards and 320/768/1024/1440 widths. Independent
review found two rollback edges and one exact-name search issue; all were fixed
and covered by regressions. Release `20261010-equipment-v1` is live; all 461
public file hashes and headers pass. Rollback was rehearsed, private downloads
and five service identities were preserved, and no Nginx reload was needed.
Public rollout evidence is in the hosting runbook.

## Features and maintenance follow-up — October 16

Published 17 grouped Features, dedicated upgrades/crafting guides, and a full
content reconciliation through the October 16 release evidence. Generated reward
instructions now agree with higher-tier four-copy costs. Nine site, five Git
refresh, thirteen browser-script and sixteen Linux publication tests pass; browser
layouts/navigation and all 464 public hashes pass. The owner’s per-change wiki
maintenance requirement is in repository instructions and the installed skill.
No gameplay was changed; existing owner acceptance gates remain. Full scope and
proof: [release record](../releases/wiki-features-20261016/README.md).
