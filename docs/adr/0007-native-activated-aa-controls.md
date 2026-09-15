# ADR 0007: activate purchased AAs through the native casting lifecycle

Date: 2026-09-12. Status: accepted for the isolated balance diagnostic.

## Context

The level-50 AA progression matrix purchased legal ranks and applied native
passive bonuses, but did not activate abilities. Assuming an owned ability
works, or adding its advertised effects as flat bonuses, would miss target
restrictions, shared timers, charge consumption, and interactions with Nightcap's
self-buff duration changes.

## Decision

Use `Client::ActivateAlternateAdvancementAbility` and normal `Client::Process`
for an explicit supported set: Improved Twincast, Frenzied Devastation,
Warlord's Tenacity, Celestial Regeneration, and Divine Arbitration. Require the
highest actually purchased rank and native eligibility. Initialize persistent
timers with the synthetic character ID. Every process begins cooldowns-ready;
it does not load cooldowns persisted by another scenario.

Record native casting state, cooldown before/after, HP, mana, maximum HP, buff
slots, duration and charges. A void activation request is not success: require
a newly started cast or native cooldown. Capture failure-message IDs in AA mode.
Timed probes deliberately request shared/repeated cooldowns. Encounters request
each selected ability at most once: Twincast, then Frenzied Devastation, then the
selected sustain AA below 80% HP. Preserve the existing 250-ms reaction and
native recovery/casting restrictions. Exclude Arbitration from the solo rotation;
retain it as a no-effect control.

Keep the original encounter controller when no activation policy is supplied.
Do not change production spells, buff rules, cooldown groups or NPC stats to
make a diagnostic succeed. Existing server behavior, including undesirable
behavior, belongs in the baseline until separately reconciled and tested.

## Alternatives and consequences

- Flat effect multipliers would be simpler but hide important native restrictions.
- Activating every owned AA indiscriminately would include group-only effects,
  conflicting cooldowns and inappropriate timing. Explicit policies are auditable,
  though they are not proven optimal rotations.
- Retain native target restrictions and long self-buff duration for this capture.
  Fixing them within the calculator would test a different server silently.

The controls reproduce a level-gate rejection for Celestial Regeneration and
long-duration Tenacity/Twincast interactions with permanent self-buffs. Those
need separate gameplay reconciliation. See `docs/balance/native-activated-aa.md`.
