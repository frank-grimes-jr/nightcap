# AA pacing and XP boost retirement - October 21, 2026

Main PR268/e64f502 and owner-authorized production activation are complete. Access is open; owner gameplay and balance acceptance remain open.

Implement 1,000,000 AA XP per point with 10% passive earning. Retire Magus
Goldwind's 100pp XP package (Commonlands and legacy PoK script); hail/empower
direct players to Matron Restora's free ordinary buffs without payment/grants.
Preserve earned points, purchases, raw partial AA XP, ordinary buffs and existing
positive boost timers. Native PercentXPIncrease buffs retain their durations;
stale permanent sentinels normalize on load to the minimum native countdown
(1 to 0 to fade across two unsuspended ticks). Offline rows need no destructive
cleanup. Future earned boosts are a separate proposal, not delivered here.

Implementation: extend the existing temporary-duration branch in spells.cpp; regression
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

## Capacity recovery before activation
Two preflights stopped at the postimage reserve gate before live changes. Docker
retained context/layer data beyond the raw zone size. The scoped cleanup verified
four exact retained local upload archives before removing their remote duplicate
transfers and pruned only observed unshared task cache IDs. All production
backups and installed release images were retained. A second cleanup postcheck
failed after cache removal; the follow-up inspection confirms both exact cache
IDs absent, unchanged running service start identities, no image events in the
checked window and the pinned candidate still available. No blind mutation replay.

resume_preflight.py reuses immutable candidate
sha256:15a159c0f9a80d541856d7412e59d94baa6b29cc320c397cab9e3d44278ecfff,
authenticates all binaries/base layers and preserves every original gate. Fresh
preflight passed with about1.2GB free. Never repeat the image build merely to
resume a completed build; inspect receipts and reuse its verified immutable ID.
Original failed logs and rollback script copies are retained.

## Verified deployment and publication
The zone-only successor 5dd5a655 and paired Goldwind scripts are installed with
AA:ExpPerPoint=1000000 and the existing 10% passive rate. Both the first startup
and final verified startup passed all 12 zone checks. Fresh stopped full backups
passed gzip integrity; earned AA and other player/custom state were preserved.
No player snapshot was restored. Client/world/shared-memory/cache pairing remains.
Final access and runtime identity: deployed.json. Both actual market startups
were independently validated; their receipts retain the before/after epochs.

First activation held access when the zone-cache hash changed. The native
seven-day policy expired exactly 485 non-corpse cache rows: 357 in zone38 and 128
in zone75, instance0, dated October13. The isolated cache-only backup restore
matched the original complete serialized hash; survivors and all other state
matched. No live restore occurred. See cache-diagnosis.json, state-drift.json and
cache-source-pairing.json. A completion guard exposed dump float round-trip
storage differences; canonical serialized values were equal. The revised guard
retains exact original/scratch and live fingerprints, binary text comparison,
and dump-compatible floats. finish-first.log and cache-float-diagnosis.json
retain this stopped-before-start check. Independent review and five recovery
tests cover drift/failure rejection and the real finish-to-open receipt layout.

finish_cache.py keeps the original hold intact, takes another stopped backup,
starts the already installed image, checks state/market/health and only then
allows the separate open action. backup.json, verified-closed.json, cache-expiry.json
and deployed.json record completion. Retain original remote evidence under
/opt/nightcap/releases/aa-pacing-million-20261021/evidence and finish-evidence.
For future rollback, use current earned state and fresh stopped receipts; the
original pre-expiry snapshot is an audit reference, not a recovery baseline.

Published wiki20261021-aa-million-v1 and private guide20261021-aa-million-guide-v1
verify all 465 and 5 HTTPS hashes/protections. Guarded publication rehearsed
rollback and preserved configuration/private downloads/service identities.
All 21 guides and 432 reward routes were reviewed; no new reward/catalog/command
behavior. Gameplay acceptance remains the owner QA above, not a release-test claim.
