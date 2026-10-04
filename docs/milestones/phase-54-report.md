# Phase 54: Universal item trading deployed

Built: effective universal trading, retained raw attunement/item provenance,
exact 1pp former-NO-DROP resale at merchants and `#sellall`, purchase floors and
quantity controls, native regressions, release/rollback plan and in-game QA.

Independent review found the `#sellall` bypass and mixed stack/charge case; both
are addressed. All five native binaries and the full 308,928-row cache enable/disable/re-enable
check passed; exact evidence is in the release guide. This candidate
was approved and deployed to OVH. All 308,961 hosted items, matching processes,
backup and preservation checks passed. Manual gameplay acceptance is not claimed.

Cut: destructive catalog rewrites, global merchant-rate changes and client binary
patching. Open: native quote preview, player trade/metadata round-trips and
currency from repeatable free items. These remain explicit QA gates rather than
exceptions to the owner's universal item policy.

[Release record](../releases/free-trade-20261004/README.md).
