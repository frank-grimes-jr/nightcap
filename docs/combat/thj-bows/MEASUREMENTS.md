# Ordinary bow damage and heroic DEX

At level 50, the pre-change server added one damage per ten heroic DEX to each landed arrow in every measured AA configuration. It missed the separate ordinary bow percentage documented in THJ's heroic-stat guide. At 100 heroic DEX, the correction raised mean noncritical damage from 29.65 to 34.21 with zero AAs, and from 69.30 to 78.41 with Archery Mastery III and Bow Mastery I. The same 4,740 of 8,192 arrows landed across all 78 level-50 combinations. [THJ heroic-stat guide](https://github.com/P1xt/thj-wiki/blob/main/classes-and-abilities/heroic-stats.md)

| Effective heroic DEX | Zero AA before | Zero AA after | Both before (20 points) | Both after (20 points) |
|---:|---:|---:|---:|---:|
| 0 | 19.65 | 19.65 | 59.30 | 59.30 |
| 100 | 29.65 | 34.21 | 69.30 | 78.41 |
| 200 | 39.65 | 45.88 | 79.30 | 91.76 |
| 250 | 44.65 | 51.42 | 84.30 | 97.84 |
| 300 | 49.65 | 57.17 | 89.30 | 104.34 |

The table reports damage per landed arrow. At heroic DEX 100, Archery Mastery III alone yielded 49.30 before and 58.41 after. Bow Mastery I alone yielded 49.65 and 54.21. At 0, the paired first successful arrow dealt 29 without AAs and 78 with both. At 100 the same rolls dealt 46 and 102 after the fix. Each physical arrow first gained 25% on its eligible portion, rounded down. Archery Mastery then increased that portion and the separate flat effects added their original amounts.

## Diagnostic setup

The fixture compiles complete method bodies from the selected server source. Physical arrows use `DoArcheryAttackDmg`, `DoAttack` or its origin-aware implementation, `CheckHitChance`, `MeleeMitigation`, `ApplyDamageTable` and `CommonOutgoingHitSuccess`. The native methods also calculate heroic ranged flat damage, offense, to-hit, skill damage, held-class membership and damage-table selection. Both JSON receipts fingerprint the source files. A separate run on the shipping parent, whose full attack.cpp SHA-256 was `e281be96887b22908920b9ab36ed5473c405213f4581696f26517faf51a9a082`, reproduced every baseline row and its damage histogram.

Each of 117 cells resets the RNG to seed 1709 and fires 8,192 shots. The ordinary grid uses a level-50 Ranger and level-50 stationary NPC, synthetic 30-damage bow and 3-damage arrow, effective ordinary DEX 150, Archery and Offense skill 200, ATK 0, target defense 420 and mitigation AC 260. These inputs yield offense 250 and to-hit 504. Holding ordinary DEX fixed isolates the direct heroic term. The diagnostic controls criticals, defender avoidance specials, procs and external damage modifiers at zero. It substitutes synthetic items, projectile transit, effective character stats, post-purchase AA bonuses, deterministic random draws, the final damage sink and network services. It exercises source-derived server code in a fixture. Player logs, replication timing, encounter DPS and owner acceptance require separate QA.

The six level-50 loadouts run at heroic DEX 0, 9, 10, 99, 100, 101, 199, 200, 249, 250, 299, 300 and 400. The checker transforms each damage bin from the *measured* zero-AA, zero-heroic control using the independently expressed THJ reference anchors. It verifies the landed counts, total, minimum, maximum, first landed damage and native flat component for every loadout. Interpolation beyond 100 and extension beyond 300 are Nightcap calibration choices. Rounded damage on small hits can stay the same across adjacent heroic values.

## AA inputs

The experiment reads the rank caps from the active Classic policy in the checkout and follows native rank chains in its pinned catalog. Both per-hit families permit Ranger ownership at level 1 and have no recorded prerequisites. The fixture assigns the effective bonuses for the owned rank. See `Mob::ApplyAABonuses` in bonuses.cpp for the SPA 301 and 220 handlers. The AA catalog SHA-256 is `016d335b379c22c759340a233589db17602d306d394af8b02788b0e66cad00ae`. [Era policy](../../../era.json) · [Rank caps](../../../config/aa-policy.json)

| Family | Legal rank IDs used | Incremental prices | Native effect |
|---|---|---|---|
| Archery Mastery, ability 82 | 199, 200, 201 | 3, 6, 9 | SPA 301 at +30%, +60%, +100%. The rank-III profile spends 18. |
| Bow Mastery, ability 878 | 1196 | 2 | SPA 220 adds 20 for Archery only, skill 7. |
| Endless Quiver, ability 84 | 205 | 9 | SPA 251 preserves ammo. It was unpurchased in the measured per-arrow profiles. |
| Trick Shot, ability 557 | 1608, 1609, 1610, 4989, 4990, 4991, 7378 | 3, 6, 9, 6, 6, 6, 3 | SPA 347 adds 2% to 14% double ranged attack. Requires Archery Mastery III. It was unpurchased in the per-arrow profiles. |

Every profile compares one physical arrow per attempt. The zero-AA Ranger, Archery Mastery I/II/III, Bow Mastery I and combined profiles spend 0, 3, 9, 18, 2 and 20 points respectively. These are checkout-policy and retained catalog results. The experiment did not purchase AAs on a player.

## Controls

- At level 51 and 100 heroic DEX, a stationary unrooted target took 51.97 per landed hit from a primary Ranger and 30.99 from a Bard holding Ranger before the fix. Both averaged 61.74 afterward. With a moving or rooted target, both averaged 30.99 before and 35.87 after. The class-gate benefit is visible in this separate above-Classic-cap control.
- Immediate physical damage and deferred impact agree in every measured cell. The delayed fixture captures resolved launch damage and supplies the bow/arrow item IDs to the impact call, with neither item equipped at landing.
- Skill-origin archery, scripted bow damage without launch provenance, throwing and NPC shots reproduce the corresponding pre-change rows. A controlled Headshot replacement deals 1,000 plus the original flat term, 1,010 at 100 heroic DEX and 1,030 at 300. The fixture forces that outcome and makes no claim about Headshot proc frequency.

## Reproduce

From this checkout, run the measurement driver with a baseline source checkout, then the candidate. Its output includes rank costs/effects, original-file SHA-256 values and all samples. Each run includes the cross-product and control assertions before it writes the receipt.

```powershell
python docs/combat/thj-bows/measure.py --source <baseline-checkout>/server-mods/code --output before.json
python docs/combat/thj-bows/measure.py --source <candidate-checkout>/server-mods/code --output after.json
```

[Before](before.json) · [After](after.json) · [Measurement driver](measure.py) · [Controlled dependencies](bow_boundary.cpp) · [In-game QA](QA.md)
