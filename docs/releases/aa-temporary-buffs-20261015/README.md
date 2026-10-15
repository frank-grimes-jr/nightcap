# Temporary AA buff duration repair — October 15, 2026

Status: built and tested candidate. Not deployed; owner gameplay acceptance
remains pending. The approved production content check completed read-only.

## Problem and behavior

The reviewed base source at `1e3bf44897f8dbd32f026c9d37f69d6cd1c2e8b8`
promotes every beneficial player/owned-pet buff to the permanent sentinel in
`Mob::GetBuffDurationForTarget`. The September direct-AA exclusion in
`CalcBuffDuration` was superseded by this blanket policy. Killing Spree is a
passive on-kill effect, so checking only activated `aa_ranks.spell` is also
insufficient.

The candidate keeps native, focus-adjusted durations for direct AA spells,
AA effect procs, and their recursive recourse/trigger descendants. It also
restores finite discipline and short-box durations. Classification uses the
zone's current AA catalog, including unowned ranks, so another caster's buffs
and pet buffs receive the same policy. It validates spell IDs before narrowing,
tracks visited spells/groups to terminate cycles, and follows only documented
spell-bearing operands. Spell groups are resolved as groups, not mistaken for
spell IDs. AA and spell `SpellOnDeath` have different operand layouts.
Missing/empty zone AA data conservatively withholds policy permanence.

Ordinary player/pet blessings retain permanence. Instant spells, detrimental
effects, NPCs, Epic 0.5 limits, native permanent spells, and range-managed auras
retain their existing rules. Positive remaining durations are preserved exactly;
native focus, proc eligibility/chance, cooldowns, ownership and AA costs do not
change. Classification is recomputed when applying/restoring a buff, avoiding a
stale cache after AA or spell reload; it is not performed on each ordinary tick.

Affected finite-formula buffs saved with the policy sentinel `-1000` or legacy
`-1` receive one remaining tick. Their original elapsed time is unavailable, so
login cannot award a fresh full duration. This uses the existing application,
player-load, pet-restore and duration-adjustment policy calls without SQL edits,
recasting, or replenishing charges/runes. Do not restore old player snapshots.
Native `BuffProcess` decrements through zero and fades below zero: a migrated
one-tick buff therefore fades by the second unsuspended processing callback.
Existing zone timer suspension and native fade/recourse behavior remain intact.

## Verification and limits

The regression suite compiles the actual duration policy, graph helpers and
`BuffProcess` with
MSVC against isolated native-shaped dependencies. Before the fix, seven runtime
controls failed: a modeled six-tick on-kill AA returned `-1000`, as did a direct
18-tick AA, with graph/reload/saved-duration cases also failing. The synthetic
six-tick example is not a live Killing Spree duration measurement. The protected
local RoF2 spell file identifies Killing Spree as spell 11023, formula 2, cap 5.
The subsequently owner-approved production content capture at 09:42:58 UTC on
October 15 confirms those values, short-box flag -1, ability 733, and nine AA
rank-effect links with SPA 360 and base2 11023. The native formula yields five
ticks before applicable focus modifiers. All 6,655 ranks, 9,850 rank effects and
40,725 spells were read without player rows or server changes.

Tests: `tools/tests/test_aa_temporary_buffs.py`, `test_gameplay_policies.py`,
`test_epic05_native.py`, and `test_buff_restore.py`. Set TEMP/TMP to a writable
workspace directory if the Windows sandbox cannot access the default temp path.
The balance suite retains its historical September evidence scope. Final results
and reviewed file hashes are recorded in `verification.json`.

All 30 focused checks pass: 19 AA policy/native countdown, two gameplay-policy,
one Epic 0.5, three reconnect/packet compatibility, and five historical duration
evidence checks. Native effects, network transport and fade side effects are
stubbed in the countdown fixture; its actual zero-tick/expiry and suspension
decisions execute. Independent review found and corrected missing cure/charge-
fade/spell-kill edges and failed-catalog handling; no blocking findings remain.

The exact extracted classifier also passes all 2,837 expected related spells
(2,380 roots and 457 descendants), 1,024 sampled nonmembers and six policy
controls using the approved production capture. Arch Shielding and Resolution
remain ordinary blessings. The optimized MSVC fixture averages 1.69–1.73 ms per
classification across three 100-lookup batches. These are Windows fixture timings,
not Linux runtime latency. Captured stored spell rows are assumed valid because
the projection did not include `player_1`. Compact evidence:
[content audit and benchmark](content-check.json).

The local build uses the fingerprinted retained October 13 tradeskill source,
whose baseline `zone/spells.cpp` exactly matches the reviewed Git baseline.
`tools/build_aa_temporary_buffs_candidate.py` verifies all retained sources and
link inputs, compiles the complete modified translation unit with Clang C++20,
links the full zone and resolves all dynamic dependencies. Only spells.cpp and
its object differ. The original zone/source/link inputs remain unchanged.
Candidate zone SHA-256:
`19cd3387952f21d1d1bcc18916e76a1d7738148de086849e3d3befe3a0df2ae1`.
The isolated binary is `/tmp/nightcap-aa-temporary-buffs-build-20261015/zone`
inside local `akk-stack-eqemu-server-1`; [manifest](build-manifest.json).
No running production binary parity, live countdown, client rendering, or owner
acceptance is claimed from build/fixture/content checks.

## Activation and recovery boundary

This change requires a zone rebuild and coordinated runtime restart. AA/rule
reload alone cannot install C++. No new rule, schema, item cache, client binary,
spell export, or ownership migration is required. Retain the current world,
shared memory, signed client and every intervening runtime change. Build from
the freshly verified retained release, not the older default overlay.

Before authorized activation: verify the current production AA/spell links and
finite duration templates; build/link the candidate against the retained source;
record source/link/binary fingerprints; use the current guarded native release
operator with backup, maintenance locks, closed gateway and preservation checks.
OVH native child exits restart the entire game runtime. Do not kill one zone.
Publish signed fix notes only with explicit publication authorization, retaining
all previous assets/history. Reconnect under the candidate normalizes saved
affected buffs. Current active objects are refreshed by the coordinated restart.

Retain the prior image for operational recovery, but it reintroduces permanent
temporary buffs. Preserve current player data and saved finite timers during any
recovery; never restore an earlier database to recover a binary.

## Exact owner QA

1. In East Commonlands, use an existing character that owns legal Killing Spree.
   Record its rank, held classes, focused duration and damage before testing.
   Kill an eligible non-trivial target until the native proc fires, stop killing,
   and verify both icon and damage bonus expire at the native duration. Repeat
   a qualifying kill to distinguish legitimate refresh from perpetual uptime.
2. Repeat with a direct timed AA such as Improved Twincast or Warlord's Tenacity,
   and with an available AA proc/recourse. Verify finite countdown, normal charge
   consumption and unchanged reuse restrictions. Tenacity's native HP drain
   remains: start at safe health and allow it to expire without extra combat.
3. Camp/reconnect and zone while a temporary buff still has time remaining. It
   must resume its saved time, not become permanent or gain a full new duration.
   A previously broken permanent AA effect must expire after its normalized
   remaining tick and normal zero-tick processing (at most two unsuspended buff
   callbacks). Verify its actual combat effect ends, not only the icon.
4. Apply an available temporary pet AA and repeat zoning/pet restore. Verify the
   buff expires and pet bonuses revert. Preserve pet equipment and charges.
5. Verify Matron/Goldwind blessings and ordinary preparation buffs still retain
   their effects through camp/zoning; clicking off and death retain existing
   behavior. Check a discipline, a short-box effect, and a native aura separately.
6. Record any legitimate spell sharing an AA spell identity: it intentionally
   receives the same finite policy regardless of who or what applied it.

Do not grant points or rewrite normal player buffs merely to run these checks;
use explicitly authorized disposable characters for synthetic saved-state tests.
