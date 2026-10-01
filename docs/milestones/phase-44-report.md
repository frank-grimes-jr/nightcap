# Phase 44: Pre-character-select material crash

Traced the player's dump to a null material in RoF2's per-actor WLD loader.
Seven models used shared dependencies outside the native prefix filter. Scoped
those material chains without changing mesh/animation bytes, ordered rendering
values, textures or gameplay. Updated generator validation and proxy/packager
contracts; release 2026100103 retains the spell-inspection and advanced-loot work.

[Incident, verification, publication and exact QA](../releases/character-select-crash-20261001/README.md).
Cut: disabling classic models, removing affected races, graphics-driver changes
and server/database changes. Remaining gate: actual character-screen/world entry.
