# Official player wiki and Features

Reviewed October 16, 2026. Wiki source is currently in
`C:/Users/verre/.codex/worktrees/nightcap-wiki/EQ_Local_Dev`, branch
`feature/nightcap-wiki`, PR #138 into dev. Confirm checkout/revision before edits;
its gameplay tree predates current integrated and deployed systems. Read the
relevant system reference and dated release evidence, not this old gameplay mirror.

## October17 independent Monk cooldown candidate

All21 maintained articles and432 generated reward routes were assessed. Combat,
multiclass/progression, Features, home, In development and Recent changes contain
local explicitly unreleased notices for the six independent basic Monk timers.
Existing no-death-EXP/reforge notes are preserved. Commands, item/zone stats,
recipes and reward values have no impact. No wiki publication occurred.

`docs/releases/monk-independent-reuse-20261017/` in the October17 Monk checkout
listed in multiclass.md retains the exact patch, preimage/install receipt,
whole-wiki assessment and source-drift report. Fourteen Python and13 Node checks
pass. Broad historical drift remains REVIEW REQUIRED and the global audit ref
was not advanced. Replace all six candidate notices together only after the
authorized paired server/client activation, then verify public bytes. Gameplay
and combined-AA balance acceptance remain separate from publication checks.

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

## October17 normal-item reforge candidate

Maintained wiki commit `f106a5d` adds explicitly not-released guidance for three
identical eligible Normal/Base copies to one Polished in the Reforging Box.
Higher recipes remain four and dungeon rewards remain excluded. All21 maintained
articles, commands,432 generated reward routes, catalog values and release labels
were assessed; item-upgrades/equipment/zone-hunt/Features/home/unreleased/Recent
changes and catalog.py changed. Fourteen Python and13 Node checks pass. The
HEAD/include-worktree drift check remains REVIEW REQUIRED; the global historical
audit ref was not advanced. Exact review, patch and preimages are retained in
`docs/releases/reforge-normal-20261017/` in the reforge-normal-items checkout.
These changes are local and committed, not published. The last verified public
release below remains `20261016-dungeon-journal-v1`; no gameplay acceptance inferred.

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



Dungeon guide published October 16: Raid & Grind is Live testing at
https://wiki.nightcapgame.org/dungeon-modes.html, with Features, Travel, home,
equipment/forging guidance and Recent changes updated together. The generated
equipment catalog remains specific to hunt rewards. All 465 public hashes and
origin preservation checks pass; browser search finds the guide first and its
320/768/1024/1440 layouts have no horizontal overflow. Owner gameplay and dragon
balance acceptance remain pending. Maintained wiki commit `78991d4`; source-install
receipt and whole-wiki assessment are in `docs/dungeons/wiki-update/` and
`docs/dungeons/wiki-review.md` in dungeon-modes. Separate publication evidence is
in `docs/dungeons/wiki-publication/` and wiki's `docs/releases/wiki-dungeons-20261016/`.

Journal follow-up published October16 as `20261016-dungeon-journal-v1`: the guide
lists all52 catalog bosses and explains stage messages, full-clear credit and
Keeper Status if objectives/history are blank. All465 public hashes, player-site
surface and service preservation verify;14 Python and13 Node checks pass. The
underlying native repair is deployed separately. The owner replied "Confirmed"
after the Befallen journal retest instructions, accepting that display fix;
full-clear rewards, other modes and balance remain open. The whole-wiki follow-up
found no public content impact: boss lists, fallback guidance and Live testing
labels remain correct. Acceptance scope is in the native verification record.
Source commit78991d4 and receipt docs/releases/wiki-dungeon-journal-20261016/;
the native release retains its whole-wiki review in docs/dungeons/journal-repair/.
October17 patcher announcement2026101701 needs no wiki content change: the
published guide and Live testing labels already cover the announced mechanics.
The whole-wiki assessment is in docs/releases/dungeon-patcher-20261017/.

October17 no-death-EXP candidate: Combat, progression, Features, home,
In development and Recent changes have local unreleased notices. All maintained
articles and generated catalog scope were reviewed; commands, item/zone stats,
rewards and other death mechanics are unchanged. Production still has the level10
penalty threshold. No activation or publication occurred. Evidence and exact
maintenance patches: `E:/EQ_Local_Dev/_worktrees/no-death-exp-loss/docs/ops/no-death-exp-loss-20261017/`.
Replace candidate notices together only after authorized activation, then verify
public bytes. The broad content-review revision remains unchanged.

## Tests, publication and recovery

From wiki/: nine `test_wiki` checks cover all 458 pages; five `test_refresh` cases
use real Git (including a staged change canceled in the working copy); Node
`test_search.cjs` has six cases and `test_equipment.cjs` seven. Linux-only
`test_deploy test_update` has sixteen recovery cases. Browser checks cover links,
keyboard navigation, clean console and 320/768/1024/1440 layouts.

Live public URL: https://wiki.nightcapgame.org/features.html. Active release
`20261016-dungeon-journal-v1`, previous `20261016-dungeons-v1`. October16 public verification
matches all 465 SHA-256 values and headers, ten denied wiki source/private routes,
and current player-host behavior. Origin rehearsal preserves private downloads and
all five service identities. Evidence: `docs/releases/wiki-dungeons-20261016/`;
runbook `docs/ops/nightcap-wiki.md`; maintenance `wiki/README.md`.

`update.py` holds the shared website lock and atomically switches a guarded relative
wiki symlink, verifies every file, rehearses the previous release and reapplies.
No Nginx reload or service/client/cache/gameplay update is needed for wiki content.
Preserve current credential-based access and Cloudflare configuration. Do not
reuse historical IP-only assumptions or initial installer for content updates.
Private receipts/manifests stay outside the public tree. Recovery requires the
current pointer/config preimage and preserves later releases and player activity.

October17 idle-zone reliability correction: all21 maintained guides and432
generated reward routes assessed. Only Recent changes receives a local notice:
production rule correction/reload verified, natural unload/player continuity
pending. Features/home/commands/travel/dungeons/catalog values and release labels
remain correct. No public wiki release was made. Exact review, source-drift
report, maintenance patch and guarded install receipt are in
`E:/EQ_Local_Dev/_worktrees/dynamic-zone-worker-lifetime/docs/ops/dynamic-zone-worker-lifetime-20261017/`.
Preserve the prior candidate notices and global historical audit revision.
