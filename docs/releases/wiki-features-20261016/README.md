# Features and whole-wiki refresh — October 16, 2026

Published https://wiki.nightcapgame.org/features.html as `20261016-features-v1`.
Source implementation: `1048a5c`. Previous release: `20261010-equipment-v1`.

## Player result

Features is in primary navigation and on the home page, with 17 major departures
from Classic grouped by character, rewards, adventuring and tools. New Item
upgrades and Tradeskills/Craft All guides give actionable instructions. The
refresh reconciles 20% passive AA / 4,000 XP per point, allowed ranks at level 1,
early scribing, equipment/race rules, disabled LORE, three/four-copy upgrades,
temporary AA/song-window effects, healing targets, food/drink, current tunnel
services, travel/waypoint caveats, and deployed versus candidate boundaries.
All 432 generated item/zone pages use the current upgrade costs. The 384 item
definitions and 48-zone projection are unchanged.

## Verification and preservation

- Nine complete-site tests pass across 457 HTML pages: links, anchors, navigation,
  mechanics, catalog reachability, exact immutable package and private exclusions.
- Five real-Git refresh tests pass, including a staged edit canceled only in the
  working copy, new/deleted files and untracked source. Six search and seven
  Equipment cases pass, including all 384 exact variant names.
- Sixteen deployment/update tests pass on Linux. The actual atomic switch
  rehearsed the previous release and reapplied the new one. No Nginx reload,
  service restart, gameplay/database write, DNS or access-policy change.
- Browser keyboard navigation, 12 page/width checks (320/768/1024/1440), phone and
  desktop visual checks pass with no horizontal overflow or warning/error logs.
  The live Features page has 17 entries and an October 16 review date.
- Independent content/maintenance review findings were fixed; bounded recheck
  found no remaining material findings. Initial local test failures exposed test
  selectors and command-search precedence; both were corrected. Windows sandbox
  temporary-directory restrictions required running tests outside the sandbox.
- Public HTTPS at 14:44:03 UTC matched all 464 release hashes, TLS and security/cache
  headers. Ten private/source paths return 404; POST returns 403. Current public
  play-route statuses/success hashes, private origin downloads and all five service
  identities/start times are preserved. The preflight used current credential-era
  access behavior, not the superseded October 9 IP-only assumptions.

Receipts: [origin](origin-verification.json), [public](public-verification.json).
Retained package, screenshot and verifier are in the task's
`E:/EQ_Local_Dev/artifacts/nightcap-wiki/features-20261016/` evidence directory.
Production receipt: `/opt/nightcap/deploy/production/website-history/20261016-features-v1/`.
Recovery: [wiki runbook](../../ops/nightcap-wiki.md); validate current configuration,
hold the shared lock and restore the previous immutable relative pointer. Preserve
later content updates and current access policy; do not rerun the initial installer.

## Required ongoing maintenance

Every Nightcap change now requires a whole-wiki impact review and updates to all
affected guides, Features, commands, generated catalog pages and Recent changes.
No-impact decisions are recorded rather than generating cosmetic edits. Repository
AGENTS, wiki/README and the installed Nightcap development skill carry this rule.
`wiki/check_refresh.py` detects source drift at the chosen authority; optional
worktree inspection includes index, working files and untracked source. It does
not automatically approve content, advance the review ledger or publish changes.
Outside-Git operations and deployment/owner evidence still require review.

Website publication does not promote gameplay or close remaining owner QA gates.
