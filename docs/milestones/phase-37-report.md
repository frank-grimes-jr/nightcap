# Phase 37: combat and item repair candidate

September 27, 2026. Work remains open; no deployment or gameplay acceptance.

Implemented held Monk/Beastlord fist identity across natural damage/delay,
magical fists, empty offhand and unarmed damage tables. Independent review found
that primary-only skill caps also blocked practical skill progression; the
candidate now advances against held-class native caps without free skill points.

Replaced flat tier spell/heal stamps with a base-item strength curve. A local
93,615-item migration rehearsal proved formula parity, preservation of other
columns, replay rejection and exact full-table rollback. Additional tests reject
base/identity/rollback drift and prove rollback after an injected post-update
failure. Ten focused tests and existing lifecycle/special-attack checks pass.

No speculative casting fix was included. Owner follow-up establishes that all
non-instant bars freeze even outside combat while spells finish. A guarded,
read-only timer capture is ready; an affected Nightcap reproduction is required.
The full world/zone build is still running, and representative balance/manual
QA remains open. External cross-model review was declined in favor of regression
tests and independent review.

[Scope, evidence, limitations and exact QA](../releases/combat-item-fixes-20260922/README.md).
