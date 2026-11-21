# Item name quality colors

November 21, 2026: merged to main in PR517 (`c65d6adc`) and published as signed
client `2026112101` / proxy `0.13.7-dev`. Wiki `20261121-item-name-colors-v1` is
published and verified. Owner visible acceptance remains open. The newer AA
purchase runtime and all five service identities stayed unchanged.

## Behavior and review

| Quality | RGB |
|---|---|
| Regular / Normal / Base | green `#00FF00` |
| Polished | blue `#0070DD` |
| Exalted | purple `#A335EE` |
| Ascended / Hunt Ascension | orange `#FF8000` |

The audit found no quality-color policy in the current proxy. Native item
inspection selects green/red/purple according to equipment eligibility. The
release colors usable item headings after native rendering, plus Advanced loot
rows/details and Bazaar seller listing/quote text. Red and native unmet-requirement
purple remain warnings; the quality palette does not grant equipment access.
Button normal, hover and pressed text retain the quality color; disabled text
keeps its native color. Row selection markers, quantity/price text and actions stay.

`eq-client-dll/src/item_name_color.h` recognizes exact quality suffixes, including
Hunt's distinct Ascension spelling. Dungeon prefixes apply only in the reward
catalog range. Natural stock names such as Polished Granite Tomahawk remain green.
IDs alone do not imply quality. Stats, rewards, item names, wire contracts and
server/cache data are unchanged. Generic native chat links, stock merchant lists,
tooltips and the Bazaar buyer list have separate rendering paths and are outside
this release's coverage; do not claim universal native text replacement.

## Native evidence

The protected `eqgame.exe` is read-only. Its pinned SHA256 is
`2a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e`.
The existing signed UpdateStrings hook at RVA `0x29AE30` runs after native
SetItem's color write at `0x2A9DCA`, through `0x29F240` / call `0x2A0506`.
Name is definition offset 0 (64 bytes); the existing accessor is vtable slot 2.
The item-name label is window offset `0x314`; text color is control offset `0x12C`.
CButtonWnd::DrawText at `0x497B30` uses `0x12C` normally, `0x210` on hover,
`0x214` while pressed and `0x218` when disabled. Only known item-name buttons
receive the hover/pressed writes. Existing executable hash and runtime guards apply.

The item-window regression reproduced six expected failures before implementation.
Focused fixtures execute the actual pinned native UpdateStrings and button text
color selector, with string/font boundaries stubbed. Controller fixtures exercise
row/quote replacement. Native equipment tests retain all class/race/slot checks.
Test and build results are recorded in `verification.json`. These tests do not
prove final pixels, clipping, real gameplay timing or owner acceptance.

## Delivery and recovery

Published proxy `0.13.7-dev` ships with its matching generated patch catalog;
the launcher's embedded catalog is regenerated too. Preserve the then-current
signed client manifest and all unrelated assets. No SQL, server build, cache
regeneration, quest/rule reload or server restart is required. Fully exit EQ and
use normal launcher Play after an authorized signed publication. Never copy into
the protected reference client. Recovery uses a higher signed release counter
containing the previously verified DLL/catalog pair and current unrelated assets.

The owner explicitly authorized main/server publication on November 21; see
`AUTHORIZATION.md` and `source-merge.json`. The signed envelope and served DLL,
catalog and retained Inventory XML verify using the shipped production trust key.
All 148 signed descriptors/history remain valid; 146 unrelated assets retain their
original descriptors/URLs and were hashed at origin. All 20 Linux publisher/recovery
tests passed. See `client-staged.json`, `client-published.json` and
`client-public-verification.json`.

The current AA purchase wiki release `20261121-aa-purchase-latency-v1` reproduced
all 631 files before edits. Publication changes Equipment, Advanced loot, Change
Log and search only; 627 outputs stay exact. All 631 public HTTPS hashes/headers
and five private 404s verify. The updater rehearsed rollback and preserved all
five services, the client channel and Nginx configuration bytes/inode. All 16 Linux
wiki publisher/recovery tests and 24 guide/language/refresh tests pass. Exact
receipts: `wiki-publication.json`, `wiki-public-verification.json` and
`wiki-candidate.json`. Historical source drift remains REVIEW REQUIRED without
an unrelated ledger advance. Publication does not establish player acceptance.

## In-game QA

1. In East Commonlands, inspect one usable ordinary item and its Polished,
   Exalted and Ascended variants. Expect green, blue, purple and orange.
2. Reuse the same inspection window from Ascended back to Regular. Expect green.
   Inspect a regular Polished Granite Tomahawk: green, not tier blue.
3. Inspect a Hunt Ascension augment and Polished/Ascended dungeon rewards.
   Expect orange and blue/orange respectively. Confirm descriptions and shield-block
   annotations remain intact.
4. Inspect an item for an unheld class and one with unmet native requirements.
   Native warnings and equipment rejection must remain. Check a held secondary
   class item still equips normally.
5. Earn representative loot in a disposable QA instance, then check Advanced loot
   rows, Filters and item rule details. Hover, press, switch pages, reuse rows,
   close/reopen and reload the UI. Colors and selection/actions must stay correct.
6. Use the Bazaar seller page with QA items. Check quotes/listings at each quality,
   hover/press and quote dismissal. Price, quantity and confirmation behavior must
   remain intact. Use disposable QA listings for transaction checks.
7. Relog through the launcher-installed release; confirm the same colors and no
   missing-item or UI-reload crashes. Record screenshots and client generation.
