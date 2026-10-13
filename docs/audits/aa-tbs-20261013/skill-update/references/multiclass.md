# Multiclass, spells, skills and advancement

Audited 2026-10-12 from integrated source and dated release records. Deployment claims below are documentary, not fresh runtime observations.

## Authoritative state and spell access

`character_multiclass(character_id,class2,class3)` is authoritative; primary is the native character class. Quest `%qglobals` is not a reliable membership source. Both extra slots are selectable from level 1. Read `server-mods/plugins/multiclass.pl` (`mc_get_classes`, `mc_apply_class`, `mc_revoke_slot`) and `server-mods/code/zone/aa.cpp` before changing selection.

The per-character held-class mask must be loaded before AA loading. Class bits are one-based class ID minus one. Never modify `aa_ability.classes` for one player's access. Best-of HP/mana, equipment union, native skill eligibility and held-class melee are server concerns; an unlocked client window doesn't grant capability.

The old global spell widening is no longer sufficient guidance. The September 20 repair uses a generated **original-class spell catalog** and per-character server/client access. Start at `docs/adr/0042-per-character-spell-access.md`, `server-mods/code/common/spell_class_catalog.h`, `tools/generate_spell_class_catalog.py`, `tools/tests/test_multiclass_spell_access.py`, and `eq-client-dll/src/spell_access.h`. Native casting/scribing must use canonical ownership; widened `spells_new.classesN` and merchant display masks are client compatibility data. Canonical spell inspection and selection-menu caches received separate October fixes (`docs/releases/spell-inspection-20261001.md`, `spell-menu-20261002.md`). Don't regenerate original levels from already widened rows.

## Early spell scribing — deployed October 12

Owner-approved PR #185 (`5ae9cb0`, main merge `d6c5b65`) allows scrolls for any currently held class to be
scribed before the canonical spell level. `Client::OPMemorizeSpell` in
`zone/client_process.cpp` skips level only for `memSpellScribing`, with explicit
255/unowned rejection. `MemorizeSpellFromItem` in `zone/effects.cpp` also scribes
only; its ownership/duplicate/full-book checks remain. Gem memorization and the
`Handle_OP_CastSpell` gem authorization retain canonical level requirements.
No spell catalog, item masks, DB rows or caller-specified bulk-scribe ranges change.

Pair the rebuilt zone with proxy 0.8.1-dev and its signed patch catalog. Client
`ScribeSpellLevelHook` at RVA 0x35E084 changes only the scribing comparison; shared
levels and the following native 255 check stay intact. Missing/stale identity
fails closed. Rule/quest reload is insufficient; production native child exits
restart the whole runtime. Follow the coordinated release procedure, preserving
all intervening changes and player data, and use a higher client release counter
for rollback. Do not erase books or restore old player snapshots.

Source and exact QA: `docs/releases/early-spell-scribing-20261012/README.md` and
`verification.json` in `C:/Users/verre/Documents/Codex/2026-10-12/g-2/work/early-spell-scribing`.
`tools/tests/test_early_spell_scribing.py` compiles actual server methods; existing
multiclass gem-cast tests pass. Complete zone and x86 client builds, five runtime
tests (including the exact native comparison), 76 patch checks and independent
review pass. Full Go suite and patch-history integration tests pass. Paired OVH
zone and signed client 2026101203 are deployed; all 12 running zones and all 105
hosted files verify. Native scribe/relog/gem gameplay and owner acceptance remain
pending. See server/client receipts beside the release README. Closed-gateway
checks preserved 47 player tables, 11 custom tables, rules/content and supporting
services. Never interpret deployment verification as observed gameplay.

## AA catalog policy audit — October 13

Fresh read-only production data confirms every AA rank has level requirement1,
with expansion filtering off. See the [balance reference](balance.md) and
`E:/EQ_Local_Dev/docs/audits/aa-tbs-20261013/README.md` for the TBS rank-prefix
audit, complete inventory, later utility/pet exceptions and exact QA. This is a
recommendation, not an installed whitelist or solo-balance acceptance. Current
native AA send packets report expansion0; purchase level checks are distinct
from display eligibility. Do not use world CurrentExpansion13 as an AA-only cap.
64 saved rows include post-TBS ranks; preserve canonical earned ownership and
accounting through any later availability change. No cache/client pairing was
changed by the audit. Independent native enforcement/UI work remains future scope.

## Skills and AA ownership

- Eligible native skills seed at **1**, then train/use normally; don't reinstate max-skill-on-login. `ReconcileMulticlassSkills`, held-class cap and trainer paths have lifecycle tests. Canonical cap baseline is 58,359 rows in the dated repair; counts are not current drift baselines.
- `Client::ReleaseMulticlassSlot(int)` commits slot changes, earned-AA refunds and skill clamps atomically. Perl must check its boolean. Don't pre-update membership or call retired `PurgeAfterClassRelease`. Pair native binary and plugin.
- `m_earned_aa_ranks` preserves earned ranks/charges while a separate usable view applies class/era caps. A family that becomes unavailable must not silently lose purchased ranks or spent points. `aa_ability.id` differs from `first_rank_id`; saved AA ownership uses rank identity.
- Purchases/grants/removals/refunds commit ownership and counters before reporting success. Uncertain/failed saves invalidate the session rather than publishing partial success. See ADRs 0021–0026 and `docs/balance/native-aa-class-release-candidate.md` plus `native-aa-session-recovery.md`.
- AA rank graphs don't define the legal release pool. Balance against an explicit curated pool/rank caps; unrestricted AAs are a separately labeled stress test.

## Trainer interaction deployment

October 12 owner-approved PR #189 is on main and deployed for Palwar's held-class trainer access. The production
probe confirmed Paladin/Warrior/Monk, level 4, 20 points, Joren 999656 class 26,
and no hail quest. Server held-class authorization was already present; RoF2
blocked right-click and trainer list/button/purchase queries by primary class.
`Client::CheckTrainerHail` now delegates a native hail to `OPGMTraining`, retaining
membership, distance and current caps. No points/coins/skills/classes are granted.

Pair the rebuilt zone with proxy 0.8.2-dev and signed catalog. Trainer-only
client queries use identity-matched held classes, greatest native cap and lowest
positive unlock level; missing/stale identity preserves stock behavior. See
`eq-client-dll/src/trainer_hooks.h`, `tools/tests/test_trainer_hail.py`, and
`eq-client-dll/tests/trainer-native.cpp`. Exact native RED/GREEN, six runtime
groups, 87 signature/catalog guards, x86 proxy and complete zone link pass;
independent review cleared after verifying 141 retained live link-input hashes.
The full launcher Go suite also passes with normal Windows permissions.
The native response initializes trainer state without a preceding right-click.

Evidence and exact Joren/Garran/Aldric/unheld-trainer/spending/relog QA:
`docs/releases/multiclass-trainers-20261012/{README.md,verification.json}` in
`E:/EQ_Local_Dev/_worktrees/multiclass-trainer-access`. Deployed with signed client release 2026101204; owner training/spending/relog
acceptance remains pending. All 12 zones match; 47 player and 11 custom tables
were preserved through the graceful whole-game restart. No SQL was restored. Retained production has a primary-only single-argument MaxSkill
overload absent from current main; candidate staging preserves that separate
baseline difference. PR #189 merged at 7df224d, retaining early-scribing and launcher
patch-history changes. Deployment receipts record image
sha256:1eef609e4daed95ad84fcbd193e56c0f7abbefedf325813f58316be5da558578.
Recheck live image and channel before later publication. Rule/quest reload cannot
install native/client changes. Production requires coordinated full-runtime
refresh and signed client delivery; rollback retains player progress and uses
a higher signed client counter, never an old player snapshot.

## XP

`era.json`: Classic, cap 50, open AA era visibility as audited. `Character:AAExpMinLevel=1` requires a matching rule catalog. `AA:PassiveExpPercent` adds AA XP while allocation is zero without reducing ordinary leveling XP. `#aaexp on|off` maps to 100%/0%; focus at 100% gives the full AA award and no passive extra. Tiny gains round down. Quest percentage rewards have independent level/AA modifiers. Resurrection/direct grants aren't passive award sources.

**OVH: 40% passive AA and 4,000 XP per point**, freshly verified October 12,
2026 at 20:49 UTC. `AA:ExpPerPoint` fell from 50,000 to 4,000 under the owner's
request; unchanged raw AA awards now yield points 12.5 times faster. The compiled
fallbacks remain 1% passive and 23,976,503 XP/point; preserve the persistent
production overrides. This changes point earning, not AA ability purchase costs.

Existing unspent/spent points and raw partial XP are preserved. `Client::SetEXP`
converts partial XP by quotient/remainder on the next XP update. Reload alone
does not convert points or refresh the AA bar; a refresh before conversion may
temporarily show over-full progress. Do not rewrite live player records. A later
rule rollback retains earned points and remainder, never restores a player dump.
Palwar's pre/post-reload snapshot retained 4,361 partial XP at level 3; that covers
one point plus 361 remainder before the next award. Actual kill/client persistence
and later-level balance acceptance are still pending, not implied by this snapshot.

Source: `server-mods/code/zone/exp.cpp` (`CalculateExp`, `FinalizeAAExperience`,
`SetEXP`, `GetRequiredAAExperience`), `aa.cpp` (`SendAlternateAdvancementStats`),
`gm_commands/aa_exp.cpp`, `common/ruletypes.h`. Current evidence/recovery:
`docs/ops/aa-point-cost-20261012/README.md`, `preflight.json`, `result.json`, and
`verification.json`. Historical 40%-rate evidence remains in
`docs/ops/passive-aa-forty-20261009/README.md`; its old 50,000-XP curve is superseded.
`tools/tests/test_aa_point_cost.py` runs 162 checks using the exact deployed XP
methods and extracted point-conversion block; nine operation/recovery tests pass.
The independent review's evidence-write recovery issue was fixed and re-reviewed.
Existing-rule global reload was verified in world/all 12 zones without restart;
no native/client/quest pairing changed. Full PEQ backup and scoped inverse rehearsal
passed. Native tests and successful deployment do not establish combat balance.

GM level boosts must write native float32-compatible cumulative XP and exactly-once lifetime training points, preserving valid progress/highest attained level. `exp=0` at level 50 caused a subsequent award to de-level a character. Route boost changes to [Administration](admin.md).

## Focused checks

`tools/tests/test-multiclass-class-release.ps1`, `test-multiclass-release-plugin.pl`, `test-multiclass-skill-lifecycle.ps1`, `test-multiclass-trainers.ps1`, `test-multiclass-monk-combat.ps1`, and `tools/test-multiclass-plugin-skill-policy.ps1` are targeted entrypoints. `tools/balance/run_aa_class_release.py` and related native ownership controls need their documented isolated fixture environment. Read the exact runner/runbook before invoking it; old test counts aren't current acceptance.
