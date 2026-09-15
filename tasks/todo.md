# Current multiclass and release queue

Updated September 15, 2026. [Full status](../docs/status.md) and
[exact live QA](../docs/releases/live-qa-20260915/QA.md) are authoritative.

## Deployed, awaiting owner QA

- [x] Canonical skill-cap repair and value-1 lifecycle implementation.
- [x] Combined server/AA candidate and matching world/zone deployment.
- [x] PoK hub, class status, native-class merchant routing and bag pricing.
- [x] Durable level-1 AA XP rule and scoped saved-NPC-state cleanup.
- [ ] Complete per-feature live QA, including AA persistence/release/reconnect.
- [ ] Complete all-class/held-slot skill, equipment and trainer acceptance.
- [ ] Obtain owner sign-off before main gameplay promotion.

## Still open

- [ ] Client equip/Skills/trainer gates (#13/#36).
- [ ] Original M1 stats/regen acceptance (#11).
- [ ] AA title remedy preserving owned/system abilities (#16).
- [ ] Structural spell-tooltip/per-character access (#17).
- [ ] Bard movement/song reproduction and fixes (#19).
- [ ] Launcher and release-hardening work (#14/#15).
- [ ] Augment content (#26), full waypoint acceptance (#32), AA column decision (#4).
- [ ] Public site deployment and browser verification (#23).

The skill policy is unlock at native level with value 1, followed by ordinary
use/training. Monktest is the scoped capped-skill fixture; leave Done unchanged.
An interim gameplay pass does not satisfy final launcher/clean-install acceptance.
