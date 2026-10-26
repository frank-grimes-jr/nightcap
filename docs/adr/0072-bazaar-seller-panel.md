# 0072: Native Bazaar seller controls

Date:2026-10-26. Status: implemented candidate; deployment and player acceptance pending.

Players need mechanical posting/cancellation/collection inside the Bazaar window.
Use a generated SIDL TabBox with the existing Search controls on the first page
and Sell / My Listings on the second. Recursive native child lookup and parent
notification forwarding support the nesting. Keep stock control names/definitions.
A separate NPC dialog would leave selling outside the requested Bazaar window;
a web inventory UI would duplicate ownership/authentication boundaries.

The proxy controls presentation only. Opt-in `#bazaar ui` requests use existing
native command transport, strict numbers/nonces and server-owned escrow operations.
A bounded counted NCBZ1 snapshot commits atomically in the client only for its
current request and character. Eight rows/page, at most100listings, exact balance.
Transactions and recovery remain in the existing escrow engine; no new schema.

Posting previews exact cursor metadata/quantity with a single-use60second nonce.
Cancel uses explicit selected-listing confirmation. Outstanding requests disable
mutations. Timeout requires a read refresh; no automatic mutation retry. A300ms
client cooldown after send/reply exceeds the server250ms gate; initial refresh is
retried after tab reopen without replaying the old action.

Specific verified Bazaar notify/frame/deleting-destructor vtable slots avoid a
shared-screen hook and the frame prologue's relative CALL. Forward the original
frame once, preserve result/destructor flags, consume only seller notifications,
and recheck identity/visibility at click time. Pair zone, proxy/catalog/config/XML;
client exact-byte guards and native fixtures do not prove rendered acceptance.

See docs/bazaar/seller-panel/{SPEC.md,QA.md,evidence.json}. New main/live approval
is required; earlier command-market approval is scoped to its deployed release.
