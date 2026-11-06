# Single Shield Block total

Owner requests the plain label Shield Block. Keep the existing total (EQType10200)
and remove the redundant augment-only row, avoiding duplicate names or implying
that its bonus should be added a second time. Remove NCST_Row1/Name1/Value1 and
its tile reference, compact the tile/focus section, retain the normal font.
Tooltip says the total includes augments and strongest augment block applies.
No server, DLL, protocol, cap, item, stacking or combat change; no restart.

Signed candidate2026110604/proxy0.13.4 replaces Inventory XML only;147other asset
URLs/descriptors retained. Existing Stats2/gameplayUI5 tests pass. Scope audit
proves exactly3redundant controls removed,4owning controls updated, every other
control retained, and one Shield Block label using the original total EQType.
Publisher20Linux fault tests precede publication; signature/exe/pair checks apply.

Owner QA: exit EQ/use launcher Play. Inventory Stats shows one Shield Block row
with the same total (7% in the supplied screenshot), no Hunt/contribution/max
breakdown row. Shielding stays separate. Confirm normal font/scrolling/resize and
gear refresh. Prior owner report confirms functioning; revised display remains
live QA. Do not interpret synthetic checks as native pixel acceptance.

Wiki: five owning guides/Features/Change Log reviewed together; current normal
instructions use one total. Historical release notes retain their dated scope.
All item/zone/catalog values, Home, navigation, other guides/Build Lab/assets
remain. Publish only scoped changes over the actual public510-file source,
exclude unrelated main-only previews. Recovery uses a newly signed higher counter
with prior XML plus current retained assets; never roll the counter back.

## Verified publication

Main PR414/b80a6e0959f1308bcb1e1dd585dee2b90f1019ed is published as signed
2026110604/proxy0.13.4. Signature, all148descriptors/history and served changed XML
plus retained DLL/catalog verify. Publisher hashes all147retained files; all five
service identities/starts/restarts are unchanged. HTTPS scope is3files, not a
repeated download of unchanged files. No server/DLL/restart/player-data change.
20Linux publisher fault tests and7UI/3public-scope tests pass. Wiki510files,
504preserved, rollback/private/service guards pass. Recorded overrides
reproduce79source inputs/510outputs. Historical global drift stays review-required.
Owner previously reports Stats functioning; revised display pixels remain QA.
Exit EQ/use launcher Play to load the XML update.
