# Native equipped-character diagnostics

Date: 2026-09-12. Candidate loadouts, not certified combat BiS or full boss fights.

The native diagnostic resolves the existing 20-slot sets through actual Client
inventory and bonus calculations. It uses level-50 Human agnostic characters,
database creation defaults, base-class maximum skills, no purchased AAs,
and no active buffs. Worn effects participate in CalcBonuses; clicks are not used.
Quest-driven item changes, procs, and complete combat are outside this first run.

Correction from the AA follow-up: this first harness did not resolve maximum
held-class skills and did not enforce specialization limits. Its resource
comparisons remain recorded controls; use `native-aa-stats.md` for corrected
skill ceilings and the AA progression diagnostics.

| Build | Tier | HP | Mana | AC sum | Avoidance | MR | FR | CR |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| WAR/CLR/WIZ | Base | 3,525 | 2,662 | 465 | 431 | 131 | 77 | 77 |
| WAR/CLR/WIZ | Polished | 4,135 | 3,314 | 526 | 432 | 160 | 96 | 96 |
| WAR/CLR/WIZ | Exalted | 4,640 | 3,907 | 577 | 433 | 184 | 111 | 111 |
| WAR/CLR/WIZ | Ascended | 5,902 | 4,707 | 640 | 439 | 257 | 158 | 158 |
| WAR/CLR/MNK | Base | 3,360 | 2,385 | 465 | 431 | 99 | 52 | 52 |
| WAR/CLR/MNK | Polished | 3,913 | 2,930 | 521 | 433 | 117 | 58 | 58 |
| WAR/CLR/MNK | Exalted | 4,354 | 3,405 | 571 | 434 | 130 | 64 | 64 |
| WAR/CLR/MNK | Ascended | 5,542 | 4,099 | 632 | 440 | 176 | 87 | 87 |
| MAG/NEC/SHM | Base | 2,669 | 3,291 | 358 | 378 | 92 | 83 | 76 |
| MAG/NEC/SHM | Polished | 3,148 | 3,935 | 382 | 379 | 102 | 90 | 81 |
| MAG/NEC/SHM | Exalted | 3,591 | 4,473 | 406 | 381 | 120 | 105 | 93 |
| MAG/NEC/SHM | Ascended | 4,437 | 5,832 | 436 | 387 | 170 | 147 | 129 |

AC sum and avoidance are server combat inputs, not the client's displayed AC.
Separate block/parry/dodge/riposte checks are not condensed into this avoidance
value. All these sets have zero worn shielding. The earlier Nagafen control's
600 avoidance and 35 shielding belonged to its artificial defender; do not reuse
those values for these equipped characters.

Effective spell damage/healing amounts are 0/100/240/250 across the four tiers.
Ascended raw 400 is clipped at 250. No cap change was made or recommended.

## Verification and provenance

- `native-equipped-stats.json`: native outputs and resource components.
- `native-resource-check.json`: all 12 HP/mana pairs match the verified Python
  formulas with resolved native stats/bonuses and frozen base data.
- `native-build-manifest.json`: executable, harness, modified startup, flags, and
  129 object/archive hashes. Objects are reused from the existing build; this does
  not establish a fresh build of all current source or every live process's binary.
- `native-runtime-manifest.json`: hashes of actual inputs, outputs, executable,
  and isolated item/spell caches. Credentials are excluded.
- `native-clone-manifest.json`: content export hashes and table coverage. The
  captured clone has 237 table schemas and zero account/character rows.
- `native-guard-check.json`: seven preflight refusal checks pass before startup.
- `native-db-isolation-check.json`: the test account can access the isolated
  database, its account/character_data tables remain empty, and live PEQ access
  is denied by database permissions.

The isolated database is `nightcap_balance_20260912`, with a dedicated test user.
Runtime files live in `/tmp/nightcap-balance-20260912` inside the server container.
No live world/zone process was restarted and no production source or binary was
replaced. The normal quest compatibility gate is skipped only in the copied
diagnostic startup; its quest/plugin directories are empty. The cache builder
requires `shared_memory: "shared/"` with a trailing slash in this build.

Purchased AA resource diagnostics are now in `native-aa-stats.md`. Remaining
work includes AA activations, buffs/clicks, pet and weapon combat, full
NPC casting/control mechanics, combat-oriented BiS selection, and balance sweeps.
The overall user goal remains active; these diagnostics establish equipped inputs.
