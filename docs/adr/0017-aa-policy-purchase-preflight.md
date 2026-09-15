# 0017: Preflight AA rank policy against existing ownership

Date: 2026-09-13. Status: implemented read-only preflight; enforcement pending.

## Decision

Compile the calculator's candidate ability caps into explicit native rank IDs
using complete stored AA chains and inherited prerequisites. Compare each saved
purchase by its canonical first-rank ID and rank count. Produce an affected-row
report without SQL edits or automatic refunds. Keep native per-character
eligibility and complete expansion scheduling as separate required checks.

## Why

The current era toggle cannot express Nightcap's custom rank caps. Native loading
skips a saved family whose owned rank fails availability; it does not retain a
lower permitted rank automatically. Subsequent saves or purchases can change the
same canonical record. Turning on an incomplete policy without reconciling this
state would risk inconsistent effective power, points and ownership.

## Alternatives and consequences

Using native expansion tags alone is simpler but removes intentional Classic AA
exceptions. Applying the diagnostic combat core immediately would also remove
unreviewed utility from the offering. Keep those alternatives out of the current
rollout; complete the offering and purchase handling before enabling enforcement.

Current table costs support an impact estimate, not proof of points actually paid.
Missing later rank rows do not invalidate existing prefixes because native loading
truncates the chain. The preflight preserves that behavior while rejecting cycles,
ambiguous rank ownership and prerequisite gaps. See the preflight report for
captured counts, source evidence, reproduction and explicit in-game QA.
