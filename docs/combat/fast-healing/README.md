# Fast direct healing — November 20, 2026

Deployed to production and verified on all12zone workers. Public wiki publication also verified. Owner authorized test promotion, main merge and production deployment after validation in the current chat. Visible player acceptance is separate.

## Behavior and scope

Stock Minor Healing (200) and Light Healing (17) receive at least one healing point per effective Heal Amount on an original player direct cast. The existing item bonus is retained whenever larger. The existing spell-level eligibility, item-mod opt-out and Heal Amount cap remain in force. Incoming healing modifiers, criticals and heroic WIS retain their existing order.

This is gated by the existing NightcapTHJBehaviors rule, independently of whether heroic scaling is enabled. Ordinary spell-gem casts and qualifying original activated-AA delivery use the existing source receipt; procs, item clicks, combat skills, reflected effects, ticks, duration hybrids, NPCs and other spell IDs do not gain the floor. No new rules, content definitions, client assets or caches. Custom content is untouched. Healing (12), Greater Healing (15), runes, HoTs and damage retain their existing formulas. The reviewed two spell IDs remain supported as expansions release; later spell additions require explicit review.

At 100 HA without other modifiers, Minor Healing rises40→120 and Light Healing130→165. Greater Healing stays700. At750HA the corresponding values are170→770,552→815, and2975 unchanged. High-HA Minor Healing becomes much more mana-efficient; cast/recovery time and interruption still limit emergency throughput.

Sympathetic Healing remains one twentieth of the largest resolved direct heal, rounded down, capped48. It applies once after the ordinary cast and normal overheal limits apply. Worn healing retains precedence. The added sympathetic result does not re-enter the new floor.

## Validation plan

1. Extracted actual-method regression: confirm original failure then positive floor, Greater Healing and unrelated/custom IDs unchanged, delivery source gates, item opt-outs, level restrictions, NPC/tick/duration exclusions, crit and heroic ordering.
2. Reproduce current shipping zone289df4f2 exactly, compile only effects.cpp, link candidate against authenticated retained objects. Isolated paired native measurements use production caches and rules, Palwar's saved gear, legal endgame gear, and a clearly labeled750HA stress injection. Synthetic cases do not imply owned-AA or real-client acceptance.
3. Exercise actual timed-cast completion under controlled hit counts and Channeling175/200. Record attempted/landed casts, healing and charged mana with sympathetic on/off. These are controlled Channeling/delivery tests, not full NPC encounter/pathing/fizzle simulation.
4. Verify native sympathetic application, overheal and worn precedence. Run existing sympathetic delivery, heroic source and spell-scaling suites.
5. Promote feature→dev→test; preserve concrete player QA below. Main/deploy only after release validation. Verify immutable zone identity, unchanged world/client/caches/rules, all12workers and runtime health. Rollback selects prior image; never restore a player snapshot.

## In-game QA on test/live

Validation evidence: `validation.json` records144 matched pressure cells and28,800 attempted casts per binary. Complete Healing/Greater Healing rows and all18Paladin proc cases match. Native results with saved Palwar gear (no earned AAs) are Minor42→115, Light137→169, Greater742 unchanged. Full legal healer gear is Minor125→531, Light409→587, Greater2208 unchanged. At487HA, Minor's calculated uninterrupted healing including sympathetic/recovery is185.67HP/s versus Light176.0; Greater remains501.33. Spell Haste II benefits Light but not Minor. Cheap-heal mana efficiency rises intentionally; full encounter and owned-AA acceptance remain open.

Baseline zone289df4f2 reproduces exactly; only effects.cpp changes in the shipped native binary. All6focused regression tests and independent review passed. The19wiki tests and search tests pass; the public Inventory predecessor reproduces and only Combat, Equipment, Change Log and search change.

Use level50 Palwar in the Arena for controlled casting, then a single ordinary Lower Guk ghoul and a separate Lady Vox attempt in Permafrost. Record exact gear/HA/heroic WIS, Channeling, buffs and AAs. Compare the same target's missing HP; distinguish crits and overheal.

- Cast Minor Healing, Light Healing, Healing and Greater Healing with sympathetic off, then Moonstone Ring's sympathetic buff on. The first two improve with positive HA; the latter two match the predecessor. A fully landed cast gets at most48 extra sympathetic healing, once. An interrupted cast gets neither heal nor sympathetic bonus.
- Repeat self and another player as recipient, low missing HP, and full missing HP. No overheal exceeds maximum HP.
- Compare Channeling175/200 and Djarn's Amethyst Ring on/off. Spell Haste II reduces Greater Healing3s→2.55s and Light Healing2s→1.7s; it does not qualify Minor Healing's1.5s base. This release does not change haste or interruption formulas.
- During ordinary and raid melee, record success/interrupts, effective HP restored, mana spent and survival. Movement/stun failures remain separate from hit-based Channeling. No promise that every heal can be channeled.

## Wiki impact

Combat and Change Log require updated guidance. Equipment requires a short link explaining the distinction between healing focus and spell haste. No item catalog values, NPC/zone definitions, custom rewards or commands change. Preserve current published Inventory documentation and all unrelated pending guide changes. Historical review-ledger drift is not approval to advance unrelated fingerprints.

## Deployment record

Gameplay passed dev PR495, test PR496 and main PR497. Main PR498 records the explicit owner-approved admission-drain action. Stage `fast-healing-20261120-v2` deployed zone `35330918b99b33b6a0d02fe3da6d3950ab4d97b6a9438c15e64bf2fa65db70d9`. The fresh stopped backup, saved-state/market checks, all12workers, unchanged rules/current Guise cache/signed client and reopened access verified. No player snapshot was restored. V1 was preflight-only and never activated. See `production-verified.json`.

Wiki20261120-fast-healing-v1 verified631canonical files and private exclusions;627outputs preserve the public Inventory predecessor exactly. Linux publisher tests and pointer rollback rehearsal passed. The gameplay runtime and client channel stayed unchanged during publication. See `wiki-public-verification.json`. Historical unrelated wiki source drift remains flagged; the global ledger was not advanced.

For recovery, hold admissions and use a fresh guarded binary-only release based on current service/DB state, selecting the retained predecessor image from `cache-pins.json`. Recompute the native saved-state/market boot expectations and take a new stopped backup before a restart. Never replay a terminal activation or restore the old player snapshot. The retained predecessor executable reproduced exactly before candidate compilation; operator behavior follows the tested backup/drain/recovery guards in `docs/releases/thj-combat-20261113/ops/`.
