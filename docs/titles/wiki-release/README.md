# Titles wiki preview — published November 12, 2026

Owner request: “Push to wiki.” Published release
`20261112-earned-titles-v1` replaces `20261112-dot-ticks-v2`.
Public guide: https://wiki.nightcapgame.org/titles.html.

This publishes instructions for all77planned cosmetic titles, not the server
feature. Availability is **Not released**. Title counting/unlocks/#titles are not
activated; native rendered/gameplay acceptance remains OPEN. Main source PR428
and this website release are separate evidence.

## Source and verification

`baseline.json` is the fresh read-only origin snapshot. Rebuilt the authenticated
DoT public source and matched all613public hashes before any title edits.
`source-reproduction.json` records that proof. Source input lives under the
ignored `artifacts/titles-wiki-20261112/wiki-source-v2/`, preserving configuration
and reviewed public-source overrides rather than publishing the main mirror.

All43authored sources, navigation/commands, release labels and generated item/
zone/catalog impacts were reviewed. Added only titles.html. Updated ten owning/
navigation/history pages plus Guides, search index and sitemap. The other600
existing files retain exact bytes; assets, all item/zone values/acquisition,
Build Lab and Loot Finder are retained. Existing Imitate Death/DoT live guidance
and every unrelated candidate boundary remain.

- 20complete-site/refresh tests pass: release-tests.log.
- 77exact title requirements, generated-source parity, top title search queries,
  and existing search/equipment/experience controls pass: content-checks.json.
- 16Linux publisher/recovery tests pass before activation. The updater rehearsed
  the previous pointer and returned to the new release: publication.json.
- All614public HTTPS SHA256/security-header checks and five private404denials
  pass: public-verification.json. Total verified public bytes:8769888.
- All five service IDs/start times, config bytes/inode, channel and private
  downloads are preserved. No Nginx reload, server restart or gameplay write.
- Browser rendering remains unverified because no web browser is connected.
  Native RoF2 title-picker/nameplate acceptance is a separate open gate.

The exact tools are `prepare_titles_wiki.py`, `check_titles_wiki.py`,
`publish_titles_wiki.py` and `verify_titles_wiki.py` under tools/. The first
preparation clone is retained privately after a slow diff attempt; a subsequent
guard rejected Home's differently named anchor before any article was written.
The successful preparation resumed only after proving its entire input clone
still matched the authenticated baseline. No public mutation occurred until
the final validated package was published.

## Recovery and future maintenance

The publisher is one-shot. Do not rerun it after a terminal receipt. Retained
remote stage: `/opt/nightcap/releases/wiki-earned-titles-20261112-v1/`;
publisher history owns the exact previous/new manifests and config/service
preimages. Current relative pointer is releases/20261112-earned-titles-v1;
previous DoT release remains available. Any future update must acquire the same
deployment/website locks and compare the actual pointer/config/services first.
Never restore over a later release, edit Nginx in place, change player access
or reuse a game-deployment operator for a content-only update.

`wiki/check_refresh.py --ref HEAD --include-worktree` remains REVIEW REQUIRED for
historical unrelated source drift. This scoped publication does not advance the
global ledger or establish title gameplay acceptance. A later native activation
must update the guide's release label only after exact deployment evidence.
