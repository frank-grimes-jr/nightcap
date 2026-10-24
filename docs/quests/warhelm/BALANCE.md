# Ashen Compact combat calibration

Final candidate measurements, October 24, 2026. All 24 bounded native boss cases
ended in a kill. The four lower-progression controls ended in player death.
These results support retaining the authored statistics; full-route tuning and
owner acceptance remain open. No game database, deployed binary or service changed.

## Measured setup

Level 50 Human Shadow Knight main, Cleric/Monk secondaries, legal Classic
Bertoxxulous creation allocation, and 3,566 legally purchased AA points. This
maximum legal allocation is a stress fixture, not a recommended entry requirement.
Prepared HP/mana were 8,118/5,093. Gear uses captured strong items, Darkforge
Gauntlets 603144 and Boots 603146, and the proc-free Balanced Tonfa of Serenity
662038 through held Monk. Inherited Warrior-only Indicolite pieces and Paladin-only
Ghoulbane 605403 are excluded. Exact slots, augments and AA ranks are in the
per-case input files and sk-aa.json; this setup is not claimed to be global BiS.

The native controller uses melee, Monk abilities/Mend, Lifedraw and Superior
Healing, with Valor/Symbol preparation and recovery between cases. Raid uses
135% base HP and 115% native calculated damage. Three deterministic seeds
(101, 2718, 8675309) were used per boss and mode, with a 300-second limit.

| Boss | Mode | Time to kill, three seeds | Lowest HP reached |
|---|---|---:|---:|
| Herald of the Iron Oath | Grind | 55.0–61.9 s | 72.8% |
| Herald of the Iron Oath | Raid | 78.0–81.9 s | 69.2% |
| Marshal Kharzug | Grind | 76.0–78.5 s | 61.2% |
| Marshal Kharzug | Raid | 107.0–115.2 s | 52.0% |
| General Vhalek | Grind | 94.0–105.2 s | 47.1% |
| General Vhalek | Raid | 137.9–143.9 s | 54.9% |
| Echo of Endless War | Grind | 124.0–130.9 s | 41.7% |
| Echo of Endless War | Raid | 178.7–186.8 s | 14.1% |

The finale's Raid cases reached 39.4%, 25.9% and 14.1% HP; minimum remaining mana
ranged from 74.2% to 80.7%. Damage spikes, rather than mana exhaustion, dominate
this particular fixed controller. Do not read its results as proof that other
class combinations or optimal play have equivalent difficulty.

## Progression controls and limits

The same SK/Cleric/Monk controller with 500 legal AA points, Polished gear and no
augments died against the Herald in 20.7–59.5 seconds and against the Echo in
8.3–18.6 seconds, across two seeds each. These controls demonstrate a progression
contrast; they do not establish a minimum AA, gear or class requirement.

The arena excludes the quest's Perl warnings, movement checks, adds, defense,
Kael pathing and consecutive route attrition. It also omits the SK pet, Life
Leech and optimal activated SK AA use. Full-route QA must examine both the added
script pressure and stronger player strategies before calling balance accepted.
Bosses have charm/fear/fleeing immunity, remain interruptible by stun, and use
living Storm Giant model 189. The Echo's special ability 5 is a 5% flurry.
Defense war souls use Spectre model 85 and remain controllable.


The later Everfrost entrance revision leaves all NPC definitions, private Kael
spawns, items and combat logic unchanged. These measurements retain their exact
pre-relocation build in calibration-native-build-manifest.json; they were not
rerun or relabeled as a new combat measurement. The current entrance build has
its own native-build-manifest.json. See EVERFROST.md for the verified comparison.

## Reproduction and evidence

Follow RUNBOOK.md. The final diagnostic was linked after the full candidate
build; all local native overlay sources match its full-source manifest. Exact
binary, source, input and result bindings are in calibration-receipt.json.
sk-results.json and sk-controls.json summarize the compressed raw outputs, each
with an uncompressed SHA-256. The synthetic fixture's public data derives from
the October 23 Camil capture; it is not a fresh production snapshot.
