# Candidate source review — October 30, 2026

Author review, not independent approval. Baseline origin/main f3e9e5ff was
re-fetched and remains the source baseline. Do not infer live state from this
checkout; newer outside-Git public/wiki operations have separate evidence.

## Correctness and regression boundaries

- Actual CalculateExp/AddEXP tests cover pre-AA awards and exclusions; the existing
  369-check AA harness retains its character progression behavior. Item XP is
  additive, except an uncertain inventory commit intentionally quarantines before
  further session mutation. No extra character or AA reward is granted.
- Policy tests cover all levels 1–255, arithmetic overflow, small awards, three
  increasing costs and top-tier stop. Actual native award tests exercise a full
  path, metadata, compatible/incompatible augments, lore custody and dye/instance
  preservation. Faults before a write decline; ambiguous writes or publication
  quarantine. An ambiguous result is never automatically replayed.
- The native failure harness exposed lowercase hex incompatibility with the
  reused Bazaar validator. Only hex spelling is normalized; saved metadata bytes
  remain exact. Native SQL tests and disposable MariaDB tests pass after the fix.
- Actual IsEquipable/IsSlotAllowed methods allow the training projection only
  when enabled. Native Power Sources retain ordinary behavior; removal to an
  inventory slot remains allowed when disabled. SwapItem additionally validates
  complete families, instance state and required/recommended levels in both swap
  directions. Packet projection is not treated as server authorization.
- Actual CalcItemBonuses and GetRawItemAC tests prove training items do not reach
  normal/augment or additive-worn bonus dispatch and add no raw AC. Real Power
  Sources and non-client dispatch retain their prior behavior. Source review also
  covers four item-focus scans, cast/verify gates, login/swap equip events,
  attunement and auto-equip. These are not actual-client visual/click acceptance.
- Existing box/zoneforge rules retain 3/4/4 costs and restrictions. Only valid
  XP-only customization is newly admitted; consumed partial progress is discarded.
  Existing Paladin/Bazaar regression groups exercise actual metadata loading,
  grip projection and native reconstruction with XP plus grip.

## Custody audit

The authenticated candidate source retains custom_data in the common inventory
save/load and CreateItem paths. The reviewed overlay locations are
common/shareddb.cpp (SaveInventory and GetInventory) and zone/trading.cpp
(PutItemInInventory transfers), plus zone/client_bazaar.cpp (Restore). In the
retained complete source, zone/corpse.cpp captures GetCustomDataString at death,
stores it in corpse rows and passes it back through CreateItem on loot;
zone/zonedb.cpp carries custom_data during corpse row reconstruction. Item copy
construction preserves the map. No side table depends on a runtime GUID.

Native metadata, Bazaar reconstruction and SQL tests are automated coverage;
full move/zone/relog/death/direct-trade/Bazaar interaction remains the explicit
in-game QA matrix. Strict preimages deliberately refuse drift instead of silently
normalizing saved state. A real legacy noncanonical row or concurrent change must
be diagnosed rather than bypassing the guard or repeatedly retrying.

## Security, architecture and performance

SQL receives only bounded canonical decimals and validated hex. All persisted
instance fields except regenerated GUID are exact predicates; only identity,
default color and metadata may change. InnoDB, no triggers, autocommit and no
active transaction are checked before writing. Saved GUID remains untouched.
The disposable test database contains synthetic rows, not player data.

Arithmetic, metadata, family validation and guarded persistence are separate
small headers. The award is integrated at the existing combat-XP calculation
boundary, and replacement uses owned ItemInstance data rather than shared cache
mutation. There is no new DB schema or per-item timer. Each eligible award checks
three connection/schema capabilities and performs one UPDATE; family lookup is
four cached definitions. No query is added for an absent/ineligible/top-tier item.
Live load measurements remain distinct from functional correctness checks.

## Open gates

Final full paired build/link is running in an isolated directory and must finish
before release preparation. Independent review is not yet recorded. Real RoF2
placement/effect/custody checks and measured 4–8-hour pacing are owner acceptance
gates. The default-off candidate has not been promoted, deployed, activated or
publicly published. Disabling the rule is the safe stop; reverting to an older
multi-key metadata loader or restoring old player snapshots is not a safe rollback.
