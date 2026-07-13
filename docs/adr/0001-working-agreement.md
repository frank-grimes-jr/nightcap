# ADR 0001: Working agreement — branch flow, commit discipline, documentation

Date: 2026-07-13
Status: Accepted

## Context

Solo hobbyist EQEmu server repo. Many changes touch the live database and compiled binaries, and some features can only be validated by playing the game — automated tests can't cover in-game behavior. Needed: a clear QA handoff point and a durable decision trail.

## Decision

- Branch flow: `feature/<name>` → `dev` (automated testing) → `test` (pause; user runs manual in-game QA from an explicit checklist provided at promotion) → `main` (after user sign-off).
- Claude commits/PRs/merges autonomously up to `test` when tests pass; `test` → `main` needs sign-off.
- Small commits: one system or feature each, with tests.
- Ambiguous tasks: propose 2–3 options with tradeoffs in the PR/commit description instead of silently choosing.
- Docs: CLAUDE.md kept current; significant decisions get a short ADR here; each phase ends with `docs/milestones/phase-N-report.md`; invented lore is tracked in `docs/lore/structure.md`.

## Consequences

- Manual in-game QA is a deliberate bottleneck before `main` — nothing ships on green CI alone.
- Per-phase documentation overhead, traded for an audit trail that survives DB/binary changes git can't capture.
