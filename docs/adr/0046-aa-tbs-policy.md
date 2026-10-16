# AA availability for Classic solo QA

## Owner correction — October 13, 2026

The level-staging decision below was rejected in live QA. All legal AA ranks must be available from character level 1; players choose their spending. The release pool and numeric rank ceilings remain. Policy JSON now holds rank counts; DB level requirements cannot reinstate client gates. See [correction](../releases/aa-tbs-level1-20261013/README.md). Earlier evidence below describes the superseded candidate.

Status: accepted implementation intent, October 13, 2026; gameplay acceptance pending.

The owner requested the Buried Sea cutoff, the audit's conservative exceptions,
early rank caps, preservation of purchases, and OVH live QA. The baseline is
origin/main 114c730. Do not promote to main before owner gameplay acceptance.

Keep the complete database catalog and canonical earned ownership. Compile a
reviewable, generated rank allowlist from `config/aa-policy.json` and the captured
catalog. The native server checks the rank identity and character level for list,
purchase, grants, activation and usable-rank projection. Unknown ranks fail closed.
Later expansion ranks require a named exception; no global expansion/rule changes.
No AA definitions, masks, costs, purchases, charges or wallets are rewritten.

Core passives begin at level 1 or 10 with second/third ranks at 20/30. Other
ordinary TBS families begin at 30, with second/third ranks at 40/50. The Classic
ceiling is three ranks unless explicitly overridden. Utility gets individual
limits. Dangerous execute, burn, resource-refill and combat-glyph families remain
deferred even when older than TBS. These are conservative trial limits, not
measured balance thresholds. Dependencies raise unlock levels or remove an
unreachable rank and its successors; they never widen the allowed pool.

Exceptions: Eyes Wide Open (8 free ranks), Diminutive Companion (1), Enchanter
Pet Discipline (1, requiring Animation Empathy 3); shallow pet defenses are QA
candidates: Companion's Durability and Agility 1/2/3 at 30/40/50, Sturdy Companion
1 at 50. Preserve existing grant-only system entries only when explicitly named.
Custom attunement/dispatch remain available. No later burst or sustain exceptions.
Grant-only veteran rewards (including Lesson, recovery and vendor/banker summons)
also become dormant; they are not an exception to the curated purchase pool.

Higher owned ranks become dormant. Lower usable ranks retain their canonical
earned count, charges and spent-point accounting. Reproject from in-memory earned
state on level changes, before bonus calculation, without a database reread that
could lose pending charge consumption. Login/class/reload paths retain the same
policy. Clear and resend the AA list when eligibility changes. Existing temporary
spell buffs finish normally; this policy is not a blanket buff dispel.
Pet avoidance/AC query the owner's current bonuses. Pet maximum HP is fixed at
summon by the existing engine: Durability changes take effect on the next summon,
including restored pets after the deployment restart. Do not force resummons,
refill health or discard pet buffs on level changes. QA must resummon for HP trials.

Implementation order: policy/generator and tests; native gate and level projection;
independent review; provenance-checked zone build; guarded OVH candidate deployment
with backup, graceful whole-runtime restart, preservation checks and image rollback.
No new rule catalog or client asset is needed. Regeneration and a new zone build
are required for future policy changes; `era.json` names the policy source.

Proof: deterministic regeneration, dependency closure, representative class/level
coverage, real native gate/projection tests, preservation of dormant ranks/charges,
full zone compile/link, deployment recovery tests and stopped-state fingerprints.
Manual QA covers same-zone level transitions, purchase/activation, pets, relog,
and demanding solo encounters. No claim of fun or balance until owner acceptance.
