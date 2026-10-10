# NPC-targeted heals default to the caster

Status: the owner explicitly authorized promotion to main and server deployment
on October 9, 2026. PR #139 is merged to main and deployed to OVH; all twelve zones and
follow-up health checks passed. In-game acceptance remains pending. This is a targeting
fix, with no changes to heal strength, mana, cast time, reuse, AA availability,
expansion rules or database contents.

## Behavior and cause

Player heals previously retained the submitted NPC target. With
`Spells:UseSpellImpliedTargeting` enabled, they could instead follow that NPC's
target. Neither behavior guarantees healing the caster.

`ResolvePlayerHealTarget` in `zone/spells.cpp` now selects the caster before
implied targeting and target validation in `CastSpell`, and before targeting and
range checks in `SpellFinished` for instant AA/item/triggered paths. The selected
combat target is not changed. The saved cast target remains self even when the
player selects another target during the cast.

Positive HP, HP-once, heal-over-time, complete-heal and percentage-heal effects
are recognized directly, including regeneration and the one-level triggered
effects supported by the native trigger lookup. The generic AI heal classifier
misses several HP-once and triggered variants, so it is not used for this policy.

Ordinary heals aimed at any NPC, including an owned or charmed pet, default to the
caster. A selected player remains the recipient. NPC AI healing is unchanged.
Group/area heals retain their native group/area distribution, using the caster
as their target/center. Pet-only, corpse, body-type-specific and target's-target
spells keep their explicit native targeting requirements; the fix does not turn
those special spells into player self-heals. Pure non-healing buffs, damage and
lifetaps retain their existing behavior.

## Automated verification

From `tools/tests`:

```powershell
python test_heal_targeting.py --container akk-stack-eqemu-server-1
python test_heal_targeting.py --source ../../akk-stack/code/zone/spells.cpp --container akk-stack-eqemu-server-1
```

The compiled fixture executes the actual pre-validation sections of `CastSpell`
and `SpellFinished`, the new helper and native spell classification/trigger
functions. Entity and timer services are isolated fixtures; this is not a running
game-client test. The original implementation failed 42 of the initial 62 checks.
The final implementation passes 99/99 checks on each source copy, including
implied targeting on/off, idle NPCs, player/pet/NPC casters and targets, PC-only
validation, triggered HP-once/percentage heals, final-slot effects, retargeting,
invalid spells and null targets.

The initial local translation-unit compile passed without changing the running
local binary. The owner then authorized production promotion. A fresh production
zone build passed against the exact retained deployed source; only
`zone/spells.cpp` differs from that source manifest. The prior hardened source
and binaries are retained. Deployment and recovery evidence is recorded in
[the release report](../ops/npc-heal-self-20261009/README.md).

## Exact in-game QA after deployment

Use a normal account and only spells/AAs legal for its held classes and release.
If a listed spell is unavailable, record that case as pending; do not grant
unrestricted AAs or change the era to satisfy this checklist.

1. In East Commonlands (`ecommons`), take damage from an ordinary hostile NPC
   such as an orc pawn. Keep that NPC selected and cast Minor Healing (200) or
   another known direct heal. Your HP must increase; the NPC must not receive the
   heal. Your target window must remain on the NPC, with normal mana/cast/reuse.
2. Repeat with Camil Silvermist (NPC 999521, tunnel) selected while injured.
   An idle/friendly NPC must also cause the heal to land on you.
3. With the hostile NPC attacking another player or your pet, heal while still
   targeting the hostile NPC. You must receive the heal, not its combat target.
4. Target the other injured player directly and heal. That player must receive
   it. Target your own pet with an ordinary player heal: you must receive it.
   Use an available pet-only heal separately: it must retain its native pet target.
5. Repeat the NPC-targeted case with an available HoT, Complete Heal (13), and
   instant healing AA or item. HoT ticks must restore your HP. Group heals must
   heal the normal eligible members around your group/center, not the NPC's group.
6. Start a timed heal with an NPC selected, then select another player before
   the cast finishes. It must still heal you. Repeat with a distant NPC selected;
   its distance must not cause the self-heal to fail a range check.
7. Cast a damage spell or lifetap at the NPC: it must still affect the NPC.
   Verify a non-healing buff keeps its existing targeting behavior. Repeat after
   zoning to a second zone process to detect a partially deployed binary.

Record zone, character/build, spell/AA/item, target, pre/post HP and result for
each case. Offline checks do not establish client packet or animation behavior.

## Deployment and rollback boundary

Author review checked early target validation, cast-target persistence, unchanged
per-recipient group application, explicit special target types, bounded spell
effect scans and source-mirror parity for the new helper. No new dependencies,
database access, rule catalog entries or permission bypasses are introduced.
The fresh zone executable linked successfully. Client animations and gameplay
acceptance remain unverified.

The zone executable was deployed with a graceful whole-runtime restart.
Persisted player/custom tables, rules, content, quests and client assets passed
preservation checks; no database restore ran.
The owner explicitly requested "Push to main and server" for this fix on
October 9, authorizing this release before manual in-game acceptance. The default
branch policy remains in place for unrelated future changes.
The OVH supervisor was inspected before rollout: a child exit can restart
the entire runtime. Do not kill one zone assuming only it will restart.

Every running zone was verified against the new binary hash. Complete the
checklist above for owner acceptance. Recovery selects the retained prior
immutable game image using the guarded procedure in the release report, while
retaining current SQL state.
