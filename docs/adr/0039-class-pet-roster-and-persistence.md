# ADR 0039: One persistent pet per held class

Status: tested QA candidate; September 19, 2026. Native checks and independent
review pass; owner acceptance remains open.

## Problem

The client has one pet window, while Nightcap needs three concurrent class pets.
The previous implementation assigned summon ownership from globally widened
spell class columns, treated the primary pet differently, and saved only that
pet. Changing class order could assign a Mage summon to a Shaman or Warrior.

## Decision

Generate a checked immutable catalog of summon spell eligibility from the
preserved original RoF2 spell file (SHA256
`bae7ba7d897962f67581e3e731b94f4a31898d160c30c2edb74912b21aa11880`).
The catalog contains 547 spells with summon/familiar effects. Unknown spells
fail closed; new custom summon spells require a reviewed catalog update.
Original item/AA-only summons consume the primary held class slot. Shared
class spells initially select the first eligible held class at its original
level. Persisted pets keep their original class identity.

Register every permanent class pet by class ID. `GetPetID()` selects a single
window representative; it does not imply the character's primary class.
Prefer a combat pet over a familiar. Repeated summons from an occupied class
slot leave the existing pet intact. Charms and target-locked temporary pets
retain the native exclusive path.

Send one ordinary pet command to each validated registered NPC through the
same native implementation. Resolve toggles once from the representative.
Keep range, line-of-sight, fear, mez, animation, familiar and AA restrictions.
Attack remains an AI order, not a direct damage call. Armor resolves by the
same class registry, using the existing eight-slot item escrow.

Select the RoF2 window with the existing OP_Charm packet after spawn creation
and representative changes. Exact client disassembly verifies opcode 0x5D92,
handler 0x4B74E0, and the selected pet field at owner spawn +0x2B4. This packet
changes client selection; it does not charm the server NPC. Only the selected
pet sends window buffs, HoTT and pet-target updates. HP updates retain each
spawn's ID and remain available for every pet.

## Persistence and lifecycle

Reuse the existing integer pet keys in all three pet state tables:

| Key | Meaning |
|---|---|
| 0 | Legacy active pet, read for migration |
| 1 | Legacy suspended minion, read for migration |
| 2–17 | Active pet class ID + 1 |
| 18–33 | The single suspended minion's class ID + 17 |

Save all state tables in one checked InnoDB transaction, with no reconnect or
statement replay. Load from one consistent snapshot. Refuse nested transactions.
A failed or uncertain database operation disconnects the session and prevents
an empty or stale roster from overwriting durable state.

Restore native pet equipment and buffs, then apply escrow armor, then restore
HP and mana against the armored caps. Escrow item IDs are never also saved as
native pet equipment. The underlying equipment remains available when armor is
removed. Suspend Minion recalls its saved class when that class slot is free;
otherwise it retains the native one-suspended-pet limit.

Owner death removes all active summoned pets. Familiar fade and reclaim remove
only the affected pet. Successful class release removes that class's active or
suspended pet after the class transaction commits; armor stays recoverable.

## Rollback and validation

This requires matching server overlays and a full rebuild. An older binary's
save path deletes all extended keys; back up all three pet state tables before
rollback and do not treat binary rollback alone as preserving extra pets.
No launcher update is required for these server behaviors.

The native matrix covers class and summon-order permutations, duplicate
prevention, shared commands and native AA gates, representative loss, save/load,
suspension, separate armor slots and underlying gear. Actual client rendering,
zone transitions and player-death behavior still require the release QA steps.

[Native evidence and exact owner QA](../releases/multiclass-pets-20260919/README.md).
