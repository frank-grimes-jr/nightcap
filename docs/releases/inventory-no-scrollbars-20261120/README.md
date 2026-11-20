# Main Inventory without scrollbars

November 20, 2026: source and XML candidate prepared; not published or accepted in game.
Branch `feature/inventory-no-scrollbars`, based on freshly fetched main `99331464`.

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
complete two-setting change. Public HTTPS reads returned 403; this is an origin
capture, not a fresh public-download/signature validation or publication claim.

The new scrollbar expectation failed against the original generator. All 18 tests
pass after repair:

```powershell
python -B -m unittest tools.tests.test_client_character_stats tools.tests.test_client_gameplay_ui tools.tests.test_client_gameplay_assets
```

Tests cover generated flags, stat/cap/heroic layout, equipment semantics, exact-byte
repair scope, idempotence, malformed inputs and retained Stats scrolling.
The existing window geometry is preserved; static checks do not prove native pixels.

## Client delivery and recovery

Prepared launcher notes use candidate counter `2026112001` and retain the actual
current signed manifest's full note history. Recheck the channel and choose a higher
counter if another release lands first. Publish only Inventory XML plus the additive
note, retaining all other asset descriptors/URLs, DLL/catalog/config, tombstones and
launcher requirements. No server, DLL, database, cache or protected-client write is
needed. The player must fully exit EQ and use normal launcher Play after publication.
An old running client cannot receive this correction through server rule reloads.
Recovery after publication requires a higher signed counter over the then-current
channel; never rewind a public channel or discard unrelated newer assets.

Main promotion and publication await owner sign-off under AGENTS.md branch policy.
The historical November 12 permission does not authorize this release.

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
source reproduces all 631 files before editing. Candidate source is under
`artifacts/inventory-no-scrollbars/wiki-source/wiki`; only Equipment, Recent changes
and the generated search index change. Main source receives the same scoped edits.
`published-wiki.patch` applies to the current publication's source with `--unidiff-zero`.
`wiki-impact.json` records whole-wiki scope; unrelated guides, Features/Home/commands,
item/zone catalogs and numeric/balance data need no edits. Refresh-ledger drift stays
review-required; do not publish the older main wiki mirror or blindly advance it.
Wiki edits remain unpublished alongside the client candidate.
