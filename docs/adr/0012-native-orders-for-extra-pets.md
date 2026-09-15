# ADR 0012: Issue native attack orders to every owned class pet

> Current status (2026-09-15): implemented server/AA/PoK candidates are deployed for live QA; main gameplay acceptance remains pending. See [current status](../status.md). The dated evidence below retains its original scope and is not a current deployment checklist.


Date: 2026-09-12. Status: candidate in isolated diagnostic; not deployed.

## Problem

The extra-pet broadcaster called `NPC::Attack` directly, while primary pets received
orders through the normal range, target, state and AA checks. Native command tests
reproduced 102 damage from four attack requests at 500 units, with NPC AI paused.
The same issue affected qattack. Extra pets received no hate-list orders, and the
handler returned immediately when no primary pet existed, ignoring surviving
extra pets entirely. Summon correctness therefore did not establish valid combat.

## Decision

Share the existing attack/qattack switch in a local handler lambda and invoke it
for the primary pet and each real, owned, non-depopping extra pet. Each pet receives
the existing native checks and hate-list order. NPC AI controls movement and swing
timing. The native differences between attack and qattack range/target handling
are retained. Primary success speech and button updates remain primary-only.
The remaining movement/dismissal command paths are unchanged.

Adding a range check to the direct swing would still permit extra attacks through
command spam and omit the native order/state checks. Disabling extra commands
would defeat the intended multiclass playstyle. Sharing the established order
path provides the intended behavior without a second combat implementation.

## Verification and remaining work

Eight command controls cover attack/qattack at 80/500 units, extra-only ownership,
and ordinary primary-only pets. Four pet-only fights exercise both bosses at zero
and all open-pool AA purchases. These intentionally omit owner support and do not
certify class balance. The diagnostic now records native boss HP changes alongside
client packets because distant actors can be absent from client damage messages.
Nested damage calls are recorded but root HP deltas are counted once.

See `../balance/native-pet-commands.md` for results and exact artifact references.
The source change is limited to `Client::Handle_OP_PetCommands`; the imported
mirror otherwise matches the captured active source. A full fresh-source build,
manual client QA and the remaining pet behaviors are still required.

## In-game QA before promotion

1. With a non-GM level50 MAG/NEC/SHM, summon water633, Necromancer443 and Shaman166.
   In a safe area of Solusek B, issue attack and qattack against a legal target
   roughly 80 units away. All pets should approach and attack through normal AI.
2. Repeat from 500 units. No pet should swing, deal damage or gain an attack order.
   Repeat quickly four times: input frequency must not create extra swings.
3. With only Necromancer/Shaman pets remaining, repeat both commands at legal
   range. They must respond without a primary pet or primary pet window.
4. Check primary-only behavior, sit/stop/regroup transitions, an illegal target,
   a mezzed target, a feared pet, animations without/with the required AA,
   familiar/target-lock pets, and LoS with the corresponding rule enabled.
   These broader state/client checks are not all covered by the eight native cases.
5. Test backoff, follow, dismissal, death, zoning and resummoning separately. This
   change does not repair every extra-pet command or persistence path.
6. Exercise Lord Nagafen in Solusek B and Lady Vox in Permafrost with active owner
   slow/healing/DoTs before selecting release AA pools or numerical balance changes.

Do not promote to main without the owner's in-game sign-off.
