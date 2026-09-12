# ADR 0005: Resolve equipped balance inputs through an isolated engine harness

Date: 2026-09-12
Status: accepted; first equipped-stat diagnostic validated, full encounters pending

## Context

Nightcap combines multiclass HP/mana and skills with custom item stats, worn
effects, focus, and AAs. A gear row sum cannot represent all of these accurately.
Reimplementing every inventory and bonus path before running a fight would delay
feedback and introduce a second large implementation to maintain.

## Decision

Use a separate native diagnostic executable for resolved character inputs, while
retaining the seeded Python event runner and differential formula controls.
The first diagnostic uses the existing mock Client constructor, captured legal
Human creation allocations, synthetic multiclass rows, maximum eligible skills,
real item instances, and CalcBonuses. It reports the existing 20-slot candidate
sets with no purchased AAs or active buffs. This does not certify combat BiS.

The harness has its own content-only database, database-scoped test user, empty
player/account tables, runtime directories, and generated shared memory. It must
refuse a live runtime/configuration before the original zone startup runs.
The copied main disables world/QueryServ startup connections and returns from
the diagnostic without entering the normal server loop. Production source,
build outputs, binaries, and processes remain untouched.

The normal quest-plugin compatibility gate is disabled only in the copied
diagnostic startup because its quest/plugin directories are empty. Quest-driven
item changes or encounter behavior are outside this initial diagnostic.

The first build reuses existing native object files and pins their hashes along
with the new harness, modified startup copy, flags, and executable. This proves
behavior of that artifact, not a fresh rebuild of all current source files or
parity with every running zone. Source freshness and in-game QA remain explicit
gates before using the results for a tuning promotion.

## Alternatives and consequences

- A complete Python port would make repeated sweeps easy but duplicate a large,
  stateful bonus/AA implementation. Keep small verified arithmetic ports; avoid
  treating an expanding collection of guessed inputs as a character.
- Tests against live PEQ would reduce setup time but zone initialization can write
  state. An isolated clone preserves production behavior during experiments.
- A full new native build provides stronger source provenance. The initial
  artifact reuse shortens the feedback cycle; it cannot claim that stronger proof.

The first 12 native HP/mana results match the calculator and seven early-refusal
checks pass. Next gates are legal AA/buff setup, acquisition and
combat objective coverage, complete boss mechanics, sensitivity runs, and focused
in-game QA. No cap or NPC HP change follows from the harness alone.

## AA follow-up (2026-09-12)

Resolve the requested 0/100/200/500/all comparison through the same isolated
native engine. Export native use/level eligibility and effect/prerequisite data,
construct explicit ordered purchase candidates, then require native purchase
acceptance, exact cost accounting, and post-purchase completeness checks. Use
native `SetAA` after `CanPurchaseAlternateAdvancementRank`, deduct costs, and
calculate bonuses without UI, quest, title, logging, or persistence side effects.

Zero means zero spent points, with common purchasable free ranks held consistently
at all budgets; keep the previous completely empty-AA report as a separate
control. Grant-only rewards require their own acquisition evidence. Candidate
offense/sustain/defense and durability-first paths expose allocation sensitivity;
neither path is declared optimal until encounter measurements support it.

The first harness actually used base-class caps despite its earlier held-class
description. Corrected diagnostics take held-class maximum trained skills and
native specialization rules. Practical skill attainment, client access, and
base-class-only runtime paths remain explicit QA gates. Purchased AA inputs and
HP/mana now pass 24 native scenarios; this does not establish activated combat
effects or full fight outcomes. See `docs/balance/native-aa-stats.md`.
