# 0061: Reusable four-for-one item upgrades

Date: 2026-10-12. Status: accepted design; gameplay acceptance pending.

Players need an earned use for duplicate Polished and Exalted items. The owner
selected a reusable combining container supplied free by a tunnel NPC.

Use one four-slot Reforging Box for legacy tier loot and the explicit Classic
zone reward catalog. Four identical units produce one next-tier item; base and
top-tier inputs are excluded. Match legacy families by both ID and name. Align
zone-forge higher-tier costs to four while retaining its three-copy base recipe.
Sixteen Polished copies therefore yield one top-tier item.

Handle combines natively through the existing inventory transaction: lock and
validate preimages, consume inputs, insert output and receipt, then publish
after acknowledged commit. Quarantine uncertain outcomes. Invalid ingredients
stay in place. The NPC only supplies the box and instructions.

Ordinary quest removal/summoning cannot commit consumption and reward together.
A reusable container supports upgrades while adventuring and avoids ingredient
trade returns. It occupies a carried bag slot and excludes container items,
since bags cannot nest. Customized, augmented and evolving inputs are rejected
to prevent silent instance-data loss.

Evidence, activation and rollback: `docs/releases/item-upgrades-20261012/`.
Design acceptance does not imply live deployment or manual acceptance.
