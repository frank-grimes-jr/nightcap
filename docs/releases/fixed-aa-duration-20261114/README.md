# Rage of Rallos Zek and Bloodlust · November 14 production

Rank-one Rage now lasts 12 seconds from successful application. Bloodlust lasts 24 seconds of active time and still pauses in zones that suspend buff timers. Neither cast consumes duration-focus charges. A zone crossing or reconnect preserves the remaining timer. The server removes the effect on the first processing frame at or after expiry.

The matched Linux fixtures covered three tick offsets, four focus inputs and an ordinary control spell, with 36 observations per build. Before the fix, unfocused Rage lasted 12–18 seconds and Bloodlust lasted 18–24 seconds. Extended Bloodlust could previously reach 30 seconds. Reapplication, dispel, deadline recovery and delayed frames are covered in the [measurements](../../combat/thj-aa-duration/MEASUREMENTS.md). The [shipping fixture](ops/shipping-measurement.json) identifies the effective Linux sources. A [database exercise](ops/storage-roundtrip.json) verified millisecond precision for both running and paused timers.

The open production gateway served 12 verified zone workers after deployment. The verifier reported 0 restarts and zero native, quest or database errors. The stopped backup passed integrity verification. Gameplay main was `1cbdd0c2c7f14f6344032953f05d135397b2f854`. The deployed zone was `82d5e2d2573a440beac75dabce41f9271a20d579ebc9d6bf38a32a6ad0c1c314`. [Independent production verification](ops/production-verified.json) · [Deployment and rollback](ops/README.md).

Promotion went through [dev](https://github.com/frank-grimes-jr/nightcap/pull/458), [test](https://github.com/frank-grimes-jr/nightcap/pull/459), [main](https://github.com/frank-grimes-jr/nightcap/pull/460).

Player combat logs, real RoF2 timing and owner acceptance remain open. The updated wiki articles await publication. [In-game checks](../../combat/thj-aa-duration/QA.md) · [Wiki impact](wiki-review.md).
