# Client gameplay update, September 19, 2026

## Accepted intent

Implement the owner's seven requested changes against the working local QA
patcher baseline (19d4db7), in an isolated feature checkout. The September 19
clarification explicitly includes AA buffs and disciplines in permanent buffs,
and requires equipping, removing and inspecting armor for each owned pet.

## Behavior and acceptance

1. Inventory displays primary, second and third classes from authoritative
   character state, with empty slots identified and no stale data after switching
   characters, zoning, selecting or releasing a class.
2. The native AA lists gain a real Class column. Shared abilities list their
   eligible classes; a general ability is not arbitrarily assigned to one class.
   Sorting, selection, purchase, descriptions and all four tabs retain their behavior.
3. PoK class selection and the sixteen class merchants form a compact reachable
   hub near arrival, with nearby utility services and post-Velious models.
   Preserve quest identities, stock, prices, collision clearance and zone states
   outside the affected non-corpse instance-0 NPC set. Guarded apply and rollback
   must use fresh preimages, not replay the September 15 migration.
4. Beneficial buffs on players and their owned pets have indefinite duration and
   no countdown, including AA buffs, songs and disciplines. Death removes them,
   including normally death-persistent effects. Dispel, click-off, stacking,
   hit/charge consumption and aura range removal still apply. Duration does not
   turn instant heals into ongoing buffs. Hostile NPC buffs and debuffs keep their
   normal timing. Existing duration/balance reports are historical evidence and
   cannot certify the new policy.
5. Player-cast damage-over-time spells have zero cast time in both server behavior
   and client presentation. Mana, target restrictions, resist checks, reuse and
   recovery remain enforced; ordinary direct damage and hostile NPC casting retain
   their current behavior.
6. Pet armor UI has eight slots: head, chest, arms, wrists, hands, legs, feet and
   waist. Each owned permanent pet is separately selectable. Equip/remove/inspect
   round trips must enforce ownership, distance, combat restrictions, legal slots,
   cursor/inventory capacity and instance preservation; failure cannot duplicate
   or destroy an item. Charm/swarm pets are excluded from durable player equipment.
7. Player melee attack rounds continue during casting, retaining attack timers,
   range, facing, stun/mez/fear/death and other existing combat restrictions.

## Implementation order and proof

Start with duration, cast-time and melee server changes and native regression
controls; then guarded hub migration; then server-to-client state and native UI
integration, pet transfer/persistence and signed patcher packaging. Client memory
hooks must use the exact supported executable and verified instruction boundaries.
The UI/protocol and pet item transactions are the highest-risk work.

Tracked C++ overlays live in `server-mods/code`; full build input comes from the
existing EQEmu tree in a separate build directory. Use tabs for C++. Client hooks
live in `eq-client-dll`, signed asset delivery in `eq-launcher`. Content planners,
tests and packet checks belong in `tools`. Add focused behavior tests before each
implementation, compile affected native targets, run relevant suites, review the
diff independently and record exact owner in-game QA and rollback instructions.

The original `Client_RoF2_Dev` is read-only. Produce a QA asset generation and use
a disposable client copy. Do not overwrite unrelated dirty work, modify vcpkg,
publish a release, or claim in-game acceptance. Promotion follows feature → dev
→ test with explicit QA; these new changes need owner sign-off before main.

## Explicit alternatives

Real native UI integration is chosen over name prefixes or a separate website:
it meets the requested surfaces but requires ABI verification. Permanent buffs
include AA/disciplines as explicitly selected by the owner despite the prior
timed-AA balance policy. Pet armor uses eight physical armor slots rather than
eight arbitrary inventory items, preventing weapons or duplicate wrist slots
from silently expanding the requested armor cap.
