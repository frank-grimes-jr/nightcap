# Player DoT initial damage — November 12 candidate

**Not deployed. Owner in-game and combined-build balance acceptance remain open.**
Source starts at current integrated `origin/main` 423f9c3b in the isolated
`feature/dot-no-initial-damage` worktree. The default workspace is older and dirty.

## Contract and implementation

Keep instant player DoT casts and normal tick damage. Remove only a negative
`CurrentHPOnce` (SPA 79) landing effect when the caster's existing
`Mob::IsInstantCastDot(spell_id)` policy identifies that same spell as an instant
DoT. This policy includes detrimental ordinary, life-tap, one-tick and Bard DoTs;
it does not use the generic AI DoT classifier, which excludes some of them.

The five-line guard in `server-mods/code/zone/spell_effects.cpp`, at
`Mob::SpellEffect`'s `CurrentHPOnce` case, runs before direct-damage focus,
criticals, Spell Damage and `ResourceTap`. A removed landing hit cannot produce
damage-based resource recovery. Positive one-time healing, tick effects,
duration, debuffs, mana costs, recovery/reuse, stacking and class access stay on
their existing paths. Pure DoTs already have no landing damage. Standalone nukes,
damage with only non-DoT debuffs, casterless effects and non-client casters retain
native behavior. The classification is on the spell being cast, not existing
DoTs on its target. No SQL spell rewrite or new rule is needed.

## Reviewed spell data

`local-dot-definitions.jsonl.gz` is a SELECT-only November 12 capture from local
akk-stack `peq`, not production and not the legal player spell pool. It retains
only public spell identity, timing and twelve effect tuples
`[effect_id, base_value, formula, max]`. Selection: detrimental spells with a
positive duration formula and a negative `CurrentHP` or `BardAEDot` effect.

`local-audit.json` pins the decompressed capture SHA-256 and lists all affected
definitions/slots: 3,626 DoT definitions, 980 with 996 negative `CurrentHPOnce`
slots, and 2,646 without such a hit. None of the captured DoTs has SPA 147 or 350
(alternative percentage-HP and Mana Burn damage handlers). Triggered spells and
earned AA procs remain separate native behavior; this is not a blanket ban on
every triggered damage event associated with casting.

Examples with initial damage: Disease Cloud 340, Poison Bolt 348, Infectious
Cloud 365, Envenomed Breath 434, Venom of the Snake 435, Envenomed Bolt 436.
Examples without: Clinging Darkness 344, Engulfing Darkness 355, Heat Blood 360,
Heart Flutter 367. Reckless Health 871 has a positive one-time heal: preserve it.
The native runtime guard checks calculated effect sign, not just the base data.
Later content is handled by the same policy without hardcoded IDs or widening
the legal spell pool.

## Verification and release boundary

`tools/tests/test_dot_initial_damage.py` compiles the actual three HP/Bard landing
branches and existing instant-DoT/duration methods with boundary fakes. RED
reproduced `DoT landing still deals amplified direct damage or taps resources`;
GREEN checks suppression, repeated casts, partial/reflected effects, positive
heals, formula-derived and one-tick durations, Bard DoTs, standalone nukes,
non-DoT debuffs, NPC/pet/casterless behavior and Valor. The content test verifies
capture integrity, complete counts, representative identities and other direct
HP handlers. Adjacent gameplay-policy, THJ spell scaling/legacy Throw Stone,
THJ behavior and client cast-time suites cover retained formulas and timing.

`build_native.py` compiles the whole changed translation unit in an isolated
local container tree using retained November 12 full-build-compatible source.
It first requires an exact touched-file preimage (line endings normalized),
checks retained input hashes, reproduces the shipping Quick Buff v2 zone, then
links a candidate with only the changed spell-effects object. It does not
install or execute a game binary. Native build results belong in
`native-build.json`; test/review and wiki evidence belong in `verification.json`.
An initial byte preimage check rejected Windows CRLF; normalized text comparison
confirmed the only source difference is this guard. No gameplay input was changed.

Activation requires a zone rebuild and supported whole-runtime restart on OVH;
an ordinary rule/spell/quest reload cannot load C++. Preserve the current matched
world/shared-memory/cache, quests and client release. No shared layout, new rule,
spell definition, client asset or format change is introduced. Do not use an old
pre-Quick Buff Client-layout build. Before any authorized deployment, refresh
production identity/content evidence and use the current guarded deployment
process, admission drain, stopped backup and saved-state preservation checks.
Rollback is the previous paired runtime with current player data retained;
never restore a stale player snapshot. No deployment is authorized by this note.

## Exact in-game QA after an authorized test release

1. In `arena`, use a stationary durable test NPC. Disable autoattack, pets and
   damage procs; capture combat timestamps and target HP. Test the same earned
   build, effective Spell Damage, focus, AAs and mana before/after.
2. Cast Disease Cloud 340 and Poison Bolt 348 immediately after a known tick.
   Both cast instantly, apply their debuff and cost normal mana, but cause no
   landing damage packet or HP loss. Normal damage begins at the next tick;
   tick values and cadence match the previous build at equal inputs.
3. Recast each repeatedly between ticks. No cast-time hit or damage-derived tap
   healing occurs. Duration refresh, stacking, hate and normal tick timing still
   follow native rules. A global tick coinciding with a cast is not a landing hit.
4. Repeat with Envenomed Breath 434 and Venom of the Snake 435 on a character
   holding their class and legal level. Compare low-gear and developed legal-AA
   builds; record actual spent AAs, gear/focus, damage, mana and time to kill.
5. Cast Clinging Darkness 344 and Heat Blood 360: still instant, same ticks and
   debuffs. A normal learned standalone nuke still damages on landing even
   while a DoT is active. Verify ordinary buff heals and Valor remain intact.
6. Exercise an available duration life-tap, one-tick DoT and Bard damage song,
   and an NPC-cast Poison Bolt. Only player instant-DoT landing hits are removed;
   normal ticks, Bard mechanics and NPC direct damage remain. Check death,
   resists, overwrite failure and relog for ordinary native behavior.

No synthetic checks establish encounter balance or owner acceptance. Record
observed results and failures before the normal test-to-main promotion gate.

## Wiki impact

Reviewed all authored guides, Features, Home, commands and generated item/zone
catalogs against this five-line behavior change. Combat, In development and
Change Log describe a **Not released** preview. Existing Features already links
Combat and development previews; no new live feature/Home announcement is
appropriate. Commands, item/zone stats, acquisition, catalog/Build Lab arithmetic
and legal pools do not change. Global historical source drift remains REVIEW
REQUIRED; do not blindly advance `content-review.json`. The local edits are not
published. Future authorized publication must reproduce the then-current public
artifact and preserve all unrelated outputs and release labels.
