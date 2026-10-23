# Phase73 â€” level-scaled AA and level1 allocation

The owner selected two passive AA per level and functional native AA controls
from level1, including100% allocation to pause leveling. The implementation uses
actual level spans, preserves normal XP and saved points/fractions, and retains
valid partial percentages. Full focus earns20AA per current-level-equivalent.

A guarded proxy update changes three native level gates and bounds +/- arithmetic.
Server/profile/command handling now preserves0â€“100%. No client reference files,
AA prices/legal pool, normal XP curve, player records or retired boost changed.

Native awards, SetEXP integration, exact client execution, signed-pair checks,
SQL rehearsal and rollout/publisher failure tests pass. Independent review is
complete. Fresh paired server build, main PR305, production activation, signed140-file client
and wiki467/private-guide5 publication are verified. Native owner acceptance
remains separate and open. Exact scope and QA:
../releases/aa-level-progression-20261023/README.md.

No new boost source is included. Balance at chosen grinding levels and rendered
native control/network/persistence behavior still need the listed in-game QA.
