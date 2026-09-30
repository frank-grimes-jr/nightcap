# 0047: Scale tier spell/heal additions from base-item strength

Date: 2026-09-27. Status: candidate; gameplay QA pending.

A flat 5/12/20 spell/heal addition lets ordinary low-quality items acquire the
same added offensive/sustain value as powerful loot. That erases progression
when combined across a full multiclass loadout.

For common wearable non-bag items, define strength as the largest of base HP,
mana, AC, twice the largest ordinary attribute, and floor(100 * damage / delay)
for genuine weapons. Clamp strength to 0..100. The added stat is
floor(tier ceiling * strength / 100), with ceilings 5, 12 and 20. Ascended epics
use 20. Read unscaled base rows; do not compound already-scaled tier stats.
Positive native spell/heal retains the established 1.10/1.20/1.35 multiplier,
rounded half up. Preserve negative native values without a positive stamp.

This is a transparent strength proxy, not an estimate of rarity or encounter
cost. It omits haste, resists, procs and focus effects. No flat minimum is used:
weak cloth can receive zero added spell/heal while retaining its other tier
benefits. Required level is unreliable for classic gear and is not the curve.
The existing active spell/heal rules and 250 caps are unchanged; this does not
establish a permanent ceiling or certify encounter balance.

Generate bootstrap formulas, verification SQL and existing-item migration from
one policy. Existing servers get a captured two-column transaction, never a
rebuild of tier items. Guard item names, formula inputs and spell/heal preimages;
preserve unrelated metadata without blocking on irrelevant changes. Verify all
other columns and exact rollback against a full isolated items clone.

Independent frozen-loadout projection estimated Ascended totals of 231 for
WAR/CLR/WIZ, 215 for WAR/CLR/MNK and 214 for MAG/NEC/SHM versus the prior capped
250. These are dated candidate projections, not measured native encounter
outcomes. Preserve historical baseline reports and require representative QA.
