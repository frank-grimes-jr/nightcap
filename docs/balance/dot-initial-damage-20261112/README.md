# Player DoT initial damage — November 12 live QA

**Deployed for live QA; player access is open. Owner in-game and combined-build balance acceptance remain open.**
Initial source started from integrated `origin/main` 423f9c3b in the isolated
`feature/dot-no-initial-damage` worktree. The release source8a351145 preserves the subsequently deployed Imitate Death fix. The default workspace is older and dirty.

## Observed deployment

Main gameplay PR426/a97c55d0 and immutable DoT stage v2 are deployed. All12zone
workers independently verify7b61b5ac, restart count0 and native/quest/database
error counts0. This supersedes7bb5bd17 while preserving Imitate Death zero reuse,
Quick Buff, world95fc228a/shared_memoryb60c4dfc, quests, caches and signed
client2026111201. No client download or SQL spell/rule/schema change is needed.

A fresh stopped full backup, exact native saved-state boot model and one market
rotation passed before access reopened. No player snapshot was restored. Native
proof: production-verification.json, deployment-receipt.json and DEPLOYMENT.md.
The initial v1 DoT package never activated: the concurrent release held the lock.
The replacement authenticates2857source files and143unique retained object/library
inputs, reproduces the shipping Imitate Death zone, then compiles the whole DoT
translation unit and links the final zone. Native proof is in
native-build-current-baseline.json; the first candidate proof remains historical.

The fresh production SELECT-only audit found3629DoT definitions:986with1002
negative one-time damage slots and2643without. These include NPC/later content,
not the active legal player pool. The original local fixture remains separately
dated. No production DoT has SPA147,350or509alternative direct-HP handlers.
The eight pinned Build Lab spells have no removed initial hit; their arithmetic
stays unchanged. See production-audit.json and supplemental-review.json.

Wiki20261112-dot-ticks-v2 is published and verified: all613HTTPS hashes/headers,
five private denials, pointer rollback and all five service identities pass.
609previous outputs retain exact bytes; only Combat, In development, Change Log
and search change. Global historical drift remains REVIEW REQUIRED, including
the separately documented unchanged Build Lab provenance mismatch. Nothing here
establishes owner normal-player or encounter-balance acceptance.

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
never restore a stale player snapshot. The owner explicitly authorized this release for live testing; that does not accept gameplay or waive future deployment gates.

## Owner in-game QA (open)

1. In `arena`, have a GM create a temporary passive target named
   `Dot_QA_Dummy` with at least100,000HP, without persistent spawn/definition
   changes. Disable autoattack, pets and damage procs; capture combat timestamps and target HP. Test the same earned
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

All42authored articles, Features/Home/commands and generated item/zone/catalog
impacts were reviewed. Combat, In development and Change Log now describe the
installed live-testing behavior. Features already links the owning guide; no new
Home announcement, command, item/zone stats, rewards or Build Lab arithmetic is
needed. The source tree reproduced all613previous Imitate Death public outputs
before four scoped outputs changed. Publication and all HTTPS hashes/headers
verify;609outputs, private downloads, config and all five services are retained.
No Nginx reload or blanket content-review ledger advance occurred. The existing
Build Lab effects.cpp frozen-pin mismatch is documented, not silently refreshed.
Source review, publication and owner gameplay/balance acceptance remain distinct.

The later main earned-titles source promotion (PR428/f689f7aa) remains a separate
disabled candidate. Its source and Not released authoring guidance are preserved
in the documentation merge; it is not activated or added to this native/public
artifact. Actual shipping source, build hashes and release receipts above remain
authoritative rather than the newer integrated checkout. See
concurrent-source-review.json.
