# AA pacing: 40,000 XP per point — October 21, 2026

**Deployed for live balance testing at 09:28:12 UTC (5:28:12 a.m. Eastern), October 21.**
The public wiki and private player guide are published and verified; owner gameplay acceptance remains open. The owner reports AA points
arrive too quickly and selected 40,000 XP per point, retaining 10% passive earning
and existing points/purchases. Only AA:ExpPerPoint changes, from 4,000 to 40,000
in default ruleset 1. No native, client, quest or cache update is needed.

## Behavior
Passive and focused earning take ten times as much AA XP per point. Ordinary
leveling XP, raw AA awards, AA prices, eligibility and ownership are unchanged.
Raw partial XP is retained, not scaled: 2,000 XP goes from 50% to 5% of a point.
No player row is rewritten. Remainders and rounding mean an individual kill need
not visibly award exactly one tenth as many whole points. The client bar may
wait for its next normal AA stats update; verify it after reconnecting.

The October 17 review recorded equal normal/AA multipliers around 0.65, 10%
passive earning, normalized mode false and modern scaling false. Its simplified
continuous-leveling model uses 164,708,600 XP to level 50: about 412 passive AA at
40,000 versus 4,118 at 4,000. Boosts, prior rates, focused grinding, quest paths
and rounding alter actual results. See ../passive-aa-ten-20261017/REVIEW.md.
This is a model, not measured gameplay. A read-only production capture on October
21 at 09:16:16 UTC confirms 4,000 XP/point, passive 10%, normalized/modern modes
false, and active ruleset default. Ruleset 10 has the same 0.65 normal/AA
multipliers. See production-rule-observation.json. The subsequent activation preflight verified source/runtime, zone scope, locks and backup; see result.json.

## THJ research
No verified raw XP-per-AA threshold was found. Archived forum post 357
(December 13, 2024) reports 9%/12%/16% of a point per blue/white/yellow kill at
level 60 in Chardok B. Post 389 (December 17) reports 40–45 AA/hour in Veksar at
51. These are uncontrolled player observations, affected by build, zone,
veterancy and event bonuses. Neither 4,000 nor 40,000 is a verified THJ value.

[Post 357](https://www.firesofheaven.org/threads/the-heroes-journey-multiclass-eqemu-progression-server.15510/post-4986063);
[post 389](https://www.firesofheaven.org/threads/the-heroes-journey-multiclass-eqemu-progression-server.15510/post-4989018).
Local capture: E:/EQ_Local_Dev/artifacts/research/thj-forum-20261018/posts.json.
The THJ wiki/source endpoints were unavailable during this review.

## Activation and rollback
The owner authorized main promotion, production activation and matching guidance
publication on October 21 after candidate review. Execution is recorded separately. Existing compiled defaults remain unchanged. Relevant
source is Client::GetRequiredAAExperience, FinalizeAAExperience and SetEXP in
server-mods/code/zone/exp.cpp; AA stats use the same denominator.

1. Under existing deployment/GM locks, capture fresh full rules, active ruleset,
   retained XP source, process identities and health. Require default ruleset 1,
   the sole 4,000 override, passive 10%, normalized false and modern scaling false.
   Check zone-specific rulesets and runtime source against tested methods.
2. Validate a fresh full PEQ backup and rehearse forward/inverse in an isolated
   clone. Run forward.sql without --force. Its transaction rejects baseline drift;
   compare full rule-table pre/post images to prove exactly one value changed.
   Scripts create a temporary helper procedure, call it and remove it. On failure,
   inspect its transaction outcome and remove only the leftover named helper
   before retrying. Do not blindly rerun or use --force.
3. Perform the existing authenticated global Rules reload; verify fresh completion
   from world and every running zone, stable process identities and healthy
   services. SQL success alone is not loaded-runtime proof. Do not kill a zone:
   production's supervisor would restart the whole runtime.
4. If reload/verification fails, inspect receipts and actual rules before recovery.
   rollback.sql changes only an exact 40,000 override back to 4,000; reverify the
   full reload. Preserve later external edits and all current player progress.

Rollback keeps completed points and raw partial XP. A remainder above 4,000 can
convert to extra points on the next normal XP update. This is retained earned XP;
never erase it, rescale purchases or restore an old player snapshot.

## Exact owner QA after activation
1. In Unrest on Palwar, run #aaexp off. Record level, normal XP, banked points,
   purchases and partial AA XP; kill comparable eligible living and undead mobs.
   Normal XP and raw AA award stay the same; 40,000 accumulated AA XP gives one
   point. Compare multiple kills to account for carry.
2. Cross a boundary, buy a legal rank, zone to East Commonlands, camp and relog.
   Points, purchase, remainder and allocation must persist. Existing purchases
   must remain intact when the rule loads.
3. Run #aaexp on on comparable targets: no normal XP gain, full AA award with no
   passive extra, still 40,000 XP per point. Restore #aaexp off afterward.
4. Test a genuine quest/task reward and a disposable new character. Tiny gains
   may round to zero. Measure representative melee/caster/pet builds at levels
   20/35/50: kills, time, gains and useful purchases. Automated arithmetic and SQL
   checks do not establish player-visible behavior or balance acceptance.

See result.json for activation, verification.json for checks and wiki-review.md for guide scope.


## Authorized operator
ops/apply.py reuses the reviewed October17 single-rule activation/recovery flow.
It pins the current built world/zone and every running native child, verifies the
four-rule baseline and source-pairing.json, backs up and validates full PEQ, then
rehearses a guarded UPDATE and inverse in a rolled-back transaction. It changes
only this row and verifies global Rules acknowledgments. Ten simulated transport/
recovery checks pass, including uncertain commit, evidence failure, unrelated
rule edits, external target edits and changed processes. The manual forward.sql/
rollback.sql helpers are an alternative guarded path, not additionally executed
by the automated operator. No player-state restoration or native restart occurs.

## Activation evidence
Main promotion PR262/059fd49 is complete. result.json records exactly one changed
rule, a validated fresh 459,290,389-byte uncompressed backup, rehearsed inverse,
world/all 12 zone reloads and unchanged process identities. All five services
remain running; game/database are healthy. No player row was written by the operator.
Independent review reran all 10 operator tests and found no blocking findings.

guides-publication.json records wiki 20261021-aa-pacing-v1 and private guide
20261021-aa-pacing-guide-v1. Rollback was rehearsed; private downloads, service
identities and web configuration were preserved. The public verification receipts
confirm every one of 465 wiki files and five private guide files, route protections
and expected headers. Site checks: 14 Python article/refresh tests, 13 Node tests,
16 Linux wiki operation tests and 10 Linux player-site operation tests. These
53 checks and public verification do not establish in-game balance acceptance.
