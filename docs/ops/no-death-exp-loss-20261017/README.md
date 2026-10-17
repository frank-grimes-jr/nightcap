# No EXP penalty on death — October 17, 2026

Status: **tested configuration candidate; not activated**. The owner requested
removal of the death EXP penalty. Main promotion and production activation await
the repository's owner release approval. No production rows or processes changed.

## Change

Set default ruleset 1 `Character:DeathExpLossLevel` from `10` to `256` using
[forward.sql](forward.sql). All native character levels are uint8 values, so
`Client::Death` sets `exploss=0` before its EXP write and corpse creation. Normal
death cannot reduce EXP or de-level a player. AA progress stays intact. The same
rule controls the level-up EXP-loss warning, which is no longer reachable.

Do not set `DeathExpLossMultiplier=0`: that index still means 0.5% loss. The chosen
existing-rule override covers both loss formulas without a binary change. It is
independent of the Classic era cap; `era.json` and era application are unchanged.

Buff loss, pets, inventory, money, gems, corpse/respawn and resurrection mechanics
retain their current rules. New corpses receive zero resurrection EXP; old corpses
keep their recorded recovery amount. This is prospective, with no refund of prior
losses. Sacrifice's explicit EXP-for-reagent cost remains separate from normal
death and is not changed. No player records are rewritten.

## Evidence

[Read-only production preflight](preflight.json), October 17 at 13:47 UTC:
the only `DeathExpLossLevel` row is default ruleset 1, value 10. World uses default;
other zone rulesets have no override and load default values first. World/zone
hashes match the deployed dungeon-journal release; all five services are running,
game and database healthy. [preflight.py](preflight.py) can repeat this check.

`python -B tools/tests/test_no_death_exp_loss.py` passes two focused tests:
2,048 compiled cases from the actual `Client::Death` calculation/application
blocks cover every uint8 level, both loss formulas, level retention and zone EXP
modifiers. Two old-policy controls demonstrate actual loss, including multiplier
index zero. A source contract checks the zero-loss corpse handoff and positive
recorded-loss guards on resurrection. These are candidate-source tests, not
observed production deaths or a full server build. The complete production
attack/rule files differ from this tracked overlay; do not use this checkout to
replace production binaries. This change requires only an existing rule reload.

Reviewed source: `server-mods/code/zone/attack.cpp` (`Client::Death`),
`zone/client_process.cpp` (`OPRezzAnswer`), `zone/exp.cpp` (level-up warning),
`common/ruletypes.h`, and local full-source `common/rulesys.cpp`
(`RuleManager::LoadRules`: default rules before zone overrides).

## Authorized activation and recovery

1. Take deployment and GM-operation locks, ensure no maintenance is active, and
   repeat preflight. Require the single exact `1 / DeathExpLossLevel / 10` row,
   no overrides, current compatible binaries and healthy services. Capture the
   complete rule table and native process identities/log offsets privately.
2. Take and gzip-verify a fresh full PEQ backup. Use the existing guarded operator
   pattern in `../passive-aa-twenty-20261013/ops/apply.py`, with this rule's exact
   preimage, current binaries, and a new backup directory. Do not execute that
   historical AA operator unchanged.
3. In a transaction, rehearse forward/inverse SQL and verify each changes one
   row and the whole rule table returns to its preimage; roll back. Then execute
   forward SQL in a new transaction, require one changed row, and commit.
4. Perform authenticated `#reload rules global` using the existing
   `../passive-aa-twenty-20261013/ops/reload_rules.py`. Require fresh successful
   reload logs from world and every running zone, unchanged process identities,
   healthy services and exactly the intended difference in the whole rule table.
   Record activation separately from owner gameplay acceptance.
5. If verification fails, apply the guarded [rollback](rollback.sql) only when
   the current row still equals this operation's 256, reload globally again and
   verify. Preserve concurrent unrelated changes. An uncertain commit requires
   reading current state before recovery; never blindly replay the operation.

No restart, client update, quest reload or cache rebuild is needed. Never kill an
OVH zone to reload rules: its supervisor restarts the complete runtime. Rollback
affects future deaths only; never restore old character/database snapshots.

## Exact in-game QA after activation

1. With GM mode off, record level, normal EXP, AA points and partial AA EXP on a
   level-10-or-higher character (Palwar is suitable). In Befallen, die to a normal
   hostile NPC. After respawn, require identical EXP, AA and level.
2. Repeat near a level boundary and at cap 50 on test characters. Check an
   environmental death (falling/drowning), and a death in a Raid or Grind instance.
3. Verify belongings, spell gems, beneficial buff loss and respawn behavior match
   the existing policy. Zone and relog; retained EXP must persist.
4. Resurrect a new eligible corpse: no added EXP. An old corpse with previously
   lost EXP must retain its original recovery entitlement. Do not create or edit
   player/corpse records to manufacture these checks on production.
5. Level from 9 to 10: no announcement that deaths now cost EXP. Record character,
   zone/instance, before/after values and owner acceptance separately.

[Whole-wiki impact review](wiki-review.md): candidate notices are prepared;
publication is pending and the public site remains unchanged.
