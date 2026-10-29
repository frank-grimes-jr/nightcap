# Bazaar posting and readability repair â€” October28

## Report and diagnosis

Owner confirms buttons now render on signed2026102802, but Post does nothing with
an item on the cursor and a price entered in public East Commonlands. Text is
small and black. Owner requested no computer use; no further UI automation or
process inspection is used. Current installed proxy0.13.1 and XML match2802.

Read-only disassembly of the pinned RoF2 executable establishes a supported
native input path missed by synthetic tests: CEditWnd::SetWindowText at0x87DD00
can convert ordinary digits to UTF16 at0x87DD51 and store InputText at+0x1EC.
Typed-byte append806E02â€“806E97 preserves that representation. CXStr+4 is capacity
in bytes, +8 is code-unit length, +12 is encoding0/1, payload begins+0x14.
UTF16 allocation8058F0â€“8058F5 doubles the requested unit count; copy805AC7â€“805AE4
copies2*(length+1) bytes. The old BazaarPrice reader rejected encoding1 silently.
This proves a supported-path defect, not the owner's exact runtime encoding.
Page/Tab native forwarding and normal button message1 were independently reviewed;
no additional notification/frame defect was established.

## Change

- Read printable ASCII price characters from both native byte and UTF16 storage.
  Bound length32, byte capacity, encoding and exact terminator before returning.
  No retained pointers or altered server transaction rules.
- Failed Post/Confirm price reads display feedback and invalidate a stale quote.
- Seller controls use font4 and explicit light text255/245/225. Taller controls,
  separated rows and a taller default window leave room for larger labels.
  Saved small windows retain scrollbars. Native Search controls, ASCII serialization
  and both required tab border templates are preserved.
- Proxy0.13.2/catalog remain paired; config and all other client assets stay intact.

## Verification and delivery boundary

Price-encoding and visible-feedback regressions failed before the fix and pass
now. Native coverage includes zero/short byte capacity, length32 boundaries in
both encodings, malformed terminators, non-ASCII input, real notify-to-post dispatch,
failed confirmation invalidating a quote, double clicks and identity changes.
All11 runtime groups,117 exact-client guards,2 Bazaar native groups and19 Python
UI/asset tests pass. Independent native ABI/source review found no blocker.
An initial runtime-suite invocation omitted its required --eqgame input; the full
correct invocation subsequently passed. No failed check was waived.

Prepared against fresh signed2026102802 with three replacements: proxy, catalog
and Bazaar XML;138 remaining descriptors/URLs and all history/tombstones retained.
Main PR357/42a849d2669f2d52e5c46076b3546dea2a462b35 and signed2026102803
publication are complete. The live channel and all three changed files match
the signed candidate; all141HTTPS assets, production signature and actual DLL/catalog
pairing pass hosted verification. Allfive service IDs/start times/restart counts
are unchanged. Wiki20261028-bazaar-post-readability-v1 is published; all499public
files, security headers and private-route denials verify. The owner subsequently
reported "It works" and explicitly confirmed "Preview appears and text is readable".
The reported posting/readability problem is accepted as resolved; offline buying,
cancellation/collection and exhaustive resize QA remain separate. See
[owner acceptance](owner-acceptance.json) and the
[verified wiki acceptance update](../posting-owner-qa-20261028/README.md). This is a
client-only repair; it requires full EQ exit and launcher update, no server restart.

## Exact player QA

After update, enter public East Commonlands safely out of combat and other trades.
Open /bazaar â†’ Sell / My Listings. Confirm light readable text at the saved size
and after resizing; scroll to every action if the saved window is short.
Pick up an inexpensive permanent tradeable item, enter1platinum and click Post.
The exact item, quantity and per-item/total price must appear for review. Click
Confirm Post once; verify one listing and one cursor removal. Reopen the window
and verify persistence. Search/buy with seller offline, cancellation with empty
cursor, and proceeds collection remain end-to-end owner QA. Do not infer those
outcomes from unit tests. Failed input must produce visible feedback.

## Wiki impact review

All40 maintained article sources and generated catalog ownership reviewed for
scope. Launcher/interface troubleshooting, tunnel seller instructions and Change
Log own this correction. Home/Features already describe the same seller panel;
commands, items, zones, catalog values, class/grip/Monk behavior and unrelated
release labels have no semantic change. Keep Live testing and prior corrections.
Global refresh ledger drift remains a review signal, not authority to advance
historical source pins. Publication must be verified separately.
