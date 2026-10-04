# ADR 0052: Social gatherings in the East Commonlands tunnel

Date: 2026-10-01. Status: accepted intent; implementation under verification.

The owner rejected straight wall rows and reported missing custom residents.
The live audit found six residents outside the chamber and generic class
merchant names. The first court pass had not reviewed the complete population.

Account for all 119 actors in a complete scene audit. Place class counterparts
in loose inward-facing groups, retaining their matching uniforms and roles.
Give the 16 class merchants individual names while retaining IDs and inventory.
Concentrate supplies and six real crafting stations in a southwest corner;
disperse market traders around the remaining chamber. Move the Chronicler next
to native Shady and put the six named residents in an irregular social ring.
Re-route all eight walkers with varied native pauses. Add silent, staggered
resident gestures while preserving existing dialogue and OOC coordination.

Alternatives considered: keep wall rows with smaller offsets (still reads as a
service queue); scatter every NPC independently (loses class pairing and the
requested tradeskill corner). Small gatherings preserve readable services while
making their orientation and movement social. Native NPC functions and positions
are retained and included in obstacle/terrain coverage.

Use guarded content-only SQL, full-scene terrain checks, exact merchant identity
guards and scoped saved-state invalidation. Keep the deployed native binaries
and all economic/player data unchanged. The picture and tests do not establish
in-game visual acceptance; the release checklist remains explicit.

See [release and exact QA](../releases/tunnel-social-20261001/README.md).
