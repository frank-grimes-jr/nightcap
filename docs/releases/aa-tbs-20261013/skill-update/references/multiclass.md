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

## AA catalog policy — deployed for owner QA October 13

The TBS cutoff and six utility/pet exceptions are active in a compiled native
allowlist, with staged early caps. See [balance](balance.md) and
`C:/Users/verre/.codex/worktrees/aa-tbs-policy/EQ_Local_Dev/docs/releases/aa-tbs-20261013/README.md` for exact ranks,
source, tests, rollback and owner QA. Main promotion/player acceptance is pending.
World stays Classic; all DB AA definitions and purchases remain intact. Higher
earned ranks and veteran grants are dormant; no refund or duplicate purchase.

`aa.cpp::CanUseAlternateAdvancementRank` checks generated rank identity and level;
`ReprojectEarnedAAs` derives active ranks without losing canonical counts/charges.
`exp.cpp::SetLevel` reprojects before bonuses/save, and AA refresh sends clear,
table, points and stats. Missing prerequisite definitions fail purchase closed.
Pet HP changes on summon/restore; avoidance/AC uses current owner bonuses.
Only zone needs rebuilding for this policy; no new rule catalog or client asset.
The concurrent fully rebuilt skill/offhand fix and signed2026101301 remain paired.
All12 zone hashes and47 player/11 custom table preservation passed; no owner
balance/readability acceptance or fresh combat measurements are implied.

## Skills and AA ownership

- Eligible native skills seed at **1**, then train/use normally; don't reinstate max-skill-on-login. `ReconcileMulticlassSkills`, held-class cap and trainer paths have lifecycle tests. Canonical cap baseline is 58,359 rows in the dated repair; counts are not current drift baselines.
- `Client::ReleaseMulticlassSlot(int)` commits slot changes, earned-AA refunds and skill clamps atomically. Perl must check its boolean. Don't pre-update membership or call retired `PurgeAfterClassRelease`. Pair native binary and plugin.
- `m_earned_aa_ranks` preserves earned ranks/charges while a separate usable view applies class/era caps. A family that becomes unavailable must not silently lose purchased ranks or spent points. `aa_ability.id` differs from `first_rank_id`; saved AA ownership uses rank identity.
- Purchases/grants/removals/refunds commit ownership and counters before reporting success. Uncertain/failed saves invalidate the session rather than publishing partial success. See ADRs 0021–0026 and `docs/balance/native-aa-class-release-candidate.md` plus `native-aa-session-recovery.md`.
- AA rank graphs don't define the legal release pool. Balance against an explicit curated pool/rank caps; unrestricted AAs are a separately labeled stress test.

## Trainer interaction deployment

October 13 owner QA confirms the previous 2026101204 trainer window opens,
but purchases, natural skill gains and offhand access fail. The first release
missed two client gates and preserved a causal server baseline difference.
PR #191 merged and paired correction deployed October 13: signed game 2026101301, all 12 zones and 105 hosted assets verified. Player acceptance remains pending.

Production diagnosis found Palwar level6 Paladin/Warrior/Monk, DW1/Kick1,
with correct canonical Monk caps47/30. Do not repair this by granting points or
rewriting skill_caps. Skills seed at1 and must advance through normal use/buys.

Retained Client::MaxSkill(skill) was inline primary-only; Git main already held
the union. Stage that union and rebuild every126 zone TU with a fresh candidate
PCH. Never infer deployed advancement from main alone or retain old objects
embedding the primary-only inline call. Retained empty-fist dual wield also
used primary-only Monk/Beastlord; use direct held membership, preserving weapon
restrictions without depending on an undeployed hand-to-hand helper.

Proxy0.8.3-dev wraps the trainer at-cap predicate call0x185955 and projects its
nested cap query0x184C2B only within a character-matched thread-local scope.
Native specialization/tradeskill rules, server cap and spending remain intact.
Offhand HasSkill call0x183445 needs a separate fallback before item-class checks:
require matching current identity/profile, positive server rawDW and current-
level held native cap. Future Warrior caps must not retain staleDW after Monk
release. Stock successful checks and surrounding slot/2H guards remain intact.

Source/tests: server-mods/code/zone/{client.h,client.cpp,mob.cpp},
eq-client-dll/src/trainer_hooks.h, tools/tests/test_multiclass_skill_progression.py,
eq-client-dll/tests/trainer-native.cpp, tools/build_skill_progression_candidate.py.
Actual retained-source RED5/control4; staged/repo GREEN9, exact-native client
purchase/offhand RED/GREEN,6 runtime groups,91 catalog guards and fullGo suite
pass. Independent review verified ABI and fixed stale future-cap access.
Evidence and exact training/combat/offhand/relog QA:
docs/releases/multiclass-skills-20261013/ in
E:/EQ_Local_Dev/_worktrees/multiclass-trainer-access.

Pair rebuilt zone and signed proxy/catalog; rule/quest reload is insufficient.
Use graceful whole-runtime refresh; never kill one OVH zone. Preserve player
progress and retained image; rollback never restores old SQL and client rollback
uses a higher signed counter. Native/unit/hosted checks do not establish actual
player combat or purchase acceptance.

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
