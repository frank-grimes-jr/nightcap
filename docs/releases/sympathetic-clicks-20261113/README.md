# Classic sympathetic click production release

Main PR 444 promoted the rank I effect from test PR 443 under the owner’s November 13 instruction to push to main and server. OVH ran the scoped migration and a matching zone built from its retained native predecessor. The signed launcher update includes the two spell records and two descriptions. Release source `8f08c7a8d0a10ebd0ac8b5c4c76d4336a1d852dc`. [Main promotion](https://github.com/frank-grimes-jr/nightcap/pull/444).

## Live verification

The OVH process check observed 12 zone workers, 0 container restarts and zero native, quest or database errors. Both admissions and startup health checks passed. The cache has 310,016 item records and 99,002 spell slots. Two of each changed. The signed client kept the other 146 files and verified the public assets. An isolated replay using the four exact shipping gameplay objects activated both items, kept both buffs after unequip and measured Minor Healing at 21 → 22 and Ice Comet at 1,058 → 1,106. [Shipping-engine cast probe](native/cast.json). The two official acquisition routes were observed in the production database. [Production receipt](ops/production-verified.json) · [Isolated full-catalog rehearsal](ops/preflight.json) · [Signed client](client/public-verification.json) · [Canonical wiki](wiki/public-verification.json).

| Click | Existing Ascended item and stock source | Verified item result |
|---|---|---|
| Sympathetic Strike I (44379) | Runed Lava Pendant (610338), lava elemental in Solusek’s Eye | Equip, click and swap back to fighting gear. A qualifying direct-damage gem cast costing at least 10 base mana can add one hit to the original target. |
| Sympathetic Healing I (44380) | Moonstone Ring (610150), frenzied ghoul in Lower Guk | A positive-mana direct gem heal can add a burst to its recipient. Successful worn sympathetic healing takes precedence. The ring keeps Extended Range II. |

## Operation and recovery

Use the immutable production stage and phase receipts in the operations directory. The full production rehearsal exercised forward, repeat, disable, withdrawal with the unused new identities removed, and reapplication. The production operator checks inherited gameplay, all other items and spells, saved state, market, image, admission state, channel, backup and runtime health. An unused-ID inverse is specific to the closed, pre-admission state. After players can acquire buffs, retain the spell identities and saved player data and use an appropriate paired native/client withdrawal. Rehearse any rollback against fresh afterimages. [Operator](ops/release.py) · [Build and tests](native/) · [Paired client recovery](client/README.md).

## Player verification

Exit EverQuest and select **Play** in the Nightcap launcher. Inspect each Ascended item, equip and click it, then swap back. Both buffs should remain visible. Compare an ordinary single-target direct gem cast before and after. A qualifying 40-point heal adds at most 2 and a qualifying 960-point hit adds at most 48 before target protections. Existing worn healing, nonqualifying spells, dispels and lifetaps have separate controls in the [player QA sequence](../../items/sympathetic-clicks/README.md). [Official guide](https://wiki.nightcapgame.org/equipment.html#stock-sympathetic).

The 410 final synthetic dragon encounters measured a 4% improvement to effective healing in the opening minute of the ordinary progression setup on Vox and Nagafen. Whole-fight output varied. Owner gameplay acceptance and the proposed full-encounter 3–5% sustained gain are open. [Balance results](../../items/sympathetic-clicks/balance/README.md).
