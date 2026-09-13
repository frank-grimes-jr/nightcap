# Native AA purchase and grant persistence

Date: 2026-09-13. Feature branch only; no live activation or promotion.

Thirteen native controls exercise 52 operations per phase. Ten controls fail on
the previous source; all thirteen pass on the candidate. The three existing
rejection controls retain identical complete reports and raw report hashes.

Covered behavior:

- Paid first/second ranks save both ownership and the reduced wallet before reload.
- Free, paid multi-rank, and silent grants persist without a later profile save.
- Failed character updates roll back ownership and points, invalidate the session,
  and emit no AA purchase event. Further AA save/reload is refused until reconnect.
- Insufficient funds, skipped paid predecessors, suspended already-earned ranks,
  duplicate charged purchases, and invalid-session silent grants remain rejected.
- Charged purchase/consume/repurchase preserves wallet, earned, and expended costs.
- Grant-only abilities reject ordinary purchase and retain explicit grants.

The initial before run also exposed a stale profile-array result after successful
grants. It is included in the final before/after acceptance states. The final
matched runs include exact native AA event payloads, not just event counts.

The diagnostic captures only explicitly enabled AA_PURCHASE player-event packets
and decodes them using the native serializer. No packet is sent to world. Other
world notifications remain forbidden. The profile fixture supplies a positive
account ID for native profile behavior; it does not simulate authentication.

Both runs clean their synthetic rows and failure trigger. The AA ability/rank
catalog is unchanged. The current clone is nightcap_balance_20260912.

A fresh source tree contains 2,787 verified files, differing from the previous
bulk-refund build only in zone/aa.cpp and zone/client.h. The build succeeds and
all 87 C++ tests pass in the dedicated test directory. The initial source-directory
run returned zero despite four IPC mutex failures because its shared/config paths
were missing; aa-purchase-cpp-tests-initial.log preserves that failure. Acceptance
uses the complete passing suite summary, not its exit code alone. Zone SHA256:
da5b36b19ed6ce3c5ae5eb172e4d5cad5a3617694873f2d4293fc4e3257f2c6a.
Adjacent aa-purchase-* artifacts retain exact engine/diagnostic sources, the
regenerable patch, native reports, build logs, and manifests. Build JSON trailing
line separators were normalized on export; engine source and build output bytes
are preserved. The evidence manifest hashes the retained artifacts. All 339 calculator and
evidence tests pass; aa-purchase-python-tests.log retains the complete run.

Remaining gates: the full auto-grant/grant-all caller loops, quest/world event
delivery, toggles, class release, real reconnect, network/uncertain-COMMIT failures,
ordinary save paths, and in-game QA. Successful batch grants are durable per rank;
a later failure leaves earlier committed grants intact. This is not a claim that
all AA persistence or encounter balance is complete.
