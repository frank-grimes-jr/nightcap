# Phase 23 — Client and gameplay candidate

September 19, 2026. Scope: the owner's seven requested updates and explicit
permanent-AA/equippable-pet clarification. Implementation is isolated on
`feature/client-gameplay`; live binaries/database remain unchanged.

Built native inventory class presentation, an AA Class column, an eight-slot
per-pet armor tab with durable item transactions, permanent beneficial buffs
through all load/packet/death paths, instant player DoTs, melee while casting,
and a guarded compact PoK hub using later-era models. Extended signed packaging
from four to thirteen required files. The candidate includes a separate client
copy and a rebuilt Windows launcher.

Verification includes matching world/zone builds, 87 native server tests, native
spell/death and transfer controls, 24 injected transfer failures, full-instance
MariaDB equip/remove and rollback, 26 independent hub database checks, default/QA
Go suites, client runtime controls, eight Chrome UI checks, and visual inspection
of the new activation instruction. Exact scope and evidence are in the
[release guide](../releases/client-gameplay-20260919.md).

Independent review corrected a first-handshake cooldown, AA repaint ordering,
container sizing, item charge/augment reconstruction, serial collisions,
quarantine callbacks, legacy pet hand-ins, automatic loot replacement, and
FLOAT heading rollback preimages. The fresh real-client launch gate caught
absolute SEH operands when Windows relocated eqgame. Narrow HIGHLOW rebasing
was independently checked, and executable tests cover preferred/higher/lower
image bases. Signed release 2026091903 then reached playing with all 11 required
features active (mask 2047) and completed owned shutdown. Earlier failed
generations are retained as diagnostic evidence and are superseded.

No requested feature has been silently replaced with a web UI or AA name prefix.
Temporary/evolving/scaling pet armor is explicitly unsupported because its extra
lifetime/state semantics are not represented by an inventory row. In-game visual,
combat, pet-lifetime and balance acceptance remain open. No live deployment,
main promotion or owner acceptance is claimed.
