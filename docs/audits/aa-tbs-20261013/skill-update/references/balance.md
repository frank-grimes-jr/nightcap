# Combat and balance knowledge

Audited 2026-10-12. Dated September fixtures are reproducible evidence for their captured inputs, not a current character or production snapshot.

Nightcap favors solo play without trivializing earned progression. Evaluate classes, legal AAs, pets, buffs, heroic stats, augments and gear together. Measure incoming burst, survival, mana sustain/recovery, time to kill, cooldown use and reward acquisition, not only DPS or encounter HP. Cap increases above 250 are allowed for consideration; neither 250 nor a prior experiment is a permanent policy ceiling.

## Buried Sea AA audit — October 13, recommendation only

`E:/EQ_Local_Dev/docs/audits/aa-tbs-20261013/README.md` is the current AA catalog
review. Production content/rules were captured read-only at 09:33:44 UTC; all
6,655 rank rows require level 1, AA expansion gating is off, and 40% passive /
4,000 XP per point remain stored. No ranks are tagged expansion13, so TBS and TSS
cutoffs currently match. Conservative prerequisite-closed TBS pools retain
162–178 families / 2,861–3,413 points across six three-class profiles, versus
385–434 open families. These are class-mask catalog counts, not observed UI rows
or fresh fight results. Missing native prerequisites are not silently allowed.

Recommendation is TBS as outer bound, separate staged early-power caps and a
small utility/control list: Eyes Wide Open938 rank8, Diminutive Companion543
rank1, ENC Pet Discipline3202 rank1 with Animation Empathy195 rank3 prerequisite.
Pet HP3512/avoidance3818 through rank3 and Sturdy Companion1403 rank1 are
conditional trials; SPA397 contributes raw pet AC, not percentage mitigation.
TBS still retains deep defenses, Frenzied Devastation, Headshot/Anatomy, large
Tenacity HP, Mortal Coil and cheap glyphs. Later twincast/proc/resource engines
remain deferred. The historical solo combat cores included later pet support;
their victories do not validate a strict TBS pool on current production.

`families.csv`, `ranks.csv`, `class-coverage.csv` and `later-review.csv` enumerate
the offering. 1,310 later-rank families are inventoried, 45 individually reviewed
for content/source risks; remaining decisions are explicitly inventory triage.
`test_analysis.py` has eight focused closure/counting tests. Independent review
corrected spell-linked-versus-active labeling. All conclusions are proposals;
no runtime AA policy, fresh encounters or owner acceptance were added.

64 of 238 anonymous saved ownership rows contain later ranks. Preserve earned
ranks/charges/points and rerun per-character preflight before any enforcement.
Do not advance world CurrentExpansion just to gate AAs. Independent AA policy
needs matching server checks/cache refresh; new rule catalogs require world/zone
pairing, UI changes signed client delivery, and production native exits restart
the runtime. Exact level/build/encounter and ownership QA is in the report.
Reference-client title coverage is not signed-client verification. Current
captured custom2220/30196 point to Teleport42604/42603; the historical Ancient
Attunement99001/pet-spell finding does not describe this new content snapshot.

## Source routes

- `server-mods/code/zone/effects.cpp::GetExtraSpellAmt`: Nightcap flat/percent mode returns percentage-of-base scaling. At eligible 250 bonus, the simplified base-plus-bonus is 3.5x, not +250 damage and not a universal final-output multiplier. Exclusions, focus/criticals and DoT/HoT tick splitting still apply.
- Throw Stone spell 5225 has a specific direct additive nonnegative capped Spell Damage branch for client/bot/merc: base 1 + 250 gives 251 before downstream modifiers. It respects the explicit opt-out; NPC/reflection behavior remains distinct. `docs/releases/throw-stone-20261009.md` and its production-method regression.
- Hunt augment cap headroom is restricted to qualifying socketed items at level 50: at most +30, independently for effective heroic INT/WIS. Increasing cap doesn't create raw Spell Damage/Heal Amount. `zone/zone_hunt.cpp`, `common/zone_hunt_policy.h`, native cap fixture and `docs/releases/zone-loot-20261009/BALANCE.md`.
- Held-class HP/mana, monk weapon damage/skills, pet ownership/order routing and direct-AA buff lifetime have separate native controls. Read the source relevant to the effect, rather than reproducing the entire combat engine in Python.

## Reuse the diagnostic stack

`tools/balance/README.md` indexes the standard-library Python tools and native oracles. `baseline.py` compares active source/rules and rejects false-zero C++ runner results. Snapshot/manifest hashes pin content. Formula/resource oracles extract actual C++ methods; the native encounter harness uses real engine objects with explicit fixture/network boundaries. A fake transport test is not end-to-end gameplay.

Useful paths: `tools/balance/verify_cpp.py`, `verify_resources_cpp.py`, `native_runtime.cpp`, `native_harness.cpp`, `encounter_cli.py`, `aa_policy_preflight.py`, `aa_policy_projection.py`, `gear_candidates.py`, plus `docs/balance/` experiment reports. Native controls require the documented isolated database/source; inspect commands before executing fixtures. Don't run the entire suite for a narrow documentation/UI change.

Use legal acquisition, class/race/slot/socket restrictions and actual spent AA points. Compare held builds at equal recorded inputs and multiple progression stages. A curated pool may exhaust below the requested point budget; don't silently fill with unrestricted abilities. The old unrestricted stress ceiling isn't a Classic release target. Dated September cap comparisons retained 250/250 because pet gains weren't consistent and caster outcomes changed; later hunt headroom is a different scoped mechanic.

## Evidence limits and known gaps

Owner acceptance is feature-specific: July mana-gauge and held-Monk milestones, Permafrost portal function and the October pet-summon crash report have scoped confirmations. Many deployed systems still have visual or combined-balance QA open. Adventure Journal/Epic 0.5 and portions of combat/item and living-economy work are candidates; old THJ gap-map claims that all pets/upgrades/augments are missing are obsolete.

Historical-document hash tests can fail when their source is rewritten. Preserve historical reports and add follow-ups rather than relabeling old candidate evidence as current acceptance. Use current raw SQL/effective cache/runtime distinctions: FreeTrade and DisableLore deliberately change effective items without rewriting original SQL, so old acquisition/gear assumptions must be reviewed before new balance studies.

Record change inputs, deterministic seeds or sample scope, build/source fingerprints, before/after measurements, rollback and exact owner QA. Never claim that a few synthetic fights establish a population win rate or that automated checks prove fun, visual fidelity or final balance.
