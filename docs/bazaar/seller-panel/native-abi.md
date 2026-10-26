# Pinned RoF2 Bazaar ABI review

Read-only eqgame.exe SHA2562a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e,
image base0x400000. ConstructorVA0x634220 assigns specific vtable0x9e39a0.

| Slot RVA | Method RVA | Preferred bytes | Purpose |
| --- | --- | --- | --- |
| 0x5e3a28 | 0x235990 | 90596300 | Notify |
| 0x5e3a64 | 0x2336f0 | f0366300 | Frame |
| 0x5e39a4 | 0x236e40 | 406e6300 | Deleting destructor |

All three slots are PE HIGHLOW relocations. Runtime expected pointer is imagebase
plus methodRVA. Verified patch handles protection/flush failures; required-hook
failure aborts startup. Never copy/rebase the whole table (its preceding word is
zero) or use the frame's first9bytes as a naive trampoline: its offset4 is relative
CALL. Frame maintains search and FindTrader timers and is forwarded exactly once.

Recursive GetChildItemVA0x868330 recurses at0x868393 irrespective of visibility.
Page ordinary notify0x85ead0 forwards viaCXWnd0x8682d0; Tab notify also forwards
originalsender/message/data through parent+0x174 virtual+0x88. Native price edits
sendmessage14; the stock Bazaar handler acts on it without checking sender, so
seller Price notifications are consumed. Enter never confirms a sale.

Window visibility+0x196, enable+0x1a, text virtual+0x124, CEditBaseWnd maximums
+0x1e4/+0x1e8 and CXStr pointer+0x1ec follow the verified client ABI. The price
reader bounds capacity, length32, ASCII encoding and terminator under SEH.
Resolve controls afresh; never retain children across UI reload/destruction.

Independent review confirmed these paths and the final cooldown/identity fixes.
Synthetic native hooks cover relocation guards, protection/flush rollback, frame
return, stock forwarding, price isolation, double clicks, character-switch clicks,
hide/missing assets and destructor flags. Generated XML is checked against the
actual stock file. Native rendering, resizing/focus and skin reload remain QA.
