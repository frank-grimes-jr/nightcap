# Combat and balance knowledge

Audited 2026-10-12. Dated September fixtures are reproducible evidence for their captured inputs, not a current character or production snapshot.

Nightcap favors solo play without trivializing earned progression. Evaluate classes, legal AAs, pets, buffs, heroic stats, augments and gear together. Measure incoming burst, survival, mana sustain/recovery, time to kill, cooldown use and reward acquisition, not only DPS or encounter HP. Cap increases above 250 are allowed for consideration; neither 250 nor a prior experiment is a permanent policy ceiling.

## Buried Sea AA policy — deployed for owner QA October 13

Current implementation/evidence: `C:/Users/verre/.codex/worktrees/aa-tbs-policy/EQ_Local_Dev/docs/releases/aa-tbs-20261013/README.md`.
Feature/dev/test candidate `83ed0b5` is live on OVH with image
`sha256:5555000c74665f13eb3c99facc657b2e38c3983eff745a9ffe65a5439440f025`. Main promotion and owner in-game balance,
readability and enjoyment acceptance remain pending. The concurrent October 13
skill-progression/offhand correction and signed client2026101301 were retained.

`era.json` selects `config/aa-policy.json`; `tools/aa_tbs_policy.py` generates
`common/nightcap_aa_policy.h` from a reviewed full catalog fixture. Unknown rank
identities fail closed. TBS13 is an AA-only bound, independent of Classic world
expansion. Most families cap at3 ranks at30/40/50; core passives at1 or10/20/30.
Dependencies can raise levels/remove ranks, never widen the pool. Six exceptions:
Eyes Wide Open938 rank8 at1; Diminutive543 rank1 at10; ENC Pet Discipline3202
rank1 at20 with Animation Empathy195 rank3; Durability3512/Agility3818 ranks1/2/3
at30/40/50; Sturdy1403 rank1 at50 (raw AC, not percent mitigation).

High-risk TBS burns/executes/refills/glyphs and all grant-only veteran families
are dormant. Existing earned ranks, charges, wallets and spent accounting are
preserved, with no refunds or repurchase charges. Native CanUse gates offers,
grants, purchase, activation and usable projection. ReprojectEarnedAAs handles
same-zone levels before bonus/save; full AA refresh clears/resends table, owned
ranks and stats. Missing prerequisite definitions reject purchases.

Global ceiling390 families/941 ranks; sampled triples start at9 families at1,
about15–16 at10–20. Exact 16-class/six-union coverage and maximum legal spend are
in coverage.json; these are catalog counts, not encounter strength measurements.
5 policy tests,5,646 native rank/level cases plus actual purchase/save/projection
checks,13 deployment/preflight tests and9 preserved skill scenarios passed.
Independent review fixed missing prerequisites/incomplete refresh and checked
the final retained-source build. All12 running zones match;47 player/11 custom
tables, rules, AA content and existing services were preserved through restart.

Future policy edits require regeneration and a matching zone deployment;
era SQL/rule/AA reload cannot install a compiled allowlist. No new world rule or
client asset is needed. Production child exits restart the entire runtime; use
the release's guarded operator and image-only recovery, never old player SQL.
Pet avoidance/AC is live; pet HP updates on summon/restore, with saved HP clamped.
Temporary spell buffs expire normally. Existing cross-class Mastery of the Past
prerequisite behavior is outside this change. Resummon pets for HP cap QA.

The preceding audit remains at docs/audits/aa-tbs-20261013: all6,655 DB rank level
requirements are1 and there are no expansion13 rows. Compiled policy now supplies
independent level gates; do not interpret untouched DB rows as unrestricted live
access. No fresh encounter campaign or player acceptance was claimed.

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
