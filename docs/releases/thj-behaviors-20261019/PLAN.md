# THJ custom behaviors and stock-EQ gear comparison

Status: implementation, independent source review and full database rehearsal complete.
Paired test artifacts and exact owner QA are prepared for the dev/test handoff.
Not deployed or owner accepted.
Baseline: main45e8416 / all-class AA release. Preserve Classic50 and starter progression.

## Accepted scope
Implement the released April/May THJ custom AA mechanics and spell focuses supported
by retained evidence. Compare all131 observed Legendary definitions to independently
captured stock PEQ data (an emulator approximation of standard EQ), derive explicit
field/category scaling for ordinary unobserved gear, and retain exact observed targets.
Keep uncertain coefficients labeled as Nightcap calibration; do not invent THJ facts.
Update candidate wiki guidance and prepare native/client/content testing artifacts.
Do not activate a new era or deploy gameplay to production in this task.

## Ordered slices and proof
1. Pin released-post, native spell/AA, and independent stock-item inputs. Record exact
   IDs, class masks, costs, durations, focus limits and uncertainty dispositions.
2. Implement custom AA/spell content and narrowly scoped native resource, interruption,
   duration and focus behavior. Preserve earned ownership, refunds, deadlines and pet/WPM.
   Prove source-method math, eligibility, failure paths, and guarded SQL replay/recovery.
3. Fit and review gear rules against stock131 pairs; preserve209starter families and
   custom rewards/effects/sockets. Test exact samples, intermediate monotonicity, untouched
   fields, zero/negative stats, identity drift and guarded migration.
4. Build matching world/zone/cache/client spell and AA description candidate; rehearse
   content on an isolated database. No running-server or protected-client edits.
5. Review independently; update CHANGES, status, wiki, installed skill fingerprints and
   exact in-game QA. Prepare feature/dev/test review within authorization; main/server
   require subsequent owner approval.

## Key risks
Percent mana must debit once per cast (not once per group target); failed/blocked burns
must not consume mana or cooldown. Native spell bounds and class ownership remain.
Focus source and receiving spell differ: Bard outgoing focus stays randomized while
Bard songs receive no focus. Do not amplify unrelated NPC effects globally.
Stock item identity and source provenance must precede ratio fitting; observed zero
fields cannot justify multiplying missing native stats. Content rollback preserves
new earned AA/item state; no player snapshot restoration.
