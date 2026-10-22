# AA pacing and XP boost retirement - October 21, 2026

Candidate; owner explicitly authorizes main and production. Gameplay acceptance remains open.

Implement 1,000,000 AA XP per point with 10% passive earning. Retire Magus
Goldwind's 100pp XP package (Commonlands and legacy PoK script); hail/empower
direct players to Matron Restora's free ordinary buffs without payment/grants.
Preserve earned points, purchases, raw partial AA XP, ordinary buffs and existing
positive boost timers. Native PercentXPIncrease buffs retain their durations;
stale permanent sentinels normalize on load to the minimum native countdown
(1 to 0 to fade across two unsuspended ticks). Offline rows need no destructive
cleanup. Future earned boosts are a separate proposal, not delivered here.

Plan: extend the existing temporary-duration branch in spells.cpp; regression
tests execute the extracted policy and BuffProcess. Build only this implementation
unit from authenticated current retained source/objects and prove the original
link reproduces the live zone. Update rule/quest during a guarded full-runtime
restart, with fresh stopped backup and preserved player/content receipts.
No new rule catalog, client, spell data or cache pairing is required.

Rollback restores only prior image/Goldwind scripts and the exact guarded AA
rule. Never restore player snapshots or erase later earned progress. Do not
restart one native child: OVH supervises the whole runtime. Failed/uncertain
writes stay held for receipt-aware diagnosis.

## Owner QA
1. Relog with a prior permanent XP boost: minimal countdown then fade after two
   unsuspended native buff ticks. Ordinary buffs remain.
2. A timed XP boost retains remaining duration through zoning/relog.
3. Hail Goldwind and say empower: no platinum lost/XP buff granted. Hail Matron:
   free level-bracket buffs still work.
4. Record AA points/remainder/purchases; use #aaexp off on comparable Mistmoore
   dark blues. At level38, level35-37 mobs without boost model36-40 kills per
   passive point (carry matters). At #aaexp on, around4 kills per point with
   normal XP diverted. Restore off.
5. Buy a legal rank, zone, camp/relog and verify ownership/progress persist.
   Broader level20/35/50 melee/caster/pet balance remains owner testing.

## Model and evidence boundaries
The selected1m threshold is Nightcap tuning, not a verified THJ constant.
At level38/Mistmoore/level35-37 dark-blue mobs without +50%XP, extracted native
arithmetic gives25,081-28,030 passive AA XP per kill:36-40kills/point. Focused
earning models about4kills/point. Level50 Hole dark blues model12-13passive
kills/point because NPC XP and level/zone modifiers differ.

Corrected continuous level1-50 model includes live per-level normal/AA modifiers:
19,740,195 passive AA XP, approximately19.7points at1m (493.5at40k). The previous
412at40k estimate omitted level-modifier ratios. These are theoretical totals,
not measured player trajectories; focus, quests, overshoot and truncation vary.
Removing a +50%boost lowers its per-kill normal/AA awards by one-third; it does
not change the passive percentage. No additional paid/earned boosts ship here.

Native build v2 reproduces current59831725 zone exactly before replacing only
spells.cpp.o. Newzone5dd5a655; retained source and link inputs remain exact.
The initial isolated attempt failed include lookup before producing a candidate;
v2 adds the retained zone source include directory. No live change occurred.
Local Docker recovery retained only the two stale socket directories; containers,
database and the E: data disk were preserved.
