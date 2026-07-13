# ADR 0002: EQEmu domain knowledge as a project skill; THJ as replication spec

Date: 2026-07-13
Status: Accepted

## Context

Server knowledge (reload/cache behavior, RoF2 client limits, this build's Perl DB API, THJ's feature set) lived scattered across CHANGES.md entries and quest-file comments. A baseline test showed a fresh agent could reconstruct it, but at ~12 tool calls/4 minutes — and THJ facts relied on sources that now block scraping (wiki) or are private (GitHub org).

## Decision

- Consolidate into a project skill at `.claude/skills/eqemu/` (version-controlled, auto-discovered): `SKILL.md` for EQEmu/Nightcap internals, `thj-blueprint.md` as the durable local record of THJ's systems.
- THJ is treated as the **spec to replicate**, not loose inspiration: the blueprint carries a per-system gap map (Nightcap status vs THJ) and a suggested build order. Deliberate deviations (4 loot tiers, PoK hub, MQ2 allowed) are recorded as such.
- CHANGES.md remains the chronological audit trail; the skill holds only the distilled durable rules.

## Consequences

- Skill content must be updated when systems change, or it rots — treat it like CLAUDE.md under the working agreement.
- THJ facts were assembled from secondary sources (verified 2026-07-13); re-verify against the wiki in a browser before building each system.
- Retrieval verified by test: with the skill, an agent answered the 5-question retrieval set correctly in 2 tool calls (baseline: 12).
