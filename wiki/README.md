# Official Nightcap Wiki

Target: `https://wiki.nightcapgame.org/`. Publication state and host setup are in
[the runbook](../docs/ops/nightcap-wiki.md). The private player guide remains a
separate site. A public wiki does not grant accounts or game access.

## Build and check

Run from this `wiki/` directory; Python 3.10+ and Node are sufficient. No packages,
database, server APIs or account system are needed.

```powershell
python -B -m unittest -v test_wiki test_deploy test_update test_refresh
node test_search.cjs
node test_equipment.cjs
python -B build.py --package ABSOLUTE_NEW_FILENAME.tar.gz
python -B -m http.server 8767 --bind 127.0.0.1 --directory dist
```

Open `http://127.0.0.1:8767/`. Search requires JavaScript; all articles, directories,
contents and links are static HTML and remain readable without it. The Linux-only
recovery test is deliberately skipped on Windows and must run on the host before
deployment. Packaging emits an exact SHA256 manifest alongside the immutable tar.

## Maintain content

- Edit `articles/*.json`: title, summary, category, body (reviewed HTML), release
  status, review date, source references, and optional search keywords.
- `catalog.json` is an explicit public projection of the October 9 released item
  data. It contains only enabled zones and published item stats. `catalog.py`
  generates zone/item articles and their indexes. Update the projection from a
  verified release; never publish raw database exports or operational documents.
- Article source ledgers remain private and are omitted from built HTML/search.
  `content-review.json` records the latest reviewed source revision and supplemental
  deployment evidence. Do not use the older wiki branch's gameplay files as live
  authority. Current guide tuning is 10% passive AA and 4,000 AA XP per point;
  review the latest operations evidence before changing either claim.
- Keep `Live testing`, `Not released`, and `Reference` distinct. Do not turn
  installed status into a promise of completed gameplay/balance acceptance.
- `assets/traders-at-dusk.png` and `moon.svg` are unchanged approved site artwork.
  CSS and browser search are local. No third-party trackers or dependencies.

The build contains 455 articles plus All articles, Search, and 404 pages.
`items.html` is the Equipment catalog: 96 item families with their four qualities
together, type/slot/level/zone/name filters, sorting and 12-family pagination.
The URL preserves filters; all item links remain in static HTML without JavaScript.
`equipment.py` generates the directory. Its small CSS/JS files are bundled into
the existing public assets by `build.py`, with content-based cache versioning.
Run `test_equipment.cjs` for filtering, paging and all 384 exact variant names.
This is a custom-system and reward wiki; it is not the full ordinary game database.

## Verification contract

Python checks all generated local links, fragment targets, assets, unique IDs,
single page titles, catalog families, key live values, release labels, exact
package contents and private-data exclusions. Node exercises the actual browser
search script against the built index. Browser QA covers real navigation, item
search, command relevance, unsafe/no-results text, clean logs and 320/768/1024/1440
layouts. Repeat browser checks after changing content layout or search behavior.

## Required with every Nightcap change

Before completing a feature, fix, balance/content update, deployment or accepted
player correction, review its impact across the entire wiki. This is part of that
change, not a scheduled polling job. Update affected guides, Features (major
departures from Classic), home summaries, commands, generated item/zone guidance,
catalog values, status labels and Recent changes together. Check cross-links and
search. Do not rewrite unrelated pages or bump review dates without reviewing them.
If there is no player-facing impact, record that conclusion in the change evidence.

From `wiki/`, compare the recorded audit against the actual source authority:

```powershell
python -B check_refresh.py --repo PATH_TO_CURRENT_CHECKOUT --ref origin/main
python -B check_refresh.py --repo PATH_TO_TASK_CHECKOUT --ref HEAD --include-worktree
```

The checker returns 1 when scoped committed source changed, including new/deleted
files; `--include-worktree` also checks index, working copy and untracked sources.
Return 2 means comparison failed. Neither a clean result nor advancing the ledger
proves live deployment: separately read current release/QA records, operational
changes outside Git and the installed skill's source references. Never advance
`content-review.json` just to suppress drift. Reconcile all affected topics first.
Unreleased work stays labeled; website publication does not authorize game changes.

Build and test the complete site, preview changed layouts, package, then publish
with the authorized guarded `update.py` flow. Verify public bytes/routes and record
the release. Update the installed Nightcap skill's wiki reference and fingerprints.
If publication is not authorized or fails, report it pending; do not call local
edits a live wiki update. New systems need source-path coverage if outside the
current review scope. `test_refresh.py` exercises real Git change detection.
