# Throw Stone Spell Damage release — October 9, 2026

Status: **merged to main and deployed to OVH** under the owner's October 9
instruction. [PR #127](https://github.com/frank-grimes-jr/nightcap/pull/127) merged
as `d9c6234`; post-deployment health checks passed and access is open.
In-game acceptance remains open.

The owner subsequently requested **"Push to main and server"** on October 9,
authorizing this release's direct main promotion and OVH activation. This does not
record completed gameplay QA. Build and hosted verification are recorded below.

## Behavior

Throw Stone (spell 5225) adds nonnegative effective Spell Damage directly to its
normal hit, replacing this ability's percentage/timing/level-gated contribution.
The one-point base, existing 10-second reuse, range, access and spell data remain.
The effective stat already incorporates the configured item cap. At 0, 1, 50,
100, 240 and 250 effective Spell Damage, unmodified ordinary hits are respectively
1, 2, 51, 101, 241 and 251. With a 2x spell-critical multiplier, they double.
Actual focus effects, critical ratios, target defenses and damage taken modifiers
can change the logged result. The native spell damage/defense pipeline is retained.

Applies to clients, bots and mercenaries. Explicit spell item-modifier opt-outs
still work. NPC casts and the separate reflection calculation retain their prior
behavior, as do all other spells, healing and DoTs. No SQL, client patch, new rule
or global cap change is included. [Decision and alternatives](../adr/0057-throw-stone-spell-damage.md).

## Automated evidence

`tools/tests/test_throw_stone.py` extracts and compiles the actual
`GetActSpellDamage`, `GetExtraSpellAmt` and `GetActReflectedSpellDamage` method
bodies. Boundary fakes supply rules, stats, deterministic critical rolls and
messages; the arithmetic is production code. Using Visual C++ 14.44 with C++17:

- Before implementation: 101 checks, 83 expected failures, including old normal
  damage 3 and critical damage 6 at 250 Spell Damage.
- After implementation and adding ordinary-critical controls: **108 checks pass**.
- Existing spell-math and native-spell adapter suites: **12 tests pass**.
- Coverage includes four levels and all 16 class identities, tier-stat amounts,
  critical/ordinary hits, each global coefficient mode, opt-outs, negative stats,
  companions, NPCs, focus/target modifiers, self-target and reflection regressions.
- The 500-stat case checks future higher-cap compatibility; it does not raise or
  verify the current item cap. Inventory bonus accumulation is outside this fixture.

Run from the repository in a Visual Studio x64 tools shell:

```text
python tools/tests/test_throw_stone.py --compiler cl
```

On a host with a modern GCC/Clang, use `--compiler g++` or `--compiler clang++`.
The initial Windows check used Visual C++ because Strawberry GCC 4.9 cannot
compile the C++17 harness. A subsequent fresh Linux build links the full zone
executable from the fingerprinted production source plus exactly `zone/effects.cpp`.
No prior object directory is reused; source hashes are stable through compilation.
The same 108 method checks pass under clang++ against this exact hardened candidate.
The existing world, shared_memory, UCS and loginserver binaries remain byte-identical.
See [build summary](throw-stone-20261009/build-summary.json),
[native checks](throw-stone-20261009/native-tests.json) and the
[reproducible build](throw-stone-20261009/ops/build.py).

Eight rollout failure tests pass, covering successful activation, startup/health/
gateway/cache failures, input drift and preservation failures. The
[rollout](throw-stone-20261009/ops/rollout.py) never writes SQL. It keeps the gateway
closed while validating all five process binaries, player/receipt/state/rule
fingerprints, content, quests, client artifacts and existing free-trade cache.
Failures restore the immediately preceding image without restoring the database;
uncertain preservation leaves access closed. [Failure tests](throw-stone-20261009/ops/test_rollout.py).

The fresh OVH read-only baseline matches the retained production manifest and
confirms Throw Stone base -1, CurrentHP effect 0, reuse 10000 ms and item-modifier
opt-out 0. The legacy SQL column `maxtargets` is loaded as the native
`no_heal_damage_item_mod` field (column 219). The active item cap is 250 and all
three generic scaling rules are true. Twelve zone workers and the existing cache
verify, with no detected native/quest/SQL errors. No live files or rows changed
during these checks. Native hotbar behavior and encounter balance still require QA.

## Exact in-game QA before acceptance

Use an isolated QA deployment with the candidate zone binary and the current
rules/quests. Do not modify public hub residents or production player progress.

1. In `arena`, create a temporary human Warrior dummy with
   `#spawn ThrowStone_QA 1 1 0 100000 0 1`. Use this same target for comparisons.
   Record its defenses and remove damage shields, spell runes, vulnerability
   effects and caster focuses for the controlled damage check. Turn off autoattack.
2. Use a character who has learned Throw Stone, initially without bought AAs or
   buffs. Equip gear giving effective Spell Damage 0, 1, 50, 100, 240 and 250
   (record the actual effective stat and item IDs). Activate Throw Stone through
   its combat-ability/hotbar control. Record ten noncritical landed hits per
   loadout: expect the values above before target mitigation.
3. Add gear beyond the configured 250 cap: expected unmodified normal damage
   stays 251. Remove all Spell Damage: expected normal damage returns to 1.
   Confirm the ability retains its range and 10-second reuse.
4. Repeat at levels 1, 10, 30 and 50 where the character legally owns the ability,
   including held-Monk or held-Warrior multiclass access. Same effective stat and
   modifiers must yield the same result; this change does not grant the ability.
5. At level 50 compare WAR/CLR/WIZ, WAR/CLR/MNK and a legal Rogue-containing build
   that owns Throw Stone. Use only the release's allowed AAs/rank caps. Record
   classes, actual spent points, critical chance/ratio and buffs. Confirm criticals
   use the existing ratio and the bonus is added exactly once.
6. Compare a normal direct-damage spell (for example Ice Comet on the WIZ build),
   a normal weapon throw and healing against the prior binary with identical
   stats: results must remain unchanged. Test spell runes/immunity on the dummy;
   Throw Stone must still pass through native spell defenses.
7. In `ecommons`, use the same naturally spawned `a fire beetle` type for a low-level
   baseline/candidate comparison, then representative legal progression encounters
   at levels 30 and 50. Record NPC type/level, gear, effective Spell Damage, AA pool,
   damage distribution, kills/time, resource recovery and deaths. The 251 hit at a
   10-second reuse is about 25.1 raw DPS before modifiers; this alone does not prove
   balanced fights. Restore the prior binary if low-level overgearing or combined
   multiclass criticals trivialize the intended progression.
8. Depop the temporary QA dummy before leaving the zone so it is not preserved
   by zone-state saving. Record results; do not mark gameplay accepted from unit tests.

## Delivery and rollback

Build the current tracked `server-mods/code` overlay in an isolated source/build
directory using the established native build process, preserving production
hardening and source provenance. Only `zone/effects.cpp` changes; no new rule
catalog requires a world change. Verify the newly built zone hash after activation.
Retain the prior zone binary/image for rollback; restoring it removes this behavior
without undoing player progress, SQL or client files.

The owner's October 9 instruction authorizes main and OVH for this release,
before the manual QA above. Do not kill an OVH zone to refresh it: its supervisor
restarts the entire runtime when any child exits. Use the prepared closed-gateway
image rollout and retain the immediately prior image for rollback.

## Hosted verification

The owner-authorized deployment completed successfully. Post-deployment health
checks passed and access is open. No client update is required. In-game acceptance
remains pending under the QA steps above.

Detailed operational evidence and recovery receipts are retained locally and on
the server; they are not included in this published release record.
