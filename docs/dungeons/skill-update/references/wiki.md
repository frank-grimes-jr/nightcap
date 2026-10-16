# Official player wiki and Features

Reviewed October 16, 2026. Wiki source is currently in
`C:/Users/verre/.codex/worktrees/nightcap-wiki/EQ_Local_Dev`, branch
`feature/nightcap-wiki`, PR #138 into dev. Confirm checkout/revision before edits;
its gameplay tree predates current integrated and deployed systems. Read the
relevant system reference and dated release evidence, not this old gameplay mirror.

## Owner-required maintenance with every Nightcap change

Before completing any Nightcap feature, fix, tuning/content update, deployment or
accepted player correction, assess the whole wiki. Update all affected guides,
Features, home summaries, commands, generated item/zone pages, catalog values,
release labels and Recent changes together. Features means major departures from
Classic that players need to know. No player-facing impact means a recorded
assessment, not a cosmetic rewrite/date bump. This is part of each change, not
periodic monitoring and not authority to deploy gameplay or broaden access.

`wiki/check_refresh.py --repo CURRENT_SOURCE_CHECKOUT --ref origin/main` compares
the private `content-review.json` audit revision with selected current source.
For a task's edits use `--ref HEAD --include-worktree`: it unions committed,
staged, unstaged and untracked scoped sources, including new/deleted systems.
Return 1 requires review; return 2 means comparison failed. Check current release,
owner QA and operations outside Git too. Never blindly advance the ledger, infer
deployment from source, or describe locally edited content as published. New
systems outside scoped paths need coverage. The checker is an explicit command,
not an installed CI hook or automatic publisher.

## Content and implementation

`wiki/articles/*.json` owns reviewed prose, dates, availability and private sources.
`build.py` produces static HTML, local search, sidebar and category directories.
Features uses grouped reading rows in `articles/features.json` and wiki.css.
`catalog.json` is a public-only projection: 48 enabled hunt zones, 384 item variants,
96 families. `catalog.py` generates item/zone prose; update it when shared mechanics
change. `equipment.py` and equipment.js keep four qualities together with filters
and pagination. Do not restore flat category item dumps. New articles are indexed
and packaged automatically. Never publish raw DB exports or source ledgers.

The October 16 refresh covers 20% passive AA / 4,000 AA XP per point, all allowed
ranks from level 1, early scribing, class/any-playable-race equipment, no LORE,
three Base / four higher zone-forge costs, Veyra's four-copy box, Craft All,
temporary AA/short-box/discipline timers, healing targets, food/drink and hub/travel.
Ordinary top tier is Ascended; hunt top tier is Ascension. Gameplay acceptance
remains owned by each release. Broad combat-item and Adventure Journal candidates
stay unreleased. Existing item stats were not regenerated in this refresh.



Dungeon deployment source update October 16: the maintained local wiki has a
Live testing Raid & Grind guide, linked from Features, Travel and Recent changes.
The unreleased candidate notice was removed. The existing generated equipment
catalog remains specific to hunt rewards; dungeon rewards have a separate guide.
Full-site Python/link and Node search/equipment checks pass. Website publication
is pending. Exact preimages, installed source receipt and whole-wiki assessment:
`docs/dungeons/wiki-update/` and `docs/dungeons/wiki-review.md` in dungeon-modes.

## Tests, publication and recovery

From wiki/: nine `test_wiki` checks cover all 457 pages; five `test_refresh` cases
use real Git (including a staged change canceled in the working copy); Node
`test_search.cjs` has six cases and `test_equipment.cjs` seven. Linux-only
`test_deploy test_update` has sixteen recovery cases. Browser checks cover links,
keyboard navigation, clean console and 320/768/1024/1440 layouts.

Live public URL: https://wiki.nightcapgame.org/features.html. Active release
`20261016-features-v1`, previous `20261010-equipment-v1`. October16 public verification
matches all 464 SHA-256 values and headers, ten denied wiki source/private routes,
and current player-host behavior. Origin rehearsal preserves private downloads and
all five service identities. Evidence: `docs/releases/wiki-features-20261016/`;
runbook `docs/ops/nightcap-wiki.md`; maintenance `wiki/README.md`.

`update.py` holds the shared website lock and atomically switches a guarded relative
wiki symlink, verifies every file, rehearses the previous release and reapplies.
No Nginx reload or service/client/cache/gameplay update is needed for wiki content.
Preserve current credential-based access and Cloudflare configuration. Do not
reuse historical IP-only assumptions or initial installer for content updates.
Private receipts/manifests stay outside the public tree. Recovery requires the
current pointer/config preimage and preserves later releases and player activity.
