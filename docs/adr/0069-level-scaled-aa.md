# Level-scaled earned AA and native percentage allocation

Accepted design: October 23, 2026. Implementation candidate; deployment and owner
acceptance are recorded separately in the release folder.

The owner rejected a fixed high XP cost that made low-level AA impractical and
selected two earned AA per normal level, native AA controls from level1, and the
ability to hold a chosen level while grinding AA.

Keep the installed PEQ normal leveling curve/rates. The compiled opt-in rule
AA:LevelBasedPointsPerLevel defaults to0; candidate production value20 combines
with the retained10% passive policy to earn2AA per level at0% allocation. At100%,
normal XP stops and20AA are earned per current-level-equivalent. Intermediate
percentages retain their normal share and blend passive/focused AA;50% yields
11AA and half a level for one level span starting at that level's beginning.
Crossings are segmented by actual native thresholds. Eligible modified normal
XP is the common basis, avoiding a second AA-only multiplier.

Keep AA:ExpPerPoint at1000000 as a stable storage denominator, not a new fixed
leveling-XP price. Changing a character's level must not reinterpret saved AA
fraction. Preserve points, purchases and valid0–100 selections; a full AA wallet
must not silently resume leveling. No retroactive grants or character migration.

Patch only the pinned RoF2 AA allocation gates via the signed proxy/catalog.
Three level thresholds are guarded; native +/- arithmetic is bounded for valid
non-ten-percent selections. The native notify path still submits the change.
Protect the reference client and avoid broad level spoofing.

Alternatives rejected: a flat XP-per-point cost cannot meet low/high-level pacing;
a changing stored denominator risks saved-fraction reinterpretation. A binary
on/off focus violates the requested partial controls and level-hold behavior.

A new rule catalog requires fresh matched world/zone/shared_memory binaries.
Rollback must preserve percentage-aware binaries after client exposure: the old
zone turns every positive percentage into100%. Fail closed, retain current data,
and use an explicitly reviewed compatible fallback rather than restore snapshots.
See docs/releases/aa-level-progression-20261023/ for native/SQL/client tests,
source provenance, guarded operator, publication state and exact owner QA.
