# Classic gameplay fixes · November 27

| Report | Change | Verification |
|---|---|---|
| Cazic Thule | NPC 72003 in Plane of Fear now targets level 55, 24,000 HP, 85–218 base melee damage, a 3.2-second base attack delay and 13 HP per regeneration tick. His own spawn removes Avatar Power. Invoke Fear, Panic, assist calls and the loot table remain active. | Twelve baseline deaths and 20 native candidate encounters with level-50 characters. Matched runs at 199 AA yielded three wins each for WAR/CLR/MNK and MAG/NEC/SHM. WAR/PAL/MNK and WAR/CLR/WIZ lost their three attempts. The test arena excludes room geometry and adds. [Measurements and gear](balance/README.md) |
| Power Source | RoF2 retains each incoming training definition when a whole percentage or quality changes. Other copies can retain the ordinary item name and stats. | The production cache path and incoming per-instance definition were exercised in the x86 client fixture. Requires the updated launcher-delivered proxy. [Client candidate](rof2-candidate.json) |
| Ascended armor | Eligible ordinary armor and shields get an additional three percentage points at current rule values. Missing variants keep their base item. | All 10,000 rolls were tested for each item category. The armor bands are 71% Normal, 20% Polished, 5% Exalted and 4% Ascended. Other eligible ordinary items retain 74%, 20%, 5% and 1%. |
| Tunnel Recall | The login grant consults owned rank, retries a failed grant and includes class 17. The paired Hailstone General tab recognizes the class mask. | LocalDev had three marked Cairnwrights with zero Recall ranks. Six simulated login cases passed. Forward, inverse and stale-row transaction checks preserve other grant and boss data. [Preview candidate](ops/preview-candidate.json) |
| Imitate Death | The hotkey handler finishes an owned rank 1255 request by sending that AA's ready state. A click while feigned can return before the normal cast completion packet. | The 21-case AA suite included the final packet after successful and rejected clicks, 46,872 ordered family pairs and independent Purify Body reuse. The native RoF2 readiness fixture passed 49 checks. |

The base release was reproduced before compiling the changed zone. The operator checks each environment's current binary, mapped workers, two caches, affected quests, two database rows and occupancy. Rollback restores the previous scoped content and native image while keeping player progress. [Operations](ops/README.md) · [In-game QA](QA.md)

## Live deployment

The gameplay changes passed automated checks on dev and test and reached main in [PR 539](https://github.com/frank-grimes-jr/nightcap/pull/539). LocalDev and OVH each ran the same rebuilt zone on all twelve workers. OVH reopened admissions with the two scoped database changes, both quest files and the paired native binary verified. The post-start checks recorded zero restarts and zero recognized native, quest or database errors. [LocalDev receipt](ops/local-verified.json) · [OVH receipt](ops/production-verified.json) · [OVH runtime checks](ops/production-errors.json)

A primary Cairnwright received the missing Recall rank on LocalDev, retained it on a second login and kept the same AA point totals. The Plane of Fear encounter with adds, live item-window refresh, tunnel arrival and hotbar appearance still need player QA. [In-game test steps](QA.md)

Fully exit EQ and restart through the Nightcap launcher to receive standard game release `2026112701`. All 150 public game files passed verification. At the owner’s request Hailstone release `2026112702` stays privately staged. The public preview remains on `2026112202` and can still hide the General entry for a primary Cairnwright. [Standard game publication](rof2-publication.json) · [Hailstone release status](ops/preview-publication.json)

The production Loot Finder regenerated 6,377 items. Its Runnyeye armor example rose from 0.660% to 2.617% per kill, and the Hole weapon example held at 0.996%. These figures include each NPC's chance to drop the base item. [Loot Finder snapshot and controls](knowledge/loot-refresh.json)
