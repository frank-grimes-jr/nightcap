# Main Inventory without scrollbars

November 20, 2026: merged to main in PR492 (`f8faa1ba`) and published as signed
client `2026112001`. The matching wiki is published. Native visible acceptance
remains pending. Source started from freshly fetched main `99331464`.

## Problem and correction

The owner reported unwanted horizontal and vertical scrollbars. Their screenshot
also shows the bottom button row partly obscured. The November 12 summary generator
enabled both flags on `IW_InvPage`; its parent tab box already stretches automatically.
Disable only `Style_VScroll` and `Style_HScroll` on the main Inventory page.
Keep the current 468 by 556 window, font, stat rows, equipment, bags and button geometry.
The separate Stats page retains scrolling for its longer content.

`tools/client_inventory_summary_ui.py` fixes normal generation and provides
`remove_inventory_scrollbars_xml(raw)` for existing published bytes. It rejects
missing/duplicate/unsupported flags, is idempotent, and preserves every other byte.
Use this scoped transform on current signed Inventory XML, not whole-file generation
from the protected reference client or an older release.

## Evidence and validation

Read-only OVH capture found client release `2026111301`, still carrying Inventory
SHA256 `545e9692f01bde1071bab4c927a66b13a6a9b2c07b638ad48e2c2cbd8bff5ab2`.
The candidate is `artifacts/inventory-no-scrollbars/candidate/uifiles/nightcap/equi_inventory.xml`.
`verification.json` pins its hash and current channel; `inventory.patch` shows the
complete two-setting change. The initial generic HTTP probe returned 403. The
launcher User-Agent verified the published signed channel and served XML/DLL/catalog
over HTTPS. The publisher hashed all 147 retained origin assets. Exact scope is in
`client-public-verification.json`; publication is not native visual acceptance.

The new scrollbar expectation failed against the original generator. All 19 tests
pass after repair:

```powershell
python -B -m unittest tools.tests.test_client_character_stats tools.tests.test_client_gameplay_ui tools.tests.test_client_gameplay_assets
```

Tests cover generated flags, stat/cap/heroic layout, equipment semantics, exact-byte
repair scope, idempotence, malformed inputs and retained Stats scrolling.
Independent source and publication reviews passed, including the comment-only
XML match regression. All 20 publisher fault/recovery checks passed on Linux.
The wiki passed 19 tests and six search cases; its 16 Linux publication/recovery
checks also passed. The existing geometry is preserved; static checks do not prove pixels.

## Client delivery and recovery

Published client `2026112001` retains all 42 prior signed note entries and all
147 unrelated asset descriptors/URLs, DLL/catalog/config, tombstones and launcher
requirements. Only Inventory XML and its additive release note change. Future
corrections must recheck the actual channel and use a higher signed counter. No server, DLL, database, cache or protected-client write is
needed. The player must fully exit EQ and use normal launcher Play after publication.
An old running client cannot receive this correction through server rule reloads.
Recovery after publication requires a higher signed counter over the then-current
channel; never rewind a public channel or discard unrelated newer assets.

The owner authorized main promotion and publication on November 20: "Push to main and server".
See AUTHORIZATION.md. Native visual acceptance remains separate from publication.

## Exact native QA after publication

1. Fully exit EQ, use launcher Play, log in as Palwar and open Inventory.
2. Confirm both scrollbars are absent; no horizontal or vertical scrolling is needed.
3. Confirm all six bottom buttons and Plot Items are visible and clickable.
4. Confirm all equipment and ten bag slots remain visible; test normal bag opening
   and an ordinary gear move. Check crystal labels, money, XP, weight and stat rows.
5. Open Stats and scroll to its lowest bonuses. Check the other tabs still work.
6. Close/reopen Inventory, reload the Nightcap skin, then relog. Repeat the visibility
   checks with the saved window placement and the player's usual resolution/UI scale.

Native visual acceptance remains pending; the screenshot is a bug report, not acceptance.

## Wiki impact

The current public pointer was `20261114-titles-automatic-suffix-v1`. Its retained
source reproduces all 631 files before editing. Published source is under
`artifacts/inventory-no-scrollbars/wiki-source/wiki`; only Equipment, Recent changes
and the generated search index change. Main source receives the same scoped edits.
`published-wiki.patch` applies to the current publication's source with `--unidiff-zero`.
`wiki-impact.json` records whole-wiki scope; unrelated guides, Features/Home/commands,
item/zone catalogs and numeric/balance data need no edits. Refresh-ledger drift stays
review-required; do not publish the older main wiki mirror or blindly advance it.
Wiki `20261120-inventory-no-scrollbars-v1` is published. The updater verified all
631 origin files and rehearsed rollback; all five services and the Nginx configuration
bytes/inode stayed unchanged. The matching client channel was preserved. See
`wiki-publication.json` and `wiki-public-verification.json`: all 631 public hashes
and security headers pass; five private source paths return 404.
