# Merchant Sell All button — implementation candidate

The shared Nightcap merchant window has a **Sell All** button in the spare
footer below the stock action row. A left click sends exactly `#sellall` through
the existing silent UI request sender. The server still owns eligibility,
pricing, inventory changes and the sale summary. This adds no NPC scripts,
merchant-specific records, database changes or new sale policy. The command
still works from chat as before. Ordinary Buy, Sell, Done and other merchant
notifications retain their native handlers.

Source baseline: `origin/main` at `6224005`. The primary workspace has separate
uncommitted sell-all supply changes; those were not overwritten or transplanted.
The button deliberately follows whichever sell-all policy the server deploys,
including newer food/trade policy changes on main.

## Exact-client evidence

Read-only inspection of the pinned RoF2 executable (SHA-256
`2a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e`):

- Constructor at VA `0x6F4E10` assigns vtable `0x9F25B8` at `0x6F4E84`.
- Its notification slot `+0x88` points to VA `0x6F3A90`, RVA `0x2F3A90`.
- The overwritten eight bytes `6A FF 64 A1 00 00 00 00` are two complete
  instructions (`push -1; mov eax, fs:[0]`), without a relocation operand.
- Notification `1` handles native left clicks. The constructor resolves
  `MW_Sell_Button` at `0x6F512B` into member `+0x26C`; the handler compares
  against that member at `0x6F3AE6`.

The hook uses the existing guarded entry trampoline and resolves the new child
on each callback, so UI reloads cannot retain a stale control pointer. Requests
are suppressed at character select or without the profile/connection. The
required feature, runtime configuration, generated patch catalog and launcher's
embedded preflight catalog advance together.

## Verification

- x86 DLL build and runtime fixture compilation: passed.
- Native ABI regression: 1,000 valid button clicks, non-click notifications,
  stock/null senders, disconnected/character-select states and stale child
  replacement checked; passed as part of `tests/test_runtime.py`.
- Five runtime test groups: passed. Set TEMP/TMP to a writable workspace
  directory when the sandbox's default temporary directory denies file writes.
- Merchant XML generation tests and existing six gameplay-asset tests: passed.
- Real stock `EQUI_MerchantWnd.xml` generation: passed, every existing control
  retained. Output staged under `artifacts/merchant-sell-all/` in the main workspace.
- Exact-executable signature verification and generated catalog consistency: passed.
- Launcher `go test ./internal/preflight`: passed with the synchronized catalog.
- Native model compatibility fixtures: 288 family/flag cases and graphics
  invisible-model regression checks passed against the read-only reference files.

Candidate DLL SHA-256:
`c3823ec3af4a7d49de42e9c4753c83d256ce7ed8246758923872402462c7e24b`.

Native in-game rendering and sales remain unaccepted. No installed client,
server process or hosted release has been changed.

## Packaging and recovery

Build `eq-client-dll/build.bat` and generate the gameplay assets with
`tools/client_gameplay_assets.py`. Include `uifiles/nightcap/equi_merchantwnd.xml`
alongside the candidate DLL, `nightcap-patches.cfg` and patch catalog in the next
signed client release. The current desktop supports authenticated signed catalog
evolution and Nightcap XML assets, so this change needs no replacement desktop.
Its embedded catalog remains synchronized for future builds. A partial
DLL/config/catalog update is rejected by preflight/runtime.
Restart the client to load the DLL. No server rebuild is needed for this button.
Use the existing signed release procedure; do not copy files into the protected
`Client_RoF2_Dev` reference tree. Before publication, retain the complete previous
client release. Recovery uses that complete set (or a higher-numbered corrective
release if clients have already observed the new channel version).

## Exact in-game QA

1. Use a normal player account with the candidate client. Open a class merchant
   in Plane of Knowledge (`poknowledge`) and a different ordinary merchant in
   East Commonlands (`ecommons`). Confirm **Sell All** appears below the stock
   buttons in both windows, with a readable tooltip and no overlaps at the
   default size and after resizing.
2. On a disposable QA character, carry one known sellable item and one stack in
   bags. Record inventory and coin, click once, and verify one server sale
   summary, inventory removal and the same payout as `#sellall` with equivalent
   test inventory. Include a bag and temporary summoned item and confirm the
   deployed command's exclusions still apply. Test additional protected supplies
   only if that policy is present in the deployed server; this button does not
   introduce it.
3. Click with nothing eligible. Verify the existing empty-sale message and no
   wallet change. Right-click/drag the button and confirm neither triggers a sale.
4. Buy an ordinary item, use the original single-item Sell, inspect an item and
   click Done. Reopen another merchant; all native actions must still work.
5. Reload the Nightcap skin, reopen a merchant, zone, and relog. Repeat the button
   and ordinary sale tests; no crash, stale click target or duplicate sale.
6. Run `#sellall` directly and confirm it retains the deployed server behavior.

Owner acceptance is required before the normal test-to-main promotion.
