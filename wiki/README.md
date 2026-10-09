# Official Nightcap Wiki

Target: `https://wiki.nightcapgame.org/`. Publication state and host setup are in
[the runbook](../docs/ops/nightcap-wiki.md). The private player guide remains a
separate site. A public wiki does not grant accounts or game access.

## Build and check

Run from this `wiki/` directory; Python 3.10+ and Node are sufficient. No packages,
database, server APIs or account system are needed.

```powershell
python -B -m unittest -v test_wiki test_deploy
node test_search.cjs
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
- The source ledger is retained in article JSON but omitted from built HTML and
  search data. Current source snapshot: `19951a868080fb8e89521702dcb5bf609980a1a6`.
  Exceptions: the October 9 death/spell-gem change uses its dated root-workspace
  operations report. Preserve the latest 40% AA setting from the operations
  record; older guide text and the compiled 1% fallback are not current values.
- Keep `Live testing`, `Not released`, and `Reference` distinct. Do not turn
  installed status into a promise of completed gameplay/balance acceptance.
- `assets/traders-at-dusk.png` and `moon.svg` are unchanged approved site artwork.
  CSS and browser search are local. No third-party trackers or dependencies.

The first version builds 451 articles plus All articles, Search, and 404 pages.
This is a custom-system and reward wiki; it is not the full ordinary game database.

## Verification contract

Python checks all generated local links, fragment targets, assets, unique IDs,
single page titles, catalog families, key live values, release labels, exact
package contents and private-data exclusions. Node exercises the actual browser
search script against the built index. Browser QA covers real navigation, item
search, command relevance, unsafe/no-results text, clean logs and 320/768/1024/1440
layouts. Repeat browser checks after changing content layout or search behavior.
