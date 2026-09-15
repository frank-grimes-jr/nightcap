# 0013: Measure pet support with native resources and fixed combat gems

Date: 2026-09-12. Status: diagnostic implementation; release policy not approved.

## Context

Passive-owner pet fights do not represent a prepared MAG/NEC/SHM solo strategy.
AA totals alone do not describe the power of purchased pet passives, healing,
spell focus, activated abilities or expansion-specific rank availability.

## Decision

Extend the existing isolated pet controller with native preparation, resource
recovery and an explicit eight-gem support rotation. Keep gear fixed across
0/100/200/500 requested-point allocations and the unrestricted purchase closure.
Record actual expenditure and label the unrestricted closure as a stress test.
An expansion's eventual "all" baseline is its curated legal pool, not that closure.

Use actual per-spell timers, completed buff rosters, resource snapshots, native
spell and pet AI processing, and bounded position packets. Record failed casts
and terminal outcomes. Validate movement and boss HP loss independently of client
damage packets, which can omit distant pets. Preserve existing controller behavior
and compare old command/ownership/caster/monk reports by their exact raw hashes.

## Consequences

The result can identify progression and strategy sensitivity without fabricating
damage multipliers or resource replenishment. It cannot certify optimal play,
obtainable full BiS, all pet commands/persistence, or fresh complete-source parity.
Continuous kiting, pet resummoning and a complete activated-AA rotation remain
outside this controller. [Evidence and explicit QA](../balance/native-pet-support.md)
must accompany future test promotion. Numerical tuning and the final expansion
AA pool require broader evidence; main still requires owner sign-off.
