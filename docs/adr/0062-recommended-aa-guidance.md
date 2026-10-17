# 0062 — Server-selected AA guidance in the native window

Status: accepted design, implementation candidate; 2026-10-17.

New players face a large legal multiclass AA catalog. The owner approved an
optional Recommended filter prioritizing survival, sustain and useful early damage.

The server selects at most ten next ranks from a curated policy using current
ownership, held classes and native legality. The proxy adds a presentation-only
predicate to the existing native filter call, before row construction. It preserves
native selection and purchasing and explains each selected row. A counted atomic
metadata batch is bound to the existing character generation. Missing capability
or identity falls back to the ordinary catalog. No rank or cost changes occur.

We rejected automatic raw-effect/cost scoring: different effects, prerequisites,
skill availability and multiclass interactions do not share a safe scalar value.
We rejected deleting rows after native construction: it risks stale selection and
wrong-rank purchase. A separate web guide would not satisfy the requested AA filter.

The costs are a paired zone/proxy/XML release, a maintained curated list, and
native in-game QA. Starter targets are advisory and never character-level gates.
Scope, source/tests, integration, rollback and exact QA:
`docs/releases/recommended-aa-20261017/README.md`.
