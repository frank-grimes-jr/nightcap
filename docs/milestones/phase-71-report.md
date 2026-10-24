# Phase 71 — Build Lab

Built a browser-local wiki diagnostic workbench with A/B builds, a small pinned
spell library, effective stat and Hunt item differences, custom resolved actions,
mana/healing/DPS results and cast visualization. Priority search enumerates all
orders for at most six enabled attacks, holding healing behavior fixed.

Kept full gear/AA/pet derivation, native boss AI, RNG/resist behavior and global
build optimization outside this release. These omissions are explicit in the UI.
The initial controls are dated diagnostics, not current legal loadouts.

Proof:12captured native spell-value controls, scheduler/import/optimizer scenarios,
35Python checks (26pass/9POSIX-only skips), existing search/equipment/experience
checks and real browser320/768/1024/1440 layouts. Strict production CSP was tested
locally. No gameplay balance acceptance follows from these checks.

Release, impact review and publication: `docs/releases/build-lab-20261022/`.
