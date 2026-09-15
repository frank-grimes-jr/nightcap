# ADR 0025: Durable AA purchases and grants

> Current status (2026-09-15): implemented server/AA/PoK candidates are deployed for live QA; main gameplay acceptance remains pending. See [current status](../status.md). The dated evidence below retains its original scope and is not a current deployment checklist.


Date: 2026-09-13. Status: implemented on the AA feature branch; promotion pending.

## Decision

FinishAlternateAdvancementPurchase stages canonical earned and usable ranks,
then persists them with unspent, spent, and expended points through the shared
AA transaction helper. Change session state and emit purchase events only after
the commit is acknowledged. The method returns success; GrantAlternateAdvancementAbility
reports whether any rank was actually committed and stops after invalidation.

The old send_message_and_save switch becomes send_message. Silent grants must
persist too. AutoGrantAAPoints and GrantAllAAPoints stop when acquisition fails;
their successful ranks are committed individually. GrantAll no longer needs an
unrelated final SaveAA call. A failed later rank does not undo earlier committed
grants. This is per-rank durability, not an all-or-nothing batch.

Callers retain their purchase/grant eligibility rules, including explicit
GrantAll unlock levels. The shared finish method additionally rejects invalid
ownership, duplicate earned ranks, unavailable ranks, invalid costs, insufficient
points, and an already-owned charged ability. Nominal earned costs remain the
spent-point accounting basis even when a grant costs the wallet zero, matching
the existing earned-AA policy.

## Evidence and limits

Thirteen native before/after controls exercise 52 operations per phase. Ten fail
before and all thirteen pass after. Exact event ledgers prove that injected
failed purchases/grants emit no AA purchase event. Three rejection controls retain
identical complete reports. A fresh 2,787-file build and all 87 C++ tests pass.

The diagnostic explicitly captures only AA_PURCHASE player events, using the
engine's serializer format. It forwards no world packet and still rejects other
world notifications. It does not test delivery to world, quest callback effects,
the full auto-grant loop, actual reconnect, or uncertain network/COMMIT failures.
Toggle and class-release integration, broader ordinary-save behavior, and in-game
QA remain open. No live server or balance numbers change in this increment.

Evidence: ../balance/native-aa-purchase.md.
