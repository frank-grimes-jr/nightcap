# 0038 — Native multiclass UI and durable pet armor

Date: September 19, 2026. Status: candidate, pending in-game acceptance.

The owner requested native inventory/AA class presentation, a compact exotic PoK
hub, permanent beneficial buffs, instant player DoTs, eight-slot pet armor, and
melee during casting. The owner explicitly included AA buffs and disciplines in
permanence and selected equip/remove/inspect rather than inspection alone.

## Decisions

Use exact-build client hooks and a separate `nightcap` skin. The original RoF2
directory remains read-only. A signed offline package owns all 13 client files;
the native UI loader selects `nightcap` automatically for existing and new
characters. Both saved and explicit skin-name assignments are guarded hooks;
character-selection UI and native window/hotbar layout handling remain intact.
Inventory and AA metadata are opt-in, bounded, and tied to character/spawn/generation.
AA ownership uses the original ability class mask rather than widened access.

The inventory's Pet Armor tab selects each owned permanent pet by class. Its
eight slots are head, chest, arms, one wrist, hands, legs, feet and waist. A
character/class loadout remains recoverable when a pet is absent or its class is
released; it reapplies when that class's permanent pet is summoned. Existing extra
pet persistence is unchanged: extra pets must be summoned again after zoning.
Charm and swarm pets are excluded. Weapons and jewelry retain native behavior.

Store complete ordinary inventory instances in `character_pet_armor`, with the
same 17 columns as `inventory` plus `pet_class`. Move rows with transactional
INSERT SELECT / DELETE, full binary-safe preimage checks, cursor queue locks,
and no connection retry. Preserve all six augments, charges, attunement, custom
data, color and ornaments. Allocate fresh session serials during load; the saved
serial is only a comparison preimage until removal persists the fresh serial.
This follows ordinary inventory allocation and avoids cross-session collisions.

Any unconfirmed transfer disconnects and quarantines the session: no general
save, subsequent packet processing, disconnect quest or proximity exit callbacks
may overwrite its uncertain cursor. Reconnection loads whichever transaction
state actually committed. Native hand-ins cannot bypass managed armor slots;
automatic loot equipment selection skips slots currently managed by the tab.

Temporary No Rent, evolving/scaling, stackable, quest and NoPet items are rejected.
The first three have additional expiry/state semantics that the ordinary row
cannot safely preserve. This candidate therefore does not support summoned
temporary armor; that limitation is explicit in the release checklist.

Use the engine's permanent buff sentinel internally and the client's permanent
wire sentinel in every affected packet/profile path. Apply to beneficial player
and owned-pet buffs, including AA/disciplines. Death fades beneficial effects even
when their original spell or illusion would persist. Hits, charges, dispels,
click-off, stacking and aura range removal retain their own semantics. Hostile NPC
durations and detrimental spells retain timing. Player DoT detection uses native
duration formulas and negative CurrentHP/BardAEDot effects; mana/reuse remain.

Move the existing 22 PoK services near arrival without changing identities or
stock. Load verified later-era models through the zone-local character manifest.
Generated migrations guard all six table preimages/engines and invalidate only
matching non-corpse instance-0 saved states. FLOAT heading preimages must be
canonicalized to float32 before generating rollback comparisons.

## Alternatives and consequences

AA title prefixes or a web page would avoid native hooks but would not satisfy
the requested column/tab. Full client-owned inventory slots would require a new
inventory protocol; bounded UI commands with server-owned transactions reuse the
existing authoritative item model. Plain item-ID refunds were rejected because
they discard instance state. Restoring cached NPC rows on rollback was rejected
because those rows may be stale; content rolls back and the zone respawns them.

Permanent immunity and AA effects change balance substantially. The earlier timed
AA policy is superseded for this candidate; older balance results cannot certify
it. On September 19 the owner explicitly requested live activation and then
merging everything into main. This authorizes this release before manual
acceptance; the exact gameplay checks in [the release guide](../releases/client-gameplay-20260919.md)
remain open and are not implied by source promotion.

## September 19 refinement: silent client requests

Use the exact-client native channel packet sender for UI metadata and armor
requests, bypassing InterpretCmd and Say's local echo/history. Preserve the
existing server command dispatcher and authoritative handlers. The call target
is signed and guarded with relocated SEH bytes; normal chat/error display stays
unchanged. A new server opcode would require a coordinated deployment without
improving this presentation fix. See [native evidence and QA](../releases/client-silent-ui-20260919.md).
