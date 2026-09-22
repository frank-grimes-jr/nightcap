# ADR 0045: Consolidate tunnel city travel into a rustic alcove

Accepted September 21, 2026 for dev/test and owner QA. Main promotion still
requires the owner's in-game sign-off.

September 22 update: the owner explicitly authorized main promotion and
production deployment before completed manual acceptance. The original scope
and remaining visual/gameplay QA are unchanged; see the production record.

Ten full-size PoK city monuments crowd the classic East Commonlands tunnel.
Replace those ten outbound doors with one human guide, Merrin (999810), and
three native Commonlands props: a lantern at 60% scale, a barrel, and a crate.
Hailing Merrin offers the same ten destinations and exact landings. The twelve
return/PoK books, waypoint discovery and Khalure's druid-ring travel are retained.

Reuse three retired door identities as static, non-teleporting scenery. This
needs no client patch or native rebuild. Copy the complete appearance tuple from
native Bubar (22033), then clear combat, loot and merchant behavior. Place the
guide at server X=-335,Y=-1537,Z=3.75, facing into the chamber. The first proposed
corner placement failed the real map's ground checks; the revised site passed.

Travel uses an exact server-owned route list, the existing MovePC API, 50-unit
3D proximity, base instance, healthy/out-of-combat state, and a five-second
repeat-request guard. This is city transport, not a free expansion unlock or a
replacement for waypoint discovery. Existing portal arrival/pet mechanics apply.

Generate SQL from fresh stopped-target preimages. All guards precede writes;
retain unchanged templates and all twelve books in the guard set. Reject ID,
version, source geometry, landing, engine and trigger drift. Rehearse exact
apply/rollback plus case-only drift and dangling references in disposable MariaDB.
After zone activity, recapture and remove only unambiguous saved state belonging
to this guide in EC instance zero, excluding corpses and zone metadata.
Global guide-reference checks reject installation/rollback when other instances,
zones or corpse metadata would leave dangling references; those rows are retained.

Shrinking the city monuments would retain their mismatched visual style. Using
ten unlabeled plain rocks would make destination discovery worse. The owner
accepted the single-guide alcove instead. Existing optional map-layer city labels
are a known cosmetic legacy; no client files are changed by this release.

Scope, rollout, rollback and manual acceptance: [release guide](../releases/tunnel-travel-alcove/README.md).
