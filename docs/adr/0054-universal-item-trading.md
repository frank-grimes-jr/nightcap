# ADR 0054: Universal item trading and fixed NO DROP resale

Date: October 4, 2026. Status: implemented candidate; gameplay promotion pending.

## Intent

The owner requested removal of all NO DROP requirements, player trading for every
item, and a one-platinum sale value for every former NO DROP item.

## Decision

Apply `Items:FreeTrade` at shared-memory item loading, defaulting to true in the
candidate. Every item receives effective tradable, non-attuneable and transferable
flags. Original SQL definitions remain the provenance for the fixed resale class.
Saved instance attunement remains intact; trade checks and client serializers use
an effective attunement predicate. Preserve lore ownership, equipment eligibility,
inventory capacity, corpse access, and advanced-loot award receipts.

Former `items.nodrop=0` definitions receive a 1,000-copper fixed merchant payout.
Each stack unit counts once; a nonstacked charged object counts once regardless
of remaining charges. Apply this policy both to merchants and player `#sellall`.
Ordinary items retain their existing pricing. Merchant purchases of converted
items have a one-platinum minimum after all modifiers to prevent buyback loops.

The SQL flags are deliberately retained instead of a destructive blanket update:
they preserve provenance, existing SQL-based content curation, and a practical
rollback, and newly imported NO DROP items automatically inherit the policy.
An FV-only rule was rejected because it does not resolve existing attunement,
NO TRANSFER, or exact NPC resale. Changing global merchant modifiers was rejected
because it would reprice ordinary items.

## Consequences

`ItemData` shared-memory layout changes. Deploy the rebuilt world, zone,
shared_memory, loginserver and ucs together, regenerate caches with the matching
loader, and restart all native processes. Do the same on rollback. A rule reload
alone is insufficient; item snapshots must agree with the running binaries.

The native merchant quote uses a shared rate and can differ from the fixed payout.
A merchant-open message states the exact override, and the server sale receipt
contains the actual amount. Native quote accuracy is an explicit QA limitation;
no client patch or ordinary-price change is included.

The universal policy includes 1,464 temporary/summoned former NO DROP definitions
in the October 4 hosted catalog. Repeatable free rewards can now generate currency.
This follows the owner's explicit universal scope; it must be measured during QA,
not silently countered by item exemptions. The 2,479 zero-price/zero-sellrate
merchant-listed definitions are protected by the purchase floor.

See [release scope, evidence and QA](../releases/free-trade-20261004/README.md).
