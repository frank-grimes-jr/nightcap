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
node test_experience.cjs
node test_build_lab.cjs
python -B -m unittest test_build_lab
python -B build.py --package ABSOLUTE_NEW_FILENAME.tar.gz
python -B -m http.server 8767 --bind 127.0.0.1 --directory dist
```

Open `http://127.0.0.1:8767/`. Search requires JavaScript; all articles, directories,
contents and links are static HTML and remain readable without it. The Linux-only
recovery test is deliberately skipped on Windows and must run on the host before
deployment. Packaging emits an exact SHA256 manifest alongside the immutable tar.

## Clear content structure

Features is the grouped directory of custom adventures and systems: explicitly
name Raid/Grind, helmet quests, hunt/epic/class-armor rewards, character systems,
crafting and exploration. Keep each description short and link its owning guide.
Use Adventures, Character, Gear/world and Tools/previews groups; unavailable
content must say Not released. Do not reduce the directory to abstract slogans.
Guides owns current instructions, requirements and restrictions. Change Log
(`recent-changes.html`, retained for existing links) owns dated releases, fixes,
version numbers and resolved incidents. Do not prepend release announcements to
Home, Features or every affected guide. Update the actual instruction in its
owning guide and add the dated history once in Change Log.

Use the common heading/body scale in `assets/clarity.css`; avoid per-guide hero
titles. Keep long boss lists and advanced references in labeled `guide-topic`
disclosures. Every disclosure needs an ID and a useful summary; Contents/deep
links open it automatically. Existing anchors for moved notices remain contextual
links into their Change Log entry. Do not remove those links.

The guide index lists maintained guides and directory entrances, while individual
item/zone pages remain in their dedicated catalogs and global search. Home keeps
the four compact goal paths; its release digest and duplicate directory lists are
retired. All492HTML pages/499public files and the public asset allowlist remain.
One-time migration and audit: `tools/wiki_clarity_migration.py` and
`docs/releases/wiki-clarity-20261024/`. Future edits belong in article JSON.

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
  authority. The October23 paired release gives two passive AA per level and level-1 percentage controls;
  review the latest operations evidence before changing either claim.
- Keep `Live testing`, `Not released`, and `Reference` distinct. Do not turn
  installed status into a promise of completed gameplay/balance acceptance.
- `assets/traders-at-dusk.png` and `moon.svg` are unchanged approved site artwork.
  CSS and browser search are local. No third-party trackers or dependencies.

The coordinated October24 release contains 489 articles plus All articles,
Search, and 404 pages (492 HTML pages and 499 public files). Ashen Compact
adds its campaign guide, Kael page and fourteen exact item pages; High Keep
rescue and pending gameplay acceptance are described in the owning guides.
`items.html` is the Equipment catalog: 96 item families with their four qualities
together, type/slot/level/zone/name filters, sorting and 12-family pagination.
The URL preserves filters; all item links remain in static HTML without JavaScript.
`equipment.py` generates the directory. Its small CSS/JS files are bundled into
the existing public assets by `build.py`, with content-based cache versioning.
Run `test_equipment.cjs` for filtering, paging and all 384 exact variant names.
This is a custom-system and reward wiki; it is not the full ordinary game database.

`catalog.json` also has a separate `chapterhouse` projection for the verified
expedition release: four Ember qualities, three miniboss items, six final Raid
variants and Camil's existing helmet. `chapterhouse_catalog.py` generates its
zone and item pages with distinct acquisition/forging rules. The Classic Hunt
directory stays at 384 variants and 96 families. Whole-site links and the new
reward boundary are checked by `test_wiki`; preserve the existing Build Lab and
automatic loot finder when publishing this release.

## Interactive handbook

`experience.py` composes four home-page reading paths from maintained article
titles/summaries. It moves the original release notices intact into a native
disclosure below the discovery tools. Keep those notices and their fragment IDs.
`assets/experience.css` supplies dark/light tokens and responsive layouts;
`assets/experience.js` supplies quick search (`/`, Ctrl/Command+K), browser-local
bookmarks, theme preferences, path URL/Back state and reading progress/contents.
The builder bundles these into the existing versioned CSS/JS asset allowlist.
There are still 458 HTML pages and 465 public files; no runtime packages or new
hosting configuration are required.

Article prose, directory links and all four paths remain available without JS.
Search loads its public index only on demand. Saved pages and theme use the
`nightcap.saved` and `nightcap.theme` local-storage keys, never a server account.
Stored titles render as text and only local safe slugs become links. Blocked
storage falls back to the current page visit with a visible message. Native
dialogs manage keyboard focus; reduced motion and print remain supported.

Run `test_experience.cjs` for history, storage, search races and failure recovery.
Repeat real-browser responsive/keyboard checks for shell changes, including the
Equipment directory and long dungeon guides. Exact release evidence lives in
`docs/releases/wiki-interactive-20261022/`.

## Experimental Build Lab

`build-lab.html` compares two browser-local diagnostic builds at Classic50.
`build_lab.py` embeds the reviewed projection and public Hunt item stats;
`assets/build-lab-model.js` is the pure calculation/scheduling model shared with
Node tests. `build-lab.js` and `build-lab.css` implement the workbench in the
existing bundled assets. No new hosting paths or external dependencies are needed.
There are now459HTML pages/466public files and22maintained guides.

Eight source-pinned spells,12native landed value controls, effective stat caps,
custom resolved abilities, A/B results, item differences and exhaustive priority
permutations are supported. Full gear/AA/pet derivation, native boss AI and global
optimality are explicitly outside this first model. Preserve these limits beside
results and in the guide. Data regeneration: `python -B tools/build_lab_data.py`
from the repository root; review the source fingerprints instead of silently
refreshing them. Design and provenance: `docs/build-lab/`.

Saves use `nightcap.build-lab.v1`. Validate imports, class uniqueness, bounds,
canonical library identities and source values before use; render labels as text.
Browser tests must include edits recalculating on input, save/reload, invalid and
valid imports, gear differences applied once, class changes, ability edits,
optimizer cancellation and320/768/1024/1440 layouts.

## Verification contract

### Production loot finder

`loot-finder.html` adds any-held-class search (up to three), optional all-class
matching, the active production era, slot/quality/level/zone/name filters and
per-item mob/location/drop-rate details. `loot_capture.py` uses a fixed content
allowlist in a read-only MariaDB transaction. `loot_model.py` projects public
fields and calculates native database-loot probabilities; `loot_refresh.py`
publishes immutable snapshots. `loot_install.py` guards the initial JSON route
and systemd installation. The owner-approved reader, timer and JSON route were
installed October 22, 2026; publication/refresh evidence is in the release folder.

The release has460HTML pages/467public static files. Dynamic JSON is separate;
the existing Hunt catalog remains384variants/96families. Player rows, credentials,
raw captures, scripts and manifests are excluded from both public surfaces.
Private dungeon, quest, scripted and Hunt acquisition remain separate guides.

From `wiki/`, run `python -B -m unittest test_loot_model test_loot_refresh
test_loot_install`, `node test_loot_finder.cjs`, and the existing complete-site
checks. From repository root, `python -B wiki/verify_loot_linux.py` runs Linux
recovery tests and200,000-roll native comparisons in existing local Docker images,
with network disabled and the checkout mounted read-only. It uses a private
fixture at `artifacts/wiki-loot/content.json.gz`; never commit or upload it.
The script writes its receipt under that ignored directory.

`python -B wiki/verify_loot_nginx.py` checks the compressed-only storage contract
in offline local containers using synthetic data. Public `.json` URLs are served
by static gzip/gunzip; manifests hash decoded bytes and direct `.gz` URLs are
denied. The publisher keeps eight generations and reserves 256 MiB free disk after
staging allocation. Compression changed storage only, not filtering or rate math.

Local preview: `python -B wiki/loot_refresh.py --capture
artifacts/wiki-loot/content.json.gz --output artifacts/wiki-loot/preview`, then
`python -B wiki/preview_loot.py` at loopback port8769. This is a fixed local capture;
the production timer is separate. The UI does not expose an SQL console or DB port.

[ADR](../docs/adr/0068-production-wiki-loot-reader.md),
[operator/recovery](../docs/ops/wiki-loot-reader.md),
[evidence and acceptance](../docs/releases/wiki-loot-finder-20261022/README.md).

### Complete site checks

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
